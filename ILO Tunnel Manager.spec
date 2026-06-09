# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['ilo_tunnel/main.py'],
    pathex=[],
    binaries=[],
    datas=[('ilo_tunnel/resources', 'resources'), ('ilo_tunnel/models', 'ilo_tunnel/models'), ('ilo_tunnel/gui', 'ilo_tunnel/gui'), ('ilo_tunnel/services', 'ilo_tunnel/services'), ('ilo_tunnel/controllers', 'ilo_tunnel/controllers'), ('ilo_tunnel/app_settings.py', 'ilo_tunnel')],
    hiddenimports=['ilo_tunnel.app_settings', 'ilo_tunnel.models.server_types', 'ilo_tunnel.models.profile', 'ilo_tunnel.models.profile_manager', 'ilo_tunnel.services.ssh_manager', 'ilo_tunnel.services.port_checker', 'ilo_tunnel.controllers.connection_controller', 'ilo_tunnel.gui.dialogs', 'ilo_tunnel.gui.main_window', 'ilo_tunnel.gui.settings_dialog', 'ilo_tunnel.gui.server_types_dialog', 'ilo_tunnel.gui.widgets'],
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
