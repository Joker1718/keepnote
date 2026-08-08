# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for KeepNote (Windows 11)
Build with:  pyinstaller keepnote.spec

FIX: Environment-based GTK path detection replaces hardcoded paths (KEEP-PLAN-5.1)
"""

import os
import sys
import glob

block_cipher = None

# FIX: Environment-based GTK path detection for Windows (KEEP-PLAN-5.1)
# Replaces hardcoded C:\GTK paths
def get_gtk_runtime_data():
    """Detect GTK installation path from environment and sys.prefix."""
    gtk_paths = []

    # Priority 1: GTK_PATH environment variable
    if os.environ.get("GTK_PATH"):
        gtk_paths.append(os.environ["GTK_PATH"])

    # Priority 2: MSYS2/MinGW default location
    msys2_path = os.path.join(sys.prefix, "Library")
    if os.path.isdir(msys2_path):
        gtk_paths.append(msys2_path)

    # Priority 3: Conda/pip GTK installation
    conda_path = os.path.join(sys.prefix, "share", "gtk-3.0")
    if os.path.isdir(conda_path):
        gtk_paths.append(sys.prefix)

    return gtk_paths


# Collect GTK3 runtime data automatically
extra_datas = []
extra_binaries = []

gtk_prefixes = get_gtk_runtime_data()
if not gtk_prefixes:
    # Fallback to original behavior if no GTK found via env detection
    python_prefix = getattr(sys, 'base_prefix', sys.prefix)
    site_packages = next((p for p in sys.path if 'site-packages' in p), '')
    gtk_prefixes = [python_prefix]

print(f"Detected GTK prefixes: {gtk_prefixes}")

# 1. Collect .typelib files
for prefix in gtk_prefixes:
    for sp in [os.path.join(prefix, 'lib', 'girepository-1.0'),
               os.path.join(prefix, 'Library', 'lib', 'girepository-1.0')]:
        if os.path.isdir(sp):
            for tl in glob.glob(os.path.join(sp, '*.typelib')):
                extra_datas.append((tl, 'lib/girepository-1.0'))

# 2. Collect GTK DLLs from Python env
for prefix in gtk_prefixes:
    for bin_dir in [os.path.join(prefix, 'Library', 'bin'),
                     os.path.join(prefix, 'bin')]:
        if os.path.isdir(bin_dir):
            for dll in glob.glob(os.path.join(bin_dir, 'lib*.dll')):
                extra_binaries.append((dll, '.'))

# 3. Collect share data (icons, themes, schemas)
for prefix in gtk_prefixes:
    for item in ['icons', 'themes', 'glib-2.0']:
        src = os.path.join(prefix, 'Library', 'share', item)
        if os.path.isdir(src):
            extra_datas.append((src, os.path.join('share', item)))
        # Also check non-Library share directory
        src_alt = os.path.join(prefix, 'share', item)
        if os.path.isdir(src_alt) and src_alt != src:
            extra_datas.append((src_alt, os.path.join('share', item)))

    # 4. Collect etc configs (gtk-3.0, pango, fonts)
    for item in ['gtk-3.0', 'pango', 'fonts']:
        src = os.path.join(prefix, 'Library', 'etc', item)
        if os.path.isdir(src):
            extra_datas.append((src, os.path.join('etc', item)))

    # 5. Collect gdk-pixbuf loaders
    for loaders_dir in [os.path.join(prefix, 'Library', 'lib', 'gdk-pixbuf-2.0'),
                        os.path.join(prefix, 'lib', 'gdk-pixbuf-2.0')]:
        loaders_pattern = os.path.join(loaders_dir, '*', 'loaders', '*.dll')
        for loader in glob.glob(loaders_pattern):
            extra_datas.append((loader, os.path.dirname(os.path.dirname(loader))))

    # 6. Collect loaders.cache
    for cache_dir in [os.path.join(prefix, 'Library', 'lib', 'gdk-pixbuf-2.0'),
                      os.path.join(prefix, 'lib', 'gdk-pixbuf-2.0')]:
        loaders_cache = os.path.join(cache_dir, '*', 'loaders.cache')
        for cache in glob.glob(loaders_cache):
            extra_datas.append((cache, os.path.dirname(cache)))

    # 7. Collect gio modules
    for gio_dir in [os.path.join(prefix, 'Library', 'lib', 'gio', 'modules'),
                    os.path.join(prefix, 'lib', 'gio', 'modules')]:
        for gio_mod in glob.glob(os.path.join(gio_dir, '*.dll')):
            extra_binaries.append((gio_mod, os.path.dirname(gio_dir)))

print(f"Found {len(extra_binaries)} extra binaries, {len(extra_datas)} extra data dirs")

a = Analysis(
    ['bin/keepnote'],
    pathex=[],
    binaries=extra_binaries,
    datas=[
        # Resource files (icons, glade UI, translations)
        ('keepnote/rc', 'rc'),
        ('keepnote/images', 'images'),
        ('keepnote/extensions', 'extensions'),
    ] + extra_datas,
    hiddenimports=[
        'keepnote',
        'keepnote.gui',
        'keepnote.gui.richtext',
        'keepnote.notebook',
        'keepnote.notebook.connection',
        'keepnote.notebook.connection.fs',
        'keepnote.compat',
        'keepnote.server',
        'keepnote.mswin',
        'gi',
        'gi.repository.Gtk', 'gi.repository.Gdk', 'gi.repository.GObject',
        'gi.repository.Pango', 'gi.repository.GdkPixbuf', 'gi.repository.PangoCairo',
        'gi.repository.GLib', 'gi.repository.Gio', 'gi.repository.Atk',
        'gi.repository.GdkPixdata',
        'cairo', 'pango', 'pangocairo',
    ],
    hookspath=['pkg/win'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'matplotlib', 'numpy', 'scipy',
        'PIL', 'PyQt5', 'PyQt6', 'PySide2', 'PySide6',
        'IPython', 'jupyter', 'notebook',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='KeepNote',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    icon='keepnote/images/keepnote.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='KeepNote',
)
