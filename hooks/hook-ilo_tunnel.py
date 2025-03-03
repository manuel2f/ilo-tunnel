from PyInstaller.utils.hooks import collect_submodules

hiddenimports = (
    collect_submodules('ilo_tunnel.models') +
    collect_submodules('ilo_tunnel.gui') +
    collect_submodules('ilo_tunnel.utils')
)