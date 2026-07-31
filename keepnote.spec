# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for KeepNote (Windows 11)
Build with:  pyinstaller keepnote.spec
"""

import os
import sys
import site
import glob

block_cipher = None

a = Analysis(
    ['bin/keepnote'],
    pathex=[],
    binaries=[],
    datas=[
        # Resource files (icons, glade UI, translations)
        ('keepnote/rc', 'rc'),
        ('keepnote/images', 'images'),
        ('keepnote/extensions', 'extensions'),
    ],
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
        'gi.repository.Gtk',
        'gi.repository.Gdk',
        'gi.repository.GObject',
        'gi.repository.Pango',
        'gi.repository.GdkPixbuf',
        'gi.repository.PangoCairo',
        'gi.repository.GLib',
        'gi.repository.Gio',
        'gi.repository.Atk',
        'cairo',
        'pango',
        'pangocairo',
    ],
    hookspath=['pkg/win'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'PIL',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
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
    console=False,  # GUI application, no console window
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
