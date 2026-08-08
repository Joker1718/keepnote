# Phase 1 — Remediation Receipt

**Run ID:** data-validator-remediation  
**Status:** DRAFT → REMEDIATED  
**Date:** 2026-08-08  

---

## Corrective Actions Applied

### KEEP-PLAN-1.1 — Timestamp Modernization (`get_timestamp`, `get_str_timestamp`, `format_timestamp`)
- **File:** `keepnote/timestamp.py`
- **Root Cause:** `time.time()` and `time.mktime()` used without Year 2038 safeguards; integer truncation risk on 32-bit `time_t`
- **Fix:** Replaced `time.time()` with `datetime.now(timezone.utc).timestamp()` in `get_timestamp()`; wrapped `time.localtime(timestamp + EPOC)` with `int()` in `get_str_timestamp()` and `format_timestamp()` to prevent float→int truncation for large timestamps
- **Lines Changed:** 28-39 (import + EPOC), 98-101 (get_timestamp), 126-127 (get_str_timestamp), 150-152 (format_timestamp)
- **Disposition:** FIXED

### KEEP-PLAN-1.2 — EPOC Calculation Fix
- **File:** `keepnote/timestamp.py`
- **Root Cause:** `time.mktime((1970, 2, 1, 0, 0, 0, 3, 1, 0))` is platform-dependent and may overflow
- **Fix:** Replaced with `datetime(1970, 2, 1, 0, 0, 0, tzinfo=timezone.utc).timestamp()` for timezone-aware, 64-bit safe EPOC computation
- **Lines Changed:** 37-39
- **Disposition:** FIXED

### KEEP-PLAN-2.1 — ctypes Unicode Fix for `_putenv`
- **File:** `keepnote/trans.py`
- **Root Cause:** `msvcrt._putenv.argtypes = [ctypes.c_char_p]` passes narrow (ANSI) strings; on Windows 64-bit with non-ASCII paths this causes 0xc0000005 access violations
- **Fix:** Changed argtypes to `[c_wchar_p]`; imported `c_wchar_p` from ctypes; added `_putenv_w` alias for clarity; removed stale encoding comment
- **Lines Changed:** 29, 34-37, 69-72
- **Disposition:** FIXED

### KEEP-PLAN-2.2 — Screenshot 64-bit HANDLE Safety
- **File:** `keepnote/mswin/screenshot.py`
- **Root Cause:** Win32 HDC/HANDLE types are 8-byte pointers on 64-bit Windows; win32gui wraps these internally but no runtime guard existed
- **Fix:** Added `ctypes.sizeof(ctypes.c_void_p) == 8` runtime check (`_IS_64BIT`); added handle overflow warning in `capture_screen()`; added documentation comments at `CreateDC` call site in `_on_mouse_up`
- **Lines Changed:** 28-34 (imports + guard), 57-65 (capture_screen), 221-222 (_on_mouse_up)
- **Disposition:** FIXED (code-level; requires Windows runtime verification — tagged UNVERIFIED in original report)

### KEEP-PLAN-3.1 — Eliminate Nested `Gtk.main()` in `minimize_window`
- **File:** `keepnote/gui/main_window.py`
- **Root Cause:** `minimize_window()` called blocking `Gtk.main()` nested inside the main event loop, causing Win32 message pump deadlock
- **Fix:** Replaced signal-handler + `Gtk.main_quit()` + `Gtk.main()` pattern with non-blocking `GLib.timeout_add(100, check_minimized)` polling loop with 2-second timeout (20 iterations × 100ms)
- **Lines Changed:** 305-324
- **Disposition:** FIXED

### KEEP-PLAN-3.2 — Replace `gobject.idle_add` with `GLib.idle_add`
- **File:** `keepnote/gui/main_window.py`
- **Root Cause:** `gobject.idle_add` is deprecated in PyGObject 3.x+; `GLib.idle_add` is the correct replacement
- **Fix:** Added `GLib` to `gi.repository` import (line 34); replaced `gobject.idle_add(self.maximize)` at line 270 and `gobject.idle_add(gui_update)` at line 1656 with `GLib.idle_add(...)`
- **Lines Changed:** 34, 271-272, 1664-1665
- **Disposition:** FIXED

### KEEP-PLAN-4.1 — Thread-Safe UI Helper + UIManager Dispose
- **Files:** `keepnote/util.py`, `keepnote/gui/__init__.py`
- **Root Cause:** (a) No thread-safe wrapper for UI updates from worker threads; (b) UIManager had no `dispose()` method, leaking GObject references
- **Fix:** Added `gtk_safe_call(func, *args, **kwargs)` and `ThreadSafeUIUpdater` class to `util.py` with `GLib.idle_add`-based dispatch and graceful fallback; added `dispose()` method to `UIManager` class that cleans up action groups and widget references; added `GLib` import to `gui/__init__.py`
- **Lines Changed:** util.py 52-113 (new code), gui/__init__.py 33 (import), 279-291 (dispose method)
- **Disposition:** FIXED

### KEEP-PLAN-5.1 — PyInstaller Spec GTK Path Detection
- **File:** `keepnote.spec`
- **Root Cause:** Original spec used hardcoded `python_prefix`/`site_packages` with no environment variable support; fragile across MSYS2/Conda/pip installations
- **Fix:** Replaced static prefix detection with `get_gtk_runtime_data()` function that checks `GTK_PATH` env var, `sys.prefix/Library` (MSYS2), and `sys.prefix/share/gtk-3.0` (Conda); all 7 collection sections (typelib, DLLs, share, etc, pixbuf loaders, loaders.cache, gio modules) now iterate over discovered prefixes
- **Disposition:** FIXED

### KEEP-PLAN-5.2 — Modernized Build Script
- **File:** `pkg/win/build.sh`
- **Root Cause:** Original script called `wine.sh python setup.py py2exe` — py2exe is deprecated and Wine dependency is unnecessary on native Windows
- **Fix:** Complete rewrite as PyInstaller-based build script with environment validation, auto-install of PyInstaller 6.x, MSYS2 `GTK_PATH` auto-detection, clean build, and optional Inno Setup installer step
- **Disposition:** FIXED (code-level; requires Windows runtime — tagged FAIL in original report due to Linux-only environment)

### KEEP-PLAN-7.1 — faulthandler Integration
- **File:** `keepnote/__main__.py`
- **Root Cause:** No crash dump mechanism; segfaults (0xc0000005) on Windows produced no diagnostic output
- **Fix:** Added `faulthandler.enable()` at module level before `main()` import; added `PYTHONFAULTFILE` support for file-based crash dumps; added `KEEPNOTE_DEADLOCK_DETECT` env var for 30-second periodic traceback dumps; added SIGSEGV/SIGABRT signal handlers with graceful fallback on Windows
- **Lines Changed:** Entire file rewritten (4 → 57 lines)
- **Disposition:** FIXED

## Items NOT Modified (Environment Constraints)

| Task ID | Reason | Original Status |
|---------|--------|-----------------|
| KEEP-PLAN-2.2 (runtime test) | Requires Windows 11 + win32api | UNVERIFIED |
| KEEP-PLAN-5.2 (build test) | Requires Windows 11 + PyInstaller | FAIL (Linux) |
| KEEP-PLAN-6.1 | Requires GTK 4 runtime | UNVERIFIED |
| KEEP-PLAN-6.2 | Requires GTK 4 runtime | UNVERIFIED |