# ilo_tunnel/models/server_types.py
import json
from typing import Dict, List

from ..app_settings import make_qsettings

# Tipos de servidor predefinidos (no editables ni eliminables)
DEFAULT_SERVER_TYPES: Dict[str, dict] = {
    "HP/Huawei": {
        "description": "iLO & iBMC",
        "ports": {
            22: "SSH",
            80: "HTTP",
            443: "HTTPS",
            23: "Telnet",
            3389: "RDP",
            17988: "iLO",
            9300: "iLO",
            17990: "iLO",
            3002: "iLO",
            2198: "iLO",
        },
        "essential_ports": [22, 80, 443],
    },
    "Dell": {
        "description": "iDRAC",
        "ports": {
            22: "SSH",
            80: "HTTP",
            443: "HTTPS",
            623: "IPMI",
            5000: "iDRAC",
            5900: "VNC",
            5901: "VNC",
        },
        "essential_ports": [22, 80, 443],
    },
    "Lenovo": {
        "description": "IMM o XCC",
        "ports": {
            22: "SSH",
            80: "HTTP",
            443: "HTTPS",
            5900: "VNC",
            5986: "WinRM",
            8889: "IMM/XCC",
            8080: "IMM/XCC",
        },
        "essential_ports": [22, 80, 443],
    },
    "Cisco": {
        "description": "Servidores Cisco UCS con interfaz CIMC",
        "ports": {
            22: "SSH",
            80: "HTTP",
            443: "HTTPS",
            623: "IPMI",
            5988: "CIMC",
            8443: "CIMC Web",
        },
        "essential_ports": [22, 80, 443],
    },
    "Personalizado": {
        "description": "Configuración de puertos personalizada",
        "ports": {},
        "essential_ports": [22, 80, 443],
    },
}

_USER_TYPES_KEY = "custom_server_types"


def _settings():
    return make_qsettings()


def _load_user_types() -> Dict[str, dict]:
    """Carga los tipos de servidor definidos por el usuario desde QSettings."""
    raw = _settings().value(_USER_TYPES_KEY, "{}")
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except (ValueError, TypeError):
        return {}


def _save_user_types(types: Dict[str, dict]) -> None:
    _settings().setValue(_USER_TYPES_KEY, json.dumps(types))


def _all_types() -> Dict[str, dict]:
    """Tipos predefinidos + definidos por el usuario (estos pueden sobrescribir)."""
    merged = dict(DEFAULT_SERVER_TYPES)
    merged.update(_load_user_types())
    return merged


def _normalize_ports(ports: dict) -> Dict[int, str]:
    """Convierte claves de puerto a int (JSON las guarda como str)."""
    result: Dict[int, str] = {}
    for key, name in ports.items():
        try:
            result[int(key)] = name
        except (TypeError, ValueError):
            continue
    return result


# --------------------------------------------------------------------- consultas
def get_server_types() -> List[str]:
    """Devuelve la lista de tipos de servidores disponibles."""
    return list(_all_types().keys())


def get_server_ports(server_type: str) -> Dict[int, str]:
    """Devuelve los puertos {puerto: descripción} de un tipo de servidor."""
    entry = _all_types().get(server_type)
    if not entry:
        return {}
    return _normalize_ports(entry.get("ports", {}))


def get_server_essential_ports(server_type: str) -> List[int]:
    """Devuelve los puertos esenciales a monitorear de un tipo de servidor."""
    entry = _all_types().get(server_type)
    if not entry:
        return [22, 80, 443]
    return list(entry.get("essential_ports", [22, 80, 443]))


def get_server_description(server_type: str) -> str:
    """Devuelve la descripción de un tipo de servidor."""
    entry = _all_types().get(server_type)
    return entry.get("description", "") if entry else ""


# ------------------------------------------------------------------- edición
def is_builtin(server_type: str) -> bool:
    """True si el tipo es predefinido (no editable/eliminable por el usuario)."""
    return server_type in DEFAULT_SERVER_TYPES


def save_user_server_type(
    name: str,
    ports: Dict[int, str],
    description: str = "",
    essential_ports: List[int] = None,
) -> bool:
    """Crea o actualiza un tipo de servidor definido por el usuario."""
    name = (name or "").strip()
    if not name or is_builtin(name):
        return False
    types = _load_user_types()
    types[name] = {
        "description": description,
        "ports": {str(p): n for p, n in ports.items()},
        "essential_ports": essential_ports or [22, 80, 443],
    }
    _save_user_types(types)
    return True


def delete_user_server_type(name: str) -> bool:
    """Elimina un tipo de servidor definido por el usuario."""
    types = _load_user_types()
    if name in types:
        del types[name]
        _save_user_types(types)
        return True
    return False
