# Allow running as: python -m keepnote

# FIX: Enable crash diagnostics before main entry point (KEEP-PLAN-7.1)
import os
import sys
import logging

# Enable faulthandler for crash diagnostics on Windows
# This provides immediate traceback on segfaults (e.g., 0xc0000005 access violations)
try:
    import faulthandler
    faulthandler.enable()

    # Configure crash dump file if specified via environment variable
    fault_file = os.environ.get("PYTHONFAULTFILE")
    if fault_file:
        try:
            fault_fp = open(fault_file, 'w')
            faulthandler.enable(file=fault_fp)
            logging.info(f"Fault handler enabled, dumping to {fault_file}")
        except IOError as e:
            logging.warning(f"Could not open fault file {fault_file}: {e}")

    # Enable deadlock detection if requested
    if os.environ.get("KEEPNOTE_DEADLOCK_DETECT", ""):
        faulthandler.dump_traceback_later(timeout=30, repeat=True)
        logging.info("Deadlock detection enabled (30s timeout)")

    # Register signal handlers for crash dumps (Unix-like, limited on Windows)
    try:
        import signal

        def _crash_handler(signum, frame):
            logging.critical(f"Received signal {signum}, dumping traceback")
            faulthandler.dump_traceback()
            sys.exit(128 + signum)

        signal.signal(signal.SIGSEGV, _crash_handler)
        signal.signal(signal.SIGABRT, _crash_handler)
    except (AttributeError, ValueError):
        # Signal handling limited on Windows
        pass
except ImportError:
    pass  # faulthandler not available

from keepnote import main

main()