# PyInstaller hook: collect GTK3 runtime files at build time
# This hook runs during PyInstaller's analysis phase.

import os, sys, glob, shutil
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

# Collect GI typelibs
datas = collect_data_files('gi', include_py_files=False)

# Collect GTK3 data files
try:
    datas += collect_data_files('gnome', include_py_files=False)
except Exception:
    pass

# Try to collect cairo, pango, etc.
for pkg in ['cairo', 'pango', 'pangocairo', 'atk']:
    try:
        datas += collect_data_files(pkg, include_py_files=False)
    except Exception:
        pass

# Collect GTK DLLs from the Python environment
binaries = []
python_prefix = sys.prefix

# Common locations for GTK DLLs on Windows
dll_search_paths = [
    os.path.join(python_prefix, 'Library', 'bin'),
    os.path.join(python_prefix, 'lib'),
    os.path.join(python_prefix, 'bin'),
    os.path.join(python_prefix, 'Lib', 'site-packages'),
]

# GTK DLLs that must be bundled
gtk_dlls = [
    'libgtk-3-0.dll', 'libgdk-3-0.dll', 'libglib-2.0-0.dll',
    'libgobject-2.0-0.dll', 'libgio-2.0-0.dll', 'libgmodule-2.0-0.dll',
    'libatk-1.0-0.dll', 'libatk-bridge-2.0-0.dll', 'libcairo-2.dll',
    'libpango-1.0-0.dll', 'libpangocairo-1.0-0.dll', 'libpangoft2-1.0-0.dll',
    'libgdk_pixbuf-2.0-0.dll', 'libcairo-gobject-2.dll',
    'libepoxy-0.dll', 'libfontconfig-1.dll', 'libfreetype-6.dll',
    'libharfbuzz-0.dll', 'libpng16-16.dll', 'libjpeg-62.dll',
    'libtiff-5.dll', 'libwebp-7.dll', 'librsvg-2-2.dll',
    'libxml2-2.dll', 'libjasper-4.dll', 'liblcms2-2.dll',
    'libintl-8.dll', 'libiconv-2.dll', 'libwinpthread-1.dll',
    'libpcre2-8-0.dll', 'libffi-8.dll', 'libzlib-1.dll',
    'libgraphene-1.0-0.dll', 'libjson-glib-1.0-0.dll',
    'libgcc_s_seh-1.dll', 'libstdc++-6.dll', 'libbz2-1.dll',
    'libbrotlidec.dll', 'libbrotlicommon.dll', 'libexpat-1.dll',
    'libgettextsrc-8.dll', 'libgettextlib-8.dll', 'libidn2-0.dll',
    'libunistring-5.dll', 'libpsl-5.dll', 'libcrypto-3-x64.dll',
    'libssl-3-x64.dll', 'libcurl-4.dll', 'libssh2-1.dll',
    'libnghttp2-1.dll', 'libcares-2.dll', 'libntlm-0.dll',
]

for search_path in dll_search_paths:
    if not os.path.isdir(search_path):
        continue
    for dll in gtk_dlls:
        dll_path = os.path.join(search_path, dll)
        if os.path.exists(dll_path):
            binaries.append((dll_path, '.'))

# Collect all .typelib files for GI
for search_path in dll_search_paths:
    typelib_dir = os.path.join(search_path, '..', 'lib', 'girepository-1.0')
    if os.path.isdir(typelib_dir):
        for typelib in glob.glob(os.path.join(typelib_dir, '*.typelib')):
            datas.append((typelib, 'lib/girepository-1.0'))

# Collect share data (icons, themes)
for share_item in ['icons', 'themes', 'glib-2.0']:
    share_path = os.path.join(python_prefix, 'Library', 'share', share_item)
    if os.path.isdir(share_path):
        for root, dirs, files in os.walk(share_path):
            for f in files:
                src = os.path.join(root, f)
                rel = os.path.relpath(src, share_path)
                dst = os.path.join('share', share_item, rel)
                datas.append((src, dst))

# Collect etc configs (gtk-3.0, pango, fonts)
for etc_item in ['gtk-3.0', 'pango', 'fonts']:
    etc_path = os.path.join(python_prefix, 'Library', 'etc', etc_item)
    if os.path.isdir(etc_path):
        for root, dirs, files in os.walk(etc_path):
            for f in files:
                src = os.path.join(root, f)
                rel = os.path.relpath(src, etc_path)
                dst = os.path.join('etc', etc_item, rel)
                datas.append((src, dst))

# Collect gdk-pixbuf loaders
loaders_pattern = os.path.join(python_prefix, 'Library', 'lib', 'gdk-pixbuf-2.0', '2.10.0', 'loaders', '*.dll')
for loader in glob.glob(loaders_pattern):
    datas.append((loader, 'lib/gdk-pixbuf-2.0/2.10.0/loaders'))

# Copy loaders.cache if it exists
loaders_cache = os.path.join(python_prefix, 'Library', 'lib', 'gdk-pixbuf-2.0', '2.10.0', 'loaders.cache')
if os.path.exists(loaders_cache):
    datas.append((loaders_cache, 'lib/gdk-pixbuf-2.0/2.10.0'))
