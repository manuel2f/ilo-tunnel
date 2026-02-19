# ilo_tunnel/gui/__init__.py
"""
Módulo de interfaz gráfica para ILO Tunnel Manager.
"""

# Asegúrate de exportar lo necesario
from ilo_tunnel.gui.main_window import ILOTunnelApp
from ilo_tunnel.gui.dialogs import ConnectionProfileDialog, FolderManagementDialog
from ilo_tunnel.gui.widgets import PortStatusWidget, ConnectionStatusBar