# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[('cloudflared.exe', '.')],
    datas=[('templates', 'templates'), ('static', 'static'), ('minecraft_server', 'minecraft_server')],
    hiddenimports=['flask', 'flask_sqlalchemy', 'flask_login', 'flask_socketio', 'werkzeug', 'eventlet', 'psutil', 'pystray', 'PIL', 'requests', 'paramiko', 'bcrypt', 'cryptography', 'models.user', 'models.node', 'models.server', 'utils.security', 'utils.validation', 'utils.logging_config'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'pandas', 'scipy', 'IPython', 'jupyter', 'tkinter'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='TheOriginals',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
