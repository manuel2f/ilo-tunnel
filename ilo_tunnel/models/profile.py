# ilo_tunnel/models/profile.py
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class ConnectionProfile:
    """Modelo de datos para perfiles de conexión"""

    name: str
    ilo_ip: str
    ssh_user: str
    gateway_ip: str
    server_type: str = "HP/Huawei"  # Tipo de servidor por defecto
    ssh_port: int = 22
    local_ip: str = "127.0.0.1"
    key_path: str = "~/.ssh/id_rsa"
    ports: Dict[str, bool] = field(default_factory=dict)
    custom_ports: bool = False  # Flag para indicar si se usan puertos personalizados
    # Opciones SSH por perfil (antes eran globales o estaban hardcodeadas)
    use_sudo: bool = True
    compress: bool = False
    verbose: bool = False
    identity_only: bool = True
    strict_host_key: bool = False
    connect_timeout: int = 30

    @classmethod
    def from_dict(cls, data: dict) -> "ConnectionProfile":
        """Crea un perfil a partir de un diccionario (tolerante a campos ausentes)."""
        return cls(
            name=data.get("name", ""),
            ilo_ip=data.get("ilo_ip", ""),
            ssh_user=data.get("ssh_user", ""),
            gateway_ip=data.get("gateway_ip", ""),
            server_type=data.get("server_type", "HP/Huawei"),
            ssh_port=data.get("ssh_port", 22),
            local_ip=data.get("local_ip", "127.0.0.1"),
            key_path=data.get("key_path", "~/.ssh/id_rsa"),
            ports=data.get("ports", {}),
            custom_ports=data.get("custom_ports", False),
            use_sudo=data.get("use_sudo", True),
            compress=data.get("compress", False),
            verbose=data.get("verbose", False),
            identity_only=data.get("identity_only", True),
            strict_host_key=data.get("strict_host_key", False),
            connect_timeout=data.get("connect_timeout", 30),
        )

    def to_dict(self) -> dict:
        """Convierte el perfil a un diccionario"""
        return {
            "name": self.name,
            "ilo_ip": self.ilo_ip,
            "ssh_user": self.ssh_user,
            "gateway_ip": self.gateway_ip,
            "server_type": self.server_type,
            "ssh_port": self.ssh_port,
            "local_ip": self.local_ip,
            "key_path": self.key_path,
            "ports": self.ports,
            "custom_ports": self.custom_ports,
            "use_sudo": self.use_sudo,
            "compress": self.compress,
            "verbose": self.verbose,
            "identity_only": self.identity_only,
            "strict_host_key": self.strict_host_key,
            "connect_timeout": self.connect_timeout,
        }

    def is_valid(self) -> bool:
        """Valida que el perfil tenga los campos requeridos"""
        return bool(self.name and self.ilo_ip and self.ssh_user and self.gateway_ip)
