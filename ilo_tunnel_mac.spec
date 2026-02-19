# -*- mode: python ; coding: utf-8 -*-

import os
import sys

a = Analysis(
    ['run_app.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('ilo_tunnel/resources', 'ilo_tunnel/resources'),
        ('ilo_tunnel/models', 'ilo_tunnel/models'),
        ('ilo_tunnel/gui', 'ilo_tunnel/gui'),
        ('ilo_tunnel/utils', 'ilo_tunnel/utils'),
        ('ilo_tunnel/config.py', 'ilo_tunnel'),
        ('ilo_tunnel/ssh_manager.py', 'ilo_tunnel'),
        ('ilo_tunnel/__init__.py', 'ilo_tunnel'),
    ],
    hiddenimports=[
        'ilo_tunnel',
        'ilo_tunnel.models',
        'ilo_tunnel.models.server_types',
        'ilo_tunnel.models.profile',
        'ilo_tunnel.models.profile_manager',
        'ilo_tunnel.gui',
        'ilo_tunnel.gui.dialogs',
        'ilo_tunnel.gui.main_window',
        'ilo_tunnel.gui.widgets',
        'ilo_tunnel.config',
        'ilo_tunnel.ssh_manager',
        'ilo_tunnel.utils',
    ],
    hookspath=['hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
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
    icon='ilo_tunnel/resources/icon.icns',
    bundle_identifier='com.manuelf.ilotunnelmanager',
    info_plist={
        'NSHighResolutionCapable': True,
        'CFBundleName': 'ILO Tunnel Manager',
        'CFBundleDisplayName': 'ILO Tunnel Manager',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
        'NSHumanReadableCopyright': '© 2025 Manuel Fernández',
    },
)