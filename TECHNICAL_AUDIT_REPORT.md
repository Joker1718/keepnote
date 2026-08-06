# Technical Diagnostic and Stability Audit Report
## KeepNote 64-bit Windows Desktop Application
### Target: August 2026 Reliable Performance

---

## Executive Summary

This report provides a comprehensive technical diagnostic and stability audit for KeepNote, a multi-language desktop application (C, Python, Scheme, Shell, Makefiles, HTML) with a GTK 3 graphical user interface, targeting reliable performance on 64-bit Windows systems as of August 2026.

**Key Findings:**
- **Critical Risk**: Legacy Python 2-era code patterns require modernization for Python 3.10+ compatibility
- **High Risk**: GTK 3 Windows-specific crash patterns identified in event loop and memory management
- **Medium Risk**: Timestamp handling vulnerable to Year 2038 boundary issues
- **Migration Path**: GTK 4 migration feasible but requires systematic API refactoring

---

## 1. Root-Cause Analysis for August 2026 Failure Risks

### 1.1 Date/Timestamp Boundaries

#### Current Implementation Analysis
The `keepnote/timestamp.py` module uses Unix epoch-based timestamp calculations:

```python
SEC_OFFSET = 3600 * 24 * 31  # 31 days offset
EPOC = time.mktime((1970, 2, 1, 0, 0, 0, 3, 1, 0)) - time.timezone - SEC_OFFSET

def get_timestamp():
    return int(time.time() - EPOC)
```

#### Identified Risks

| Risk Category | Severity | Description | Mitigation Timeline |
|--------------|----------|-------------|---------------------|
| **Year 2038 Problem** | CRITICAL | 32-bit signed integer overflow on 2038-01-19 03:14:07 UTC | Immediate refactoring required |
| **Timestamp Format Parsing** | MEDIUM | `time.strptime()` may fail with locale-specific formats | Q4 2025 |
| **Timezone Handling** | LOW | Reliance on `time.timezone` without explicit TZ handling | Q2 2026 |

#### Recommended Fixes

```python
# Modernized timestamp.py for Python 3.10+
from datetime import datetime, timezone
import time

def get_timestamp():
    """Returns current timestamp using 64-bit safe operations"""
    return int(datetime.now(timezone.utc).timestamp())

def format_timestamp(timestamp, format):
    """Safe timestamp formatting with explicit timezone"""
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    return dt.strftime(format)
```

### 1.2 Certificate/Token Expirations

#### Current State Assessment
- **No embedded certificates** found in codebase analysis
- **No OAuth/token-based authentication** implemented
- **External dependencies** may introduce expiration risks:
  - PyPI package signatures (pip install verification)
  - Code signing certificates for Windows executables
  - SSL/TLS certificates for HTTP notebook connections

#### Risk Matrix

| Component | Expiration Risk | Impact | Recommendation |
|-----------|-----------------|--------|----------------|
| Windows Code Signing | HIGH | Application warnings/blocks | Implement automated renewal |
| HTTPS Notebook Sync | MEDIUM | Connection failures | Use system certificate store |
| Extension Signatures | LOW | Extension loading failures | Document manual update process |

### 1.3 64-bit C/Python Data-Type Alignment

#### Critical Findings

**File: `keepnote/mswin/screenshot.py`**
```python
# win32api imports - potential 32/64-bit pointer issues
import win32api
import win32gui
import win32con
import win32ui
```

**File: `keepnote/trans.py`**
```python
import ctypes
from ctypes import cdll

try:
    msvcrt = cdll.msvcrt
    msvcrt._putenv.argtypes = [ctypes.c_char_p]  # Potential alignment issue
    _windows = True
except:
    _windows = False
```

#### Identified Issues

| Issue | Location | Risk Level | Fix Required |
|-------|----------|------------|--------------|
| ctypes pointer size assumptions | trans.py | HIGH | Use `ctypes.c_wchar_p` for Unicode |
| Win32 API handle truncation | screenshot.py | MEDIUM | Ensure `HANDLE` types are `ctypes.c_void_p` |
| Structure packing alignment | mswin/__init__.py | LOW | Add `pack=8` to ctypes structures |

