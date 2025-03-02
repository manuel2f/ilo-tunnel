# ilo_tunnel/models/__init__.py
"""
Módulo de modelos de datos para ILO Tunnel Manager.
"""

from .profile import ConnectionProfile
from .profile_manager import ProfileManager
from .server_types import get_server_types, get_server_ports, get_server_description, get_server_essential_ports