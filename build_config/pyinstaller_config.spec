# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller configuration for The Originals
Creates a standalone executable for easy distribution
"""

import os
from PyInstaller.utils.hooks import collect_all, collect_data_files
from pathlib import Path

# Get the base directory
base_dir = Path(__file__).parent.parent

# Collect all data files needed
datas = []

# Add templates
datas += collect_data_files('templates', include_py_files=False)

# Add static files
datas += collect_data_files('static', include_py_files=False)

# Add configuration files
datas += [
    (str(base_dir / 'templates'), 'templates'),
    (str(base_dir / 'static'), 'static'),
    (str(base_dir / 'cloudflared.exe'), '.'),
    (str(base_dir / 'minecraft_server'), 'minecraft_server'),
]

# Hidden imports - modules that PyInstaller might miss
hiddenimports = [
    'flask',
    'flask_sqlalchemy',
    'flask_login',
    'flask_socketio',
    'werkzeug',
    'jinja2',
    'eventlet',
    'eventlet.wsgi',
    'eventlet.green',
    'eventlet.green.socket',
    'eventlet.green.threading',
    'eventlet.green.time',
    'waitress',
    'psutil',
    'pystray',
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',
    'PIL.ImageFont',
    'requests',
    'paramiko',
    'python_nmap',
    'bcrypt',
    'cryptography',
    'sqlite3',
    'json',
    'yaml',
    'logging',
    'logging.handlers',
    'subprocess',
    'threading',
    'queue',
    'socketio',
    'engineio',
    'models.user',
    'models.node',
    'models.server',
    'utils.security',
    'utils.validation',
    'utils.logging_config',
]

# Collect all dependencies
tmp_ret = collect_all('flask')
datas += tmp_ret[0]; binaries = tmp_ret[1]; hiddenimports += tmp_ret[2]

tmp_ret = collect_all('flask_sqlalchemy')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

tmp_ret = collect_all('flask_socketio')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

tmp_ret = collect_all('eventlet')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

tmp_ret = collect_all('socketio')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# Analysis configuration
a = Analysis(
    [str(base_dir / 'app.py')],
    pathex=[str(base_dir)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'IPython',
        'jupyter',
        'notebook',
        'tkinter',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Remove duplicate data files
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Executable configuration
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='TheOriginals',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to False for windowed app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(base_dir / 'static' / 'favicon.ico') if (base_dir / 'static' / 'favicon.ico').exists() else None,
    version_file=None,
)

# Optional: Create a directory distribution instead of single file
# Uncomment the following for faster startup (but multiple files)
"""
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TheOriginals',
)
""" 