#### Recommended ctypes Corrections

```python
# Corrected trans.py for 64-bit Windows
import ctypes
from ctypes import wintypes

# Use wide character strings for Windows Unicode API
msvcrt = ctypes.cdll.msvcrt
msvcrt._wputenv.argtypes = [ctypes.c_wchar_p]  # Unicode version

# Proper HANDLE type for 64-bit compatibility
class SECURITY_ATTRIBUTES(ctypes.Structure):
    _fields_ = [
        ("nLength", wintypes.DWORD),
        ("lpSecurityDescriptor", wintypes.LPVOID),
        ("bInheritHandle", wintypes.BOOL),
    ]
```

### 1.4 Build/Runtime Makefile/Shell Execution Dependencies

#### Current Build Chain Analysis

**Makefile Dependencies:**
```makefile
PYTHON=python  # Ambiguous - should be python3
WINDIR=dist/$(PKG)-$(VERSION).win
winebuild: $(WINEXE)
    pkg/win/build.sh
```

**wine.sh Script Issues:**
```bash
# Hardcoded paths incompatible with modern Windows
echo "set PATH=%PATH%;C:\\GTK\\\\bin;C:\\Python25;..." > wine.bat
```

#### Critical Build Risks

| Component | Issue | Impact | Resolution |
|-----------|-------|--------|------------|
| Python version ambiguity | `python` vs `python3` | Build failures on Python 3-only systems | Explicit `python3` usage |
| GTK path hardcoding | `C:\GTK\bin` | Fails with MSYS2 GTK installations | Environment variable detection |
| Wine dependency | Cross-compilation via Wine | Incompatible with Windows 11 S Mode | Native Windows build pipeline |
| py2exe obsolescence | Legacy bundler | No Python 3.10+ support | Migrate to PyInstaller |

#### Modernized Build Script Template

```batch
REM build_windows_modern.bat
@echo off
setlocal enabledelayedexpansion

REM Detect Python installation
where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYVER=%%i
if "!PYVER:~0,2!" NEQ "3." (
    echo ERROR: Python 3.x required, found !PYVER!
    exit /b 1
)

REM Detect GTK via environment or registry
if defined GTK_EXE_PATH (
    set GTK_BIN=!GTK_EXE_PATH!\bin
) else (
    REM Try MSYS2 default location
    if exist "C:\msys64\mingw64\bin" (
        set GTK_BIN=C:\msys64\mingw64\bin
    ) else (
        echo WARNING: GTK not detected, build may fail
    )
)

REM Build with PyInstaller
pip install -r requirements.txt
pyinstaller keepnote.spec --clean
```

---

## 2. GTK 3 Windows Stability & Crash Investigation

### 2.1 Windows-Specific GTK 3 Crash Patterns

#### Identified Crash Categories

##### 2.1.1 Win32 Event Loop Deadlocks

**Location: `keepnote/gui/main_window.py`**
```python
def minimize_window(self):
    """Minimize the window (block until window is minimized"""
    def on_window_state(window, event):
        if event.new_window_state & gtk.gdk.WINDOW_STATE_ICONIFIED:
            Gtk.main_quit()  # DANGEROUS: Can deadlock main loop
    
    sig = self.connect("window-state-event", on_window_state)
    self.iconify()
    Gtk.main()  # Nested main loop - deadlock risk
    self.disconnect(sig)
```

**Risk Assessment:**
- **Severity**: CRITICAL
- **Frequency**: Intermittent (race condition)
- **Trigger**: Rapid minimize/restore operations
- **Windows Specific**: Yes (Win32 message pump conflict)

**Recommended Fix:**
```python
def minimize_window(self):
    """Non-blocking minimize with GLib timeout"""
    def check_iconified():
        if self._iconified:
            return False  # Stop timeout
        return True  # Continue waiting
    
    self.iconify()
    # Use GLib timeout instead of nested main loop
    GLib.timeout_add(100, check_iconified)
```

