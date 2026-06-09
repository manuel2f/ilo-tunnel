# ilo_tunnel/app_settings.py
"""Fuente única de ajustes globales de la aplicación.

Centraliza el acceso a QSettings que antes estaba disperso por main_window.
Cada ajuste se declara en SCHEMA con su valor por defecto y tipo, de modo que
``get``/``set``/``reset`` son consistentes y tipados.
"""
import os
from typing import Any, Dict, Tuple

from PyQt6.QtCore import QSettings

ORGANIZATION = "ILOTunnel"
APPLICATION = "ILOTunnelApp"

# Si está definida, los ajustes se leen/escriben en este fichero INI en lugar de
# en el almacén nativo del sistema. Pensado para tests (aislamiento real, ya que
# en macOS QSettings nativo ignora HOME).
_OVERRIDE_ENV = "ILO_TUNNEL_SETTINGS_FILE"


def make_qsettings() -> QSettings:
    """Crea el QSettings de la app, honrando el override de entorno para tests."""
    override = os.environ.get(_OVERRIDE_ENV)
    if override:
        return QSettings(override, QSettings.Format.IniFormat)
    return QSettings(ORGANIZATION, APPLICATION)


# clave -> (valor por defecto, tipo)
SCHEMA: Dict[str, Tuple[Any, type]] = {
    # Generales
    "auto_start": (False, bool),
    "minimize_to_tray": (False, bool),
    "show_notifications": (True, bool),
    "confirm_exit": (True, bool),
    # SSH
    "ssh_timeout": (30, int),
    "reconnect_attempts": (3, int),
    "auto_reconnect": (False, bool),
    "identity_only": (True, bool),
    "strict_host_key": (False, bool),
    "use_sudo": (True, bool),
    # Interfaz
    "console_font_size": (9, int),
    "auto_scroll": (True, bool),
    # Sesión
    "last_folder": ("DEFAULT", str),
    "last_profile": ("", str),
}


class AppSettings:
    """Acceso tipado a los ajustes globales persistidos en QSettings."""

    def __init__(self) -> None:
        self._settings = make_qsettings()

    def get(self, key: str) -> Any:
        """Devuelve el valor de ``key`` con su tipo correcto y valor por defecto."""
        default, typ = SCHEMA[key]
        return self._settings.value(key, default, type=typ)

    def set(self, key: str, value: Any) -> None:
        """Persiste ``value`` para ``key`` (debe existir en SCHEMA)."""
        if key not in SCHEMA:
            raise KeyError(f"Ajuste desconocido: {key}")
        self._settings.setValue(key, value)

    def reset(self) -> None:
        """Restaura todos los ajustes de SCHEMA a sus valores por defecto."""
        for key, (default, _typ) in SCHEMA.items():
            self._settings.setValue(key, default)

    @property
    def qsettings(self) -> QSettings:
        """QSettings subyacente (para claves no declaradas como perfiles)."""
        return self._settings
