# ilo_tunnel/services/port_checker.py
import socket
from typing import List, Tuple

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot


class PortChecker(QObject):
    """Sondea puertos TCP locales en un hilo aparte para no bloquear la UI.

    Diseñado para vivir en un ``QThread`` (moveToThread). El método ``check`` se
    invoca por señal y emite ``result`` por cada puerto comprobado.
    """

    result = pyqtSignal(int, bool)  # puerto local, está abierto

    @pyqtSlot(list)
    def check(self, ports: List[Tuple[str, int]]) -> None:
        """Comprueba una lista de (host, puerto_local) y emite el resultado."""
        for host, port in ports:
            self.result.emit(port, self._probe(host, port))

    @staticmethod
    def _probe(host: str, port: int) -> bool:
        try:
            with socket.create_connection((host, port), timeout=1.0):
                return True
        except OSError:
            return False