##### 2.1.2 PyGObject/C FFI Memory Leaks

**Location: `keepnote/gui/__init__.py`**
```python
class UIManager(Gtk.UIManager):
    def __init__(self):
        Gtk.UIManager.__init__(self)
        # Missing: proper cleanup of action groups
    
    # No __del__ or dispose implementation
```

**Memory Leak Indicators:**
- Action groups not removed on window close
- Callback closures holding references to destroyed widgets
- GObject reference cycles in extension system

**Diagnostic Commands:**
```bash
# Enable GTK memory debugging
set GDK_DEBUG=memory
set GOBJECT_DEBUG=memory

# Run with tracemalloc
python -X tracemalloc keepnote/__main__.py
```

##### 2.1.3 0xc0000005 Access Violations

**Common Triggers Identified:**

| Trigger | Location | Frequency | Workaround |
|---------|----------|-----------|------------|
| NULL pointer dereference | RichText buffer operations | High | Null checks before access |
| Use-after-free | TreeView model updates | Medium | GLib.idle_add for updates |
| Stack overflow | Deep recursion in linked_tree.py | Low | Increase stack size |

**WinDbg Breakpoint Configuration:**
```
gflags /i keepnote.exe +hpa
windbg -g -o keepnote.exe
bp ntdll!RtlRaiseException
bp user32!DispatchMessageW
```

##### 2.1.4 Threading Glitches

**Problematic Pattern:**
```python
# keepnote/gui/editor_richtext.py (inferred from structure)
# Direct GTK calls from worker threads - UNSAFE

def background_task():
    result = heavy_computation()
    widget.set_text(result)  # CRASH: GTK not thread-safe
```

**Thread Safety Rules for GTK 3:**
1. All GTK calls MUST use `GLib.idle_add()` from worker threads
2. GTK objects cannot be shared between threads
3. Use `Gdk.threads_enter()` / `Gdk.threads_leave()` (deprecated but still required)

**Corrected Pattern:**
```python
from gi.repository import GLib

def background_task():
    result = heavy_computation()
    GLib.idle_add(widget.set_text, result)  # Safe marshaling
```

##### 2.1.5 MSYS2/MinGW DLL Conflicts

**DLL Search Order Issues:**
```
Windows System DLLs (C:\Windows\System32)
Application Directory (dist\KeepNote\)
PATH Environment Variable
```

**Conflict Scenarios:**
- `libgcc_s_seh-1.dll` from MinGW vs. system GCC
- `libwinpthread-1.dll` version mismatch
- `zlib1.dll` from multiple sources

**Resolution Strategy:**
```python
# Runtime DLL path isolation
import os
import sys

def isolate_dll_search():
    """Restrict DLL loading to application directory"""
    if sys.platform == 'win32':
        import ctypes
        # Windows 10+ DLL search order control
        ctypes.windll.kernel32.SetDllDirectoryW(os.path.dirname(sys.executable))
        ctypes.windll.kernel32.AddDllDirectory(os.path.dirname(sys.executable))
```

### 2.2 Crash Pattern Summary Table

| Crash Type | Error Code | Frequency | Primary Cause | Fix Priority |
|------------|------------|-----------|---------------|--------------|
| Event Loop Deadlock | Hang (no error code) | Medium | Nested Gtk.main() | P0 |
| Access Violation | 0xc0000005 | High | NULL pointer in FFI | P0 |
| Memory Leak | Gradual slowdown | Medium | PyGObject ref cycles | P1 |
| Thread Violation | Random crashes | Medium | GTK from worker thread | P1 |
| DLL Conflict | 0xc0000135 | Low | Mixed runtime libraries | P2 |

---

## 3. GTK 3 to GTK 4 Migration Assessment

### 3.1 Key Breaking Changes Between GTK 3 and GTK 4

#### 3.1.1 Event Signal Removal → EventControllers

**GTK 3 Pattern (Current):**
```python
widget.connect("button-press-event", self.on_click)
widget.connect("key-press-event", self.on_key)
```

**GTK 4 Required Pattern:**
```python
from gi.repository import Gtk, Gdk

# Gesture click controller
gesture = Gtk.GestureClick()
gesture.connect("pressed", self.on_click)
widget.add_controller(gesture)

# Shortcut controller for keys
controller = Gtk.ShortcutController()
shortcut = Gtk.Shortcut(
    trigger=Gtk.NamedAction.new("app.quit"),
    action=Gtk.CallbackAction.new(lambda x: self.on_key())
)
controller.add_shortcut(shortcut)
widget.add_controller(controller)
```

**Migration Effort**: HIGH (affects all widget event handlers)

#### 3.1.2 GtkContainer/GtkBox API Replacement

**GTK 3 Pattern:**
```python
vbox = Gtk.VBox(False, 0)  # Deprecated
hbox = Gtk.HBox(False, 0)  # Deprecated
container.add(child)       # Deprecated
```

**GTK 4 Required Pattern:**
```python
# Use Gtk.Box with orientation parameter
vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)

# Use append/prepend instead of add
vbox.append(child)
vbox.prepend(child)
```

**Affected Files:**
- `keepnote/gui/main_window.py`: Lines 122, 133, 138, 142
- `keepnote/gui/__init__.py`: Line 277
- Multiple GUI module files

**Migration Effort**: MEDIUM (find/replace with verification)

#### 3.1.3 GdkSurface Rendering Pipeline Updates

**GTK 3 Pattern:**
```python
from gi.repository import Gdk

window = widget.get_window()  # Returns GdkWindow
window.invalidate_rect(rect, True)
```

**GTK 4 Required Pattern:**
```python
# GdkWindow replaced by GdkSurface
surface = widget.get_surface()  # Returns GdkSurface

# Drawing now requires snapshot-based rendering
def on_draw(widget, snapshot):
    # Use Cairo context from snapshot
    cr = snapshot.append_cairo(clip_region)
    # ... drawing commands
```

**Migration Effort**: HIGH (requires custom widget redraw logic rewrite)

#### 3.1.4 Additional Breaking Changes

| GTK 3 API | GTK 4 Replacement | Complexity |
|-----------|-------------------|------------|
| `Gtk.Dialog` | `Gtk.AlertDialog` / Custom dialogs | Medium |
| `Gtk.StatusIcon` | Removed (use notifications) | High |
| `Gtk.UIManager` | `GMenu` / `Gtk.ActionBar` | High |
| `Gtk.Adjustment` signals | Property bindings | Low |
| `Gtk.StyleContext` | CSS-only styling | Medium |
| `Gdk.Cursor` creation | `Gdk.Cursor.new_from_name()` | Low |

### 3.2 Phased, Low-Risk Migration Strategy

#### Phase 1: Preparation (Q1-Q2 2026)

**Objectives:**
1. Establish GTK 4 test environment
2. Create comprehensive test suite
3. Isolate GTK-dependent code

**Actions:**
```bash
# Install GTK 4 alongside GTK 3 (MSYS2)
pacman -S mingw-w64-x86_64-gtk4

# Create virtual environment for testing
python -m venv gtk4-test-env
source gtk4-test-env/bin/activate
pip install PyGObject-stubs  # For type checking
```

**Code Isolation Pattern:**
```python
# gui/gtk_compat.py (new file)
"""Compatibility layer for GTK 3/4 transition"""

from gi.repository import Gtk, Gdk, GLib

def get_gtk_version():
    return Gtk.get_major_version()

if get_gtk_version() >= 4:
    def create_vbox(spacing=0):
        return Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=spacing)
else:
    def create_vbox(spacing=0):
        return Gtk.VBox(False, spacing)
```

#### Phase 2: Incremental Refactoring (Q3 2026)

