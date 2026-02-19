# ilo_tunnel/ssh_manager.py
import os
import platform
import subprocess
import signal
import re
from typing import List, Dict, Optional, Tuple

from PyQt6.QtCore import QObject, QProcess, pyqtSignal, QTimer


class SSHManager(QObject):
    """
    Gestor de túneles SSH con soporte para:
    - Comprobación de conexiones activas
    - Reconexión automática
    - Comprobación de estado de los puertos
    - Modo verbose
    """

    # Señales para comunicar con la interfaz
    output_ready = pyqtSignal(str)
    error_ready = pyqtSignal(str)
    process_finished = pyqtSignal(int, str)
    status_changed = pyqtSignal(str, bool)  # puerto, está abierto
    connection_status = pyqtSignal(bool, str)  # conectado, mensaje

    def __init__(self, parent=None):
        super().__init__(parent)
        self.process = None
        self.auto_reconnect = False
        self.reconnect_timer = QTimer(self)
        self.reconnect_timer.timeout.connect(self._try_reconnect)
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 3

        # Guardar los últimos parámetros usados para reconexión
        self.last_config = {
            "key_path": None,
            "ssh_port": None,
            "port_mappings": None,
            "user": None,
            "gateway": None,
            "verbose": False,
            "compress": False,
            "identity_only": True,
            "timeout": 30,
        }

    def create_tunnel(
        self,
        key_path: str,
        ssh_port: int,
        port_mappings: List[str],
        user: str,
        gateway: str,
        verbose: bool = False,
        compress: bool = False,
        identity_only: bool = True,
        timeout: int = 30,
    ) -> bool:
        """
        Crea un túnel SSH con los parámetros especificados

        Args:
            key_path: Ruta a la clave SSH
            ssh_port: Puerto SSH
            port_mappings: Lista de mapeos de puertos en formato "local_ip:local_port:remote_host:remote_port"
            user: Nombre de usuario SSH
            gateway: Dirección del gateway
            verbose: Mostrar mensajes detallados de SSH
            compress: Usar compresión SSH
            identity_only: Usar solo la identidad especificada (sin fallback a otras claves)
            timeout: Tiempo de espera de conexión en segundos

        Returns:
            True si el proceso se inició correctamente, False en caso contrario
        """
        # Guardar parámetros para posible reconexión
        self.last_config = {
            "key_path": key_path,
            "ssh_port": ssh_port,
            "port_mappings": port_mappings,
            "user": user,
            "gateway": gateway,
            "verbose": verbose,
            "compress": compress,
            "identity_only": identity_only,
            "timeout": timeout,
        }

        # Generar comando SSH
        cmd = ["sudo", "ssh"]

        # Identidad
        cmd.extend(["-i", os.path.expanduser(key_path)])

        # Puerto SSH
        cmd.extend(["-p", str(ssh_port)])

        # Opciones adicionales
        if verbose:
            cmd.append("-v")
        if compress:
            cmd.append("-C")
        if identity_only:
            cmd.append("-o")
            cmd.append("IdentitiesOnly=yes")

        # Timeout
        cmd.extend(["-o", f"ConnectTimeout={timeout}"])

        # Server alive options
        cmd.extend(["-o", "ServerAliveInterval=15"])
        cmd.extend(["-o", "ServerAliveCountMax=3"])

        # No host key checking (más conveniente para ILO)
        cmd.extend(["-o", "StrictHostKeyChecking=no"])
        cmd.extend(["-o", "UserKnownHostsFile=/dev/null"])

        # Add port mappings
        for mapping in port_mappings:
            cmd.extend(["-L", mapping])

        # Add destination
        cmd.append(f"{user}@{gateway}")

        self.output_ready.emit(f"Iniciando túnel SSH: {' '.join(cmd)}")

        # Start process
        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self._handle_stdout)
        self.process.readyReadStandardError.connect(self._handle_stderr)
        self.process.finished.connect(self._handle_finished)

        # imprimir comando completo

        print(cmd[0], cmd[1:])

        self.process.start(cmd[0], cmd[1:])

        # Indicar que estamos conectando
        self.connection_status.emit(False, "Conectando...")

        return self.process.waitForStarted(5000)  # Esperar 5 segundos máximo

    def stop_tunnel(self) -> bool:
        """
        Detiene el túnel SSH en ejecución

        Returns:
            True si se detuvo correctamente, False en caso contrario
        """
        if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
            # Desactivar reconexión automática
            self.auto_reconnect = False
            self.reconnect_timer.stop()

            # Terminar proceso
            self.process.terminate()

            if not self.process.waitForFinished(3000):  # Esperar 3 segundos
                self.output_ready.emit("Forzando terminación del proceso...")
                self.process.kill()

            self.connection_status.emit(False, "Desconectado")
            return True

        return False

    def set_auto_reconnect(self, enabled: bool, max_attempts: int = 3) -> None:
        """
        Activa o desactiva la reconexión automática

        Args:
            enabled: True para activar, False para desactivar
            max_attempts: Número máximo de intentos de reconexión
        """
        self.auto_reconnect = enabled
        self.max_reconnect_attempts = max_attempts
        self.reconnect_attempts = 0

        self.output_ready.emit(
            f"Reconexión automática {'activada' if enabled else 'desactivada'}"
            + (f" (máx. {max_attempts} intentos)" if enabled else "")
        )

    def reconnect(self) -> bool:
        """
        Intenta reconectar con los últimos parámetros usados

        Returns:
            True si se inició la reconexión, False en caso contrario
        """
        # Verificar que tengamos parámetros previos
        if not all(
            [
                self.last_config["key_path"],
                self.last_config["ssh_port"],
                self.last_config["port_mappings"],
                self.last_config["user"],
                self.last_config["gateway"],
            ]
        ):
            self.output_ready.emit(
                "No hay parámetros de conexión previos para reconectar"
            )
            return False

        # Detener cualquier proceso existente
        if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
            self.stop_tunnel()

        # Reconectar
        self.output_ready.emit("Intentando reconexión...")
        return self.create_tunnel(
            self.last_config["key_path"],
            self.last_config["ssh_port"],
            self.last_config["port_mappings"],
            self.last_config["user"],
            self.last_config["gateway"],
            self.last_config["verbose"],
            self.last_config["compress"],
            self.last_config["identity_only"],
            self.last_config["timeout"],
        )

    def check_port_status(self, port_mappings: List[str]) -> None:
        """
        Comprueba el estado de los puertos mapeados

        Args:
            port_mappings: Lista de mapeos de puertos en formato "local_ip:local_port:remote_host:remote_port"
        """
        for mapping in port_mappings:
            parts = mapping.split(":")
            if len(parts) >= 2:
                local_ip = parts[0]
                local_port = parts[1]

                # Solo comprobar localhost o 127.0.0.1 por seguridad
                if local_ip in ["127.0.0.1", "localhost"]:
                    is_open = self._check_port_open(local_ip, int(local_port))
                    port_name = f"{local_ip}:{local_port}"
                    self.status_changed.emit(port_name, is_open)

    def _check_port_open(self, host: str, port: int) -> bool:
        """
        Comprueba si un puerto está abierto

        Args:
            host: Host donde comprobar
            port: Puerto a comprobar

        Returns:
            True si el puerto está abierto, False en caso contrario
        """
        import socket

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1.0)
            s.connect((host, port))
            s.close()
            return True
        except:
            return False

    def get_local_ip_addresses(self) -> List[str]:
        """
        Obtiene las direcciones IP locales del sistema

        Returns:
            Lista de direcciones IP
        """
        import socket

        ips = ["127.0.0.1"]  # Siempre incluir loopback

        try:
            # Método 1: Usar socket para obtener la dirección IP local
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                # No importa si no se puede conectar realmente
                s.connect(("10.255.255.255", 1))
                ip = s.getsockname()[0]
                if ip not in ips:
                    ips.append(ip)
            except Exception:
                pass
            finally:
                s.close()

            # Método 2: Obtener todas las interfaces de red
            for family, _, _, _, sockaddr in socket.getaddrinfo("localhost", None):
                if family == socket.AF_INET:  # Solo IPv4
                    ip = sockaddr[0]
                    if ip not in ips and ip != "127.0.0.1":
                        ips.append(ip)

            # Método 3: Uso de hostname (si los anteriores fallan)
            try:
                hostname = socket.gethostname()
                host_ips = socket.gethostbyname_ex(hostname)[2]
                for ip in host_ips:
                    if ip not in ips and not ip.startswith("127."):
                        ips.append(ip)
            except Exception:
                pass

        except Exception as e:
            print(f"Advertencia al detectar IPs: {e}")
            # Asegurar que al menos tenemos loopback
            if "127.0.0.1" not in ips:
                ips = ["127.0.0.1"]

        # Eliminar cualquier duplicado y ordenar
        return sorted(list(dict.fromkeys(ips)))

    def is_connected(self) -> bool:
        """
        Comprueba si hay un túnel SSH activo

        Returns:
            True si hay un túnel activo, False en caso contrario
        """
        return (
            self.process is not None
            and self.process.state() != QProcess.ProcessState.NotRunning
        )

    def _handle_stdout(self) -> None:
        """Procesa la salida estándar del proceso"""
        if self.process:
            data = self.process.readAllStandardOutput().data().decode()
            self.output_ready.emit(data)

            # Detectar patrones de conexión exitosa
            if "Authenticated to" in data:
                self.connection_status.emit(True, "Conectado")
                self.reconnect_attempts = 0  # Resetear contador de intentos

    def _handle_stderr(self) -> None:
        """Procesa la salida de error del proceso"""
        if self.process:
            data = self.process.readAllStandardError().data().decode()
            self.error_ready.emit(data)

            # Detectar errores comunes
            if any(
                pattern in data
                for pattern in [
                    "Connection refused",
                    "Connection timed out",
                    "No route to host",
                    "Host key verification failed",
                ]
            ):
                self.connection_status.emit(False, "Error de conexión")

    def _handle_finished(
        self, exit_code: int, exit_status: QProcess.ExitStatus
    ) -> None:
        """
        Maneja la finalización del proceso

        Args:
            exit_code: Código de salida
            exit_status: Estado de salida (normal o crash)
        """
        # Determinar mensaje según el código de salida
        status_msg = (
            "Finalizado normalmente"
            if exit_status == QProcess.ExitStatus.NormalExit
            else "Terminado inesperadamente"
        )

        # Enviar señal
        self.process_finished.emit(exit_code, status_msg)
        self.connection_status.emit(False, f"Desconectado ({status_msg})")

        # Intentar reconexión automática si está activada
        if (
            self.auto_reconnect
            and self.reconnect_attempts < self.max_reconnect_attempts
        ):
            # Iniciar timer para reconexión (esperar 5 segundos)
            self.reconnect_timer.start(5000)

    def _try_reconnect(self) -> None:
        """Intenta reconectar automáticamente después de una desconexión"""
        self.reconnect_timer.stop()
        self.reconnect_attempts += 1

        self.output_ready.emit(
            f"Intento de reconexión {self.reconnect_attempts}/{self.max_reconnect_attempts}..."
        )

        if not self.reconnect():
            if self.reconnect_attempts < self.max_reconnect_attempts:
                # Aumentar el tiempo de espera en cada intento fallido (5s, 10s, 15s...)
                self.reconnect_timer.start(5000 * self.reconnect_attempts)
            else:
                self.output_ready.emit(
                    "Se alcanzó el número máximo de intentos de reconexión"
                )
                self.connection_status.emit(False, "Desconectado (max. intentos)")
