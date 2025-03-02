def get_server_description(server_type: str) -> str:
    """
    Devuelve la descripción de un tipo de servidor
    
    Args:
        server_type: Tipo de servidor
        
    Returns:
        Descripción del tipo de servidor
    """
    if server_type in SERVER_TYPES:
        return SERVER_TYPES[server_type]["description"]
    return ""# ilo_tunnel/models/server_types.py
from typing import Dict, List, Set

# Definición de los puertos para diferentes tipos de servidores
SERVER_TYPES = {
    "HP/Huawei": {
        "name": "HP/Huawei",
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
            2198: "iLO"
        },
        "essential_ports": [22, 80, 443]  # Puertos esenciales a monitorear
    },
    "Dell": {
        "name": "Dell",
        "description": "iDRAC",
        "ports": {
            22: "SSH",
            80: "HTTP",
            443: "HTTPS",
            623: "IPMI",
            5000: "iDRAC",
            5900: "VNC",
            5901: "VNC"
        },
        "essential_ports": [22, 80, 443]  # Puertos esenciales a monitorear
    },
    "Lenovo": {
        "name": "Lenovo",
        "description": "IMM o XCC",
        "ports": {
            22: "SSH",
            80: "HTTP",
            443: "HTTPS",
            5900: "VNC",
            5986: "WinRM",
            8889: "IMM/XCC",
            8080: "IMM/XCC"
        },
        "essential_ports": [22, 80, 443]  # Puertos esenciales a monitorear
    },
    "Cisco": {
        "name": "Cisco",
        "description": "Servidores Cisco UCS con interfaz CIMC",
        "ports": {
            22: "SSH",
            80: "HTTP",
            443: "HTTPS",
            623: "IPMI",
            5988: "CIMC",
            8443: "CIMC Web"
        },
        "essential_ports": [22, 80, 443]  # Puertos esenciales a monitorear
    },
    "Personalizado": {
        "name": "Personalizado",
        "description": "Configuración de puertos personalizada",
        "ports": {},
        "essential_ports": [22, 80, 443]  # Puertos esenciales a monitorear
    }
}

def get_server_types() -> List[str]:
    """Devuelve la lista de tipos de servidores disponibles"""
    return list(SERVER_TYPES.keys())

def get_server_ports(server_type: str) -> Dict[int, str]:
    """
    Devuelve los puertos para un tipo de servidor
    
    Args:
        server_type: Tipo de servidor (HP/Huawei, Dell, etc.)
    
    Returns:
        Diccionario con los puertos y sus descripciones
    """
    if server_type in SERVER_TYPES:
        return SERVER_TYPES[server_type]["ports"]
    return {}

def get_server_essential_ports(server_type: str) -> List[int]:
    """
    Devuelve los puertos esenciales para un tipo de servidor
    
    Args:
        server_type: Tipo de servidor (HP/Huawei, Dell, etc.)
    
    Returns:
        Lista de puertos esenciales
    """
    if server_type in SERVER_TYPES:
        return SERVER_TYPES[server_type]["essential_ports"]
    return [22, 80, 443]  # Por defecto, monitorear SSH, HTTP y HTTPS