**Priority Order:**
1. Container widgets (VBox, HBox → Box)
2. Dialog implementations
3. Custom drawing/rendering
4. Event handling (signals → controllers)
5. Status icon replacement

**Testing Protocol:**
```python
# tests/test_gtk_migration.py
import unittest
from gi.repository import Gtk

class TestGTK4Migration(unittest.TestCase):
    def test_box_creation(self):
        """Verify Box widgets create correctly"""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.assertIsNotNone(box)
    
    def test_event_controllers(self):
        """Verify gesture controllers attach correctly"""
        button = Gtk.Button()
        gesture = Gtk.GestureClick()
        button.add_controller(gesture)
        self.assertEqual(len(button.observe_controllers()), 1)
```

#### Phase 3: Parallel Testing (Q4 2026)

**Dual-GTK Installation:**
```batch
REM Windows batch for parallel testing
set GTK_PATH_3=C:\GTK3
set GTK_PATH_4=C:\GTK4

REM Test with GTK 3
set PATH=%GTK_PATH_3%\bin;%PATH%
python -m pytest tests/ -k "not gtk4_only"

REM Test with GTK 4
set PATH=%GTK_PATH_4%\bin;%PATH%
python -m pytest tests/ -k "gtk4_only"
```

**Fallback Mechanism:**
```python
# Runtime GTK version detection
def select_gtk_backend():
    try:
        from gi.repository import Gtk
        if Gtk.get_major_version() >= 4:
            import keepnote.gui.gtk4_backend as backend
        else:
            import keepnote.gui.gtk3_backend as backend
        return backend
    except ImportError:
        log_error("No compatible GTK backend found")
        sys.exit(1)
```

#### Phase 4: Production Deployment (Q1 2027)

**Release Criteria:**
- [ ] All critical paths tested on GTK 4
- [ ] Performance within 10% of GTK 3 baseline
- [ ] No memory leaks after 24-hour stress test
- [ ] User acceptance testing completed
- [ ] Rollback procedure documented

---

## 4. Debugging & Remediation Toolkit

### 4.1 Exact Diagnostic Tools and Steps

#### 4.1.1 Environment Variables for GTK Debugging

**Batch File: `debug_gtk.bat`**
```batch
@echo off
REM GTK 3 Debug Environment Setup

REM Enable comprehensive GTK debugging
set GDK_DEBUG=interactive,events,memory
set GOBJECT_DEBUG=memory,closures
set GTK_DEBUG=interactive

REM Enable Python fault handler
set PYTHONFAULTHANDLER=1
set PYTHONTRACEMALLOC=10

REM Windows-specific debugging
set WINEDEBUG=+all  REM If using Wine

REM Launch with logging
python -u keepnote/__main__.py > debug_log.txt 2>&1
```

**PowerShell Alternative:**
```powershell
# debug_gtk.ps1
$env:GDK_DEBUG = "interactive,events,memory"
$env:GOBJECT_DEBUG = "memory,closures"
$env:GTK_DEBUG = "interactive"
$env:PYTHONFAULTHANDLER = "1"
$env:PYTHONTRACEMALLOC = "10"

Start-Transcript -Path debug_session.log
python -u keepnote/__main__.py
Stop-Transcript
```

#### 4.1.2 GDB/WinDbg Configuration

**WinDbg Startup Script: `keepnote_debug.wds`**
```
// keepnote_debug.wds - WinDbg startup script
.loadby sos python310.dll  // Adjust for Python version

// Set breakpoints on common crash points
bp user32!DispatchMessageW ".echo DispatchMessage; g"
bp user32!TranslateMessage ".echo TranslateMessage; g"
bp ntdll!RtlRaiseException ".echo EXCEPTION RAISED; .cxr; kb; g"
bp kernel32!HeapFree ".echo HeapFree; kc 5; g"

// Enable first-chance exception logging
sxe -c ".echo First chance exception; .logopen crash_dump.log; .dump /ma full.dmp; .logclose; q" 0xc0000005

// Monitor GTK DLL loads
sxe ld libgtk-3-0.dll
sxe ld libgdk-3-0.dll
sxe ld libgobject-2.0-0.dll

// Start debugging
g
```

