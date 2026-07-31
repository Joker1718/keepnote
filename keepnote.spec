# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for KeepNote (Windows 11)
Build with:  pyinstaller keepnote.spec
"""

import os
import sys
import glob

block_cipher = None

# Collect GTK3 runtime data automatically
extra_datas = []
extra_binaries = []

python_prefix = getattr(sys, 'base_prefix', sys.prefix)
site_packages = next((p for p in sys.path if 'site-packages' in p), '')

# 1. Collect .typelib files
for sp in [site_packages, os.path.join(python_prefix, 'Library', 'lib', 'girepository-1.0'),
           os.path.join(python_prefix, 'lib', 'girepository-1.0')]:
    if os.path.isdir(sp):
        for tl in glob.glob(os.path.join(sp, '*.typelib')):
            extra_datas.append((tl, 'lib/girepository-1.0'))

# 2. Collect GTK DLLs from Python env
for bin_dir in [os.path.join(python_prefix, 'Library', 'bin'),
                 os.path.join(python_prefix, 'bin'),
                 site_packages]:
    if os.path.isdir(bin_dir):
        for dll in glob.glob(os.path.join(bin_dir, 'lib*.dll')):
            extra_binaries.append((dll, '.'))

# 3. Collect share data (icons, themes, schemas)
for item in ['icons', 'themes', 'glib-2.0']:
    src = os.path.join(python_prefix, 'Library', 'share', item)
    if os.path.isdir(src):
        extra_datas.append((src, os.path.join('share', item)))

# 4. Collect etc configs (gtk-3.0, pango, fonts)
for item in ['gtk-3.0', 'pango', 'fonts']:
    src = os.path.join(python_prefix, 'Library', 'etc', item)
    if os.path.isdir(src):
        extra_datas.append((src, os.path.join('etc', item)))

# 5. Collect gdk-pixbuf loaders
loaders_pattern = os.path.join(python_prefix, 'Library', 'lib', 'gdk-pixbuf-2.0', '2.10.0', 'loaders', '*.dll')
for loader in glob.glob(loaders_pattern):
    extra_datas.append((loader, 'lib/gdk-pixbuf-2.0/2.10.0/loaders'))

# 6. Collect loaders.cache
loaders_cache = os.path.join(python_prefix, 'Library', 'lib', 'gdk-pixbuf-2.0', '2.10.0', 'loaders.cache')
if os.path.exists(loaders_cache):
    extra_datas.append((loaders_cache, 'lib/gdk-pixbuf-2.0/2.10.0'))

# 7. Collect gio modules
for gio_mod in glob.glob(os.path.join(python_prefix, 'Library', 'lib', 'gio', 'modules', '*.dll')):
    extra_binaries.append((gio_mod, 'lib/gio/modules'))

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
