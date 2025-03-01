# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['ilo_tunnel/main.py'],
    pathex=[],
    binaries=[],
    datas=[('ilo_tunnel/resources', 'resources'), ('ilo_tunnel/ssh_manager.py', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ILO Tunnel Manager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ILO Tunnel Manager',
)
app = BUNDLE(
    coll,
    name='ILO Tunnel Manager.app',
    icon=None,
    bundle_identifier=None,
)