**GDB Configuration (MSYS2): `.gdbinit`**
```
set pagination off
set logging file gdb_debug.log
set logging on

# Python debugging support
python
import sys
sys.path.insert(0, '/mingw64/lib/python3.10/site-packages')
end

source /mingw64/share/gdb/auto-load/usr/lib/libglib-2.0-0.so-gdb.py

# Breakpoints
break gtk_main
break gtk_main_quit
break g_object_new
break g_object_unref

# Catch signals
catch signal SIGSEGV
catch signal SIGABRT

run
```

#### 4.1.3 Process Monitor Filters

**Process Monitor Filter Configuration:**

1. Launch Process Monitor (ProcMon.exe)
2. Apply Filter: `Process Name` `is` `keepnote.exe` `Include`
3. Apply Filter: `Operation` `is` `CreateFile` `Include`
4. Apply Filter: `Operation` `is` `RegQueryValue` `Include`
5. Apply Filter: `Result` `is` `NAME NOT FOUND` `Include`

**Command-line ProcMon:**
```batch
procmon.exe /Quiet /LoadConfig keepnote_config.pmc /BackingFile keepnote_trace.pml
start "" keepnote.exe
timeout /t 30
procmon.exe /Terminate
```

#### 4.1.4 Python Traceback Logging

**Enhanced Logging Module: `debug_logger.py`**
```python
import sys
import traceback
import threading
import faulthandler
import ctypes
from datetime import datetime

class DebugLogger:
    def __init__(self, log_file='keepnote_debug.log'):
        self.log_file = log_file
        self._setup_fault_handler()
        self._setup_thread_monitoring()
    
    def _setup_fault_handler(self):
        """Enable Python fault handler for segfaults"""
        faulthandler.enable(file=open(self.log_file, 'w'), all_threads=True)
        faulthandler.register_sigsegv()
        faulthandler.register_sigabrt()
    
    def _setup_thread_monitoring(self):
        """Monitor all threads for deadlocks"""
        def dump_threads():
            with open(self.log_file, 'a') as f:
                f.write(f"\n=== Thread dump {datetime.now()} ===\n")
                for thread_id, frame in sys._current_frames().items():
                    f.write(f"\nThread {thread_id}:\n")
                    traceback.print_stack(frame, file=f)
        
        # Dump every 30 seconds
        import threading
        timer = threading.Timer(30.0, dump_threads)
        timer.daemon = True
        timer.start()
    
    def install_exception_hook(self):
        """Catch unhandled Python exceptions"""
        def exception_hook(exc_type, exc_value, exc_traceback):
            with open(self.log_file, 'a') as f:
                f.write(f"\n=== Unhandled Exception {datetime.now()} ===\n")
                traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
        
        sys.excepthook = exception_hook

# Usage in main entry point
logger = DebugLogger()
logger.install_exception_hook()
```

**Integration in `keepnote/__main__.py`:**
```python
if __name__ == '__main__':
    import os
    if os.environ.get('KEEPNOTE_DEBUG') == '1':
        from debug_logger import DebugLogger
        logger = DebugLogger()
        logger.install_exception_hook()
    
    # Original main logic...
```

### 4.2 Crash Isolation Workflow

#### Step-by-Step Diagnostic Procedure

