# ilo_tunnel/controllers/connection_controller.py
from typing import List, Tuple

from PyQt6.QtCore import QObject, QThread, QTimer, pyqtSignal

from ..models.profile import ConnectionProfile
from ..models.server_types import get_server_ports
from ..services.port_checker import PortChecker
from ..services.ssh_manager import SSHManager

# Hosts locales cuyos puertos tiene sentido sondear
_LOCAL_HOSTS = ("127.0.0.1", "localhost")


def build_port_mappings(profile: ConnectionProfile) -> List[str]:
    """Construye los mapeos ``local:port:ilo:port`` a partir de un perfil.

    Función pura (sin estado ni Qt) para poder testearla de forma aislada.
    """
    selected = [int(p) for p, enabled in profile.ports.items() if enabled]
    if not selected and not profile.custom_ports:
        # Perfil antiguo sin selección explícita: usar los del tipo de servidor
        selected = list(get_server_ports(profile.server_type).keys())
    return [
        f"{profile.local_ip}:{port}:{profile.ilo_ip}:{port}"
        for port in sorted(selected)
    ]


class ConnectionController(QObject):
    """Orquesta perfil ↔ SSHManager ↔ vista.

    Extrae de ``main_window`` la lógica de negocio: construcción de mapeos,
    arranque/parada del túnel con las opciones del perfil y monitorización de
    puertos en un hilo aparte.
    """

    # Señales reenviadas/derivadas para la vista
    output = pyqtSignal(str)
    error = pyqtSignal(str)
    connection_changed = pyqtSignal(bool, str)  # conectado, mensaje
    finished = pyqtSignal(int, str)
    port_status = pyqtSignal(int, bool)  # puerto local, está abierto
    _request_check = pyqtSignal(list)  # interno: dispara el sondeo en el hilo

    def __init__(self, app_settings, parent=None):
        super().__init__(parent)
        self.settings = app_settings
        self.ssh = SSHManager(self)
        self._active_mappings: List[Tuple[str, int]] = []

        # Reenviar señales del SSHManager
        self.ssh.output_ready.connect(self.output)
        self.ssh.error_ready.connect(self.error)
        self.ssh.connection_status.connect(self.connection_changed)
        self.ssh.process_finished.connect(self.finished)

        # Monitor de puertos en hilo aparte
        self._checker = PortChecker()
        self._checker_thread = QThread(self)
        self._checker.moveToThread(self._checker_thread)
        self._checker.result.connect(self.port_status)
        self._request_check.connect(self._checker.check)
        self._checker_thread.start()

        self._monitor = QTimer(self)
        self._monitor.timeout.connect(self._poll_ports)

    # ------------------------------------------------------------- acciones
    def start(self, profile: ConnectionProfile) -> bool:
        """Inicia el túnel para ``profile``. Devuelve si se lanzó el proceso."""
        mappings = build_port_mappings(profile)
        if not mappings:
            self.error.emit("Debes seleccionar al menos un puerto para tunelizar.")
            return False

        # Puertos locales a monitorear (solo los expuestos en localhost)
        self._active_mappings = [
            (profile.local_ip, int(p))
            for p, enabled in profile.ports.items()
            if enabled and profile.local_ip in _LOCAL_HOSTS
        ]

        started = self.ssh.create_tunnel(
            key_path=profile.key_path,
            ssh_port=profile.ssh_port,
            port_mappings=mappings,
            user=profile.ssh_user,
            gateway=profile.gateway_ip,
            verbose=profile.verbose,
            compress=profile.compress,
            identity_only=profile.identity_only,
            timeout=profile.connect_timeout,
            use_sudo=profile.use_sudo,
            strict_host_key=profile.strict_host_key,
        )
        if started:
            self.ssh.set_auto_reconnect(
                self.settings.get("auto_reconnect"),
                self.settings.get("reconnect_attempts"),
            )
            self._monitor.start(2000)
        return started

    def stop(self) -> bool:
        """Detiene el túnel y la monitorización."""
        self._monitor.stop()
        return self.ssh.stop_tunnel()

    def is_connected(self) -> bool:
        return self.ssh.is_connected()

    def local_ip_addresses(self) -> List[str]:
        return self.ssh.get_local_ip_addresses()

    def shutdown(self) -> None:
        """Detiene el hilo de monitorización limpiamente (al cerrar la app)."""
        self._monitor.stop()
        self._checker_thread.quit()
        self._checker_thread.wait(2000)

    # -------------------------------------------------------------- interno
    def _poll_ports(self) -> None:
        if self._active_mappings:
            self._request_check.emit(self._active_mappings)