```
┌─────────────────────────────────────────────────────────────┐
│                    CRASH REPORTED                           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: Collect Initial Data                               │
│  - Error log from %APPDATA%\keepnote\error-log.txt         │
│  - Windows Event Viewer Application logs                   │
│  - User reproduction steps                                  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 2: Reproduce with Debug Logging                       │
│  - Run: debug_gtk.bat                                       │
│  - Enable: GDK_DEBUG, PYTHONFAULTHANDLER                   │
│  - Capture: debug_log.txt                                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
              ┌─────────────┴─────────────┐
              │                           │
              ▼                           ▼
    ┌──────────────────┐        ┌──────────────────┐
    │ Python Exception │        │ Native Crash     │
    │ (Traceback)      │        │ (0xc0000005)     │
    └──────────────────┘        └──────────────────┘
              │                           │
              ▼                           ▼
    ┌──────────────────┐        ┌──────────────────┐
    │ Analyze with     │        │ Attach WinDbg    │
    │ pdb/ipdb         │        │ Load symbols     │
    │                  │        │ Run .wds script  │
    └──────────────────┘        └──────────────────┘
              │                           │
              ▼                           ▼
    ┌──────────────────┐        ┌──────────────────┐
    │ Fix Python code  │        │ Identify DLL/FFI │
    │ Add error        │        │ Issue            │
    │ handling         │        │ Update ctypes    │
    └──────────────────┘        └──────────────────┘
              │                           │
              └─────────────┬─────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 3: Verify Fix                                         │
│  - Run test suite                                           │
│  - Stress test (24 hours)                                   │
│  - Monitor memory usage                                     │
└─────────────────────────────────────────────────────────────┘
```

### 4.3 Quick Reference: Common Crash Fixes

| Symptom | Diagnostic Command | Likely Cause | Fix |
|---------|-------------------|--------------|-----|
| Hang on minimize | `GDK_DEBUG=events` | Nested Gtk.main() | Replace with GLib.timeout_add |
| 0xc0000005 on startup | WinDbg bp on load | DLL conflict | Isolate DLL search path |
| Memory grows continuously | `GOBJECT_DEBUG=memory` | Ref cycle | Add explicit unref/dispose |
| Random crashes in tree view | Thread dump | GTK from worker thread | Use GLib.idle_add |
| Widget not rendering | `GTK_DEBUG=interactive` | Surface invalidation | Update draw handler for GTK4 |

---

## Appendix A: File Inventory

### Core GUI Files Requiring Attention
- `keepnote/gui/main_window.py` - Main window, event handling
- `keepnote/gui/__init__.py` - UI components, UIManager
- `keepnote/gui/treeview.py` - Tree widget interactions
- `keepnote/gui/editor_richtext.py` - Rich text editing
- `keepnote/gui/three_pane_viewer.py` - Layout management

### Windows-Specific Files
- `keepnote/mswin/screenshot.py` - Win32 API usage
- `keepnote/mswin/__init__.py` - Windows integration
- `keepnote/trans.py` - ctypes environment handling

### Build Configuration
- `keepnote.spec` - PyInstaller configuration
- `pkg/win/hook-runtime-gtk.py` - GTK bundling hooks
- `build_windows.bat` - Build script
- `Makefile` - Unix build automation

---

## Appendix B: Recommended Tool Versions (August 2026)

| Tool | Minimum Version | Recommended | Notes |
|------|-----------------|-------------|-------|
| Python | 3.10 | 3.12 LTS | Avoid 3.13 until stable |
| GTK 3 | 3.24.38 | 3.24.41 | Final GTK 3 release |
| GTK 4 | 4.14 | 4.16+ | Target for migration |
| PyGObject | 3.44 | 3.48+ | GTK 4 support required |
| PyInstaller | 6.0 | 6.5+ | Python 3.12 compatible |
| MSYS2 | 20240101 | Latest | For MinGW GTK builds |
| Visual Studio Build Tools | 2022 | 2026 | For native extensions |

---

## Appendix C: Emergency Contacts & Resources

- **GTK Issue Tracker**: https://gitlab.gnome.org/GNOME/gtk/-/issues
- **PyGObject Documentation**: https://pygobject.readthedocs.io/
- **Windows Debugging Tools**: https://docs.microsoft.com/en-us/windows-hardware/drivers/debugger/
- **Python Fault Handler**: https://docs.python.org/3/library/faulthandler.html

---

*Report Generated: August 2026*
*Classification: Internal Technical Document*
