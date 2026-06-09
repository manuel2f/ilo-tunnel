# ilo_tunnel/services/ssh_manager.py
import os
import socket
from typing import List, Optional, Tuple

from PyQt6.QtCore import QObject, QProcess, QTimer, pyqtSignal


def parse_port_mapping(mapping: str) -> Optional[Tuple[str, int, str, int]]:
    """Valida un mapeo ``local_ip:local_port:remote_host:remote_port``.

    Returns:
        La tupla (local_ip, local_port, remote_host, remote_port) si es válida,
        o ``None`` si el formato o los puertos no son correctos.
    """
    parts = mapping.split(":")
    if len(parts) != 4:
        return None
    local_ip, local_port, remote_host, remote_port = parts
    if not local_ip or not remote_host:
        return None
    try:
        lp, rp = int(local_port), int(remote_port)
    except ValueError:
        return None
    if not (1 <= lp <= 65535 and 1 <= rp <= 65535):
        return None
    return local_ip, lp, remote_host, rp


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
            "use_sudo": True,
            "strict_host_key": False,
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
        use_sudo: bool = True,
        strict_host_key: bool = False,
    ) -> bool:
        """
        Crea un túnel SSH con los parámetros especificados.

        Args:
            key_path: Ruta a la clave SSH
            ssh_port: Puerto SSH
            port_mappings: Lista de mapeos "local_ip:local_port:remote_host:remote_port"
            user: Nombre de usuario SSH
            gateway: Dirección del gateway
            verbose: Mostrar mensajes detallados de SSH
            compress: Usar compresión SSH
            identity_only: Usar solo la identidad especificada
            timeout: Tiempo de espera de conexión en segundos
            use_sudo: Anteponer ``sudo`` al comando (necesario para puertos < 1024)
            strict_host_key: Verificación estricta de clave de host

        Returns:
            True si se lanzó el proceso, False si la validación falló. El éxito
            real de la conexión se comunica de forma asíncrona por señales.
        """
        # Validar mapeos antes de construir el comando
        invalid = [m for m in port_mappings if parse_port_mapping(m) is None]
        if invalid:
            self.error_ready.emit("Mapeos de puertos no válidos: " + ", ".join(invalid))
            return False

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
            "use_sudo": use_sudo,
            "strict_host_key": strict_host_key,
        }

        # Generar comando SSH
        cmd = ["sudo", "ssh"] if use_sudo else ["ssh"]

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
            cmd.extend(["-o", "IdentitiesOnly=yes"])

        # Timeout y server-alive
        cmd.extend(["-o", f"ConnectTimeout={timeout}"])
        cmd.extend(["-o", "ServerAliveInterval=15"])
        cmd.extend(["-o", "ServerAliveCountMax=3"])

        # Verificación de clave de host
        if strict_host_key:
            cmd.extend(["-o", "StrictHostKeyChecking=yes"])
        else:
            cmd.extend(["-o", "StrictHostKeyChecking=no"])
            cmd.extend(["-o", "UserKnownHostsFile=/dev/null"])

        # Mapeos de puertos
        for mapping in port_mappings:
            cmd.extend(["-L", mapping])

        # Destino
        cmd.append(f"{user}@{gateway}")

        self.output_ready.emit(f"Iniciando túnel SSH: {' '.join(cmd)}")

        # Lanzar proceso de forma no bloqueante: el estado se notifica por señales
        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self._handle_stdout)
        self.process.readyReadStandardError.connect(self._handle_stderr)
        self.process.finished.connect(self._handle_finished)
        self.process.errorOccurred.connect(self._handle_error)

        self.connection_status.emit(False, "Conectando...")
        self.process.start(cmd[0], cmd[1:])
        return True

    def stop_tunnel(self) -> bool:
        """
        Detiene el túnel SSH en ejecución.

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
        Activa o desactiva la reconexión automática.

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
        Intenta reconectar con los últimos parámetros usados.

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
            self.last_config["use_sudo"],
            self.last_config["strict_host_key"],
        )

    def check_port_status(self, port_mappings: List[str]) -> None:
        """
        Comprueba el estado de los puertos mapeados localmente.

        Args:
            port_mappings: Lista de mapeos "local_ip:local_port:remote_host:remote_port"
        """
        for mapping in port_mappings:
            parsed = parse_port_mapping(mapping)
            if parsed is None:
                continue
            local_ip, local_port, _remote_host, _remote_port = parsed

            # Solo comprobar localhost o 127.0.0.1 por seguridad
            if local_ip in ("127.0.0.1", "localhost"):
                is_open = self._check_port_open(local_ip, local_port)
                self.status_changed.emit(f"{local_ip}:{local_port}", is_open)

    def _check_port_open(self, host: str, port: int) -> bool:
        """Comprueba si un puerto TCP local está aceptando conexiones."""
        try:
            with socket.create_connection((host, port), timeout=1.0):
                return True
        except OSError:
            return False

    def get_local_ip_addresses(self) -> List[str]:
        """
        Obtiene las direcciones IP locales del sistema.

        Returns:
            Lista de direcciones IP (siempre incluye 127.0.0.1)
        """
        ips = ["127.0.0.1"]  # Siempre incluir loopback

        # Método 1: socket UDP para descubrir la IP de salida
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                s.connect(("10.255.255.255", 1))
                ip = s.getsockname()[0]
                if ip not in ips:
                    ips.append(ip)
            except OSError:
                pass
            finally:
                s.close()
        except OSError:
            pass

        # Método 2: resolución del hostname
        try:
            hostname = socket.gethostname()
            for ip in socket.gethostbyname_ex(hostname)[2]:
                if ip not in ips and not ip.startswith("127."):
                    ips.append(ip)
        except OSError:
            pass

        return sorted(dict.fromkeys(ips))

    def is_connected(self) -> bool:
        """
        Comprueba si hay un túnel SSH activo.

        Returns:
            True si hay un túnel activo, False en caso contrario
        """
        return (
            self.process is not None
            and self.process.state() != QProcess.ProcessState.NotRunning
        )

    def _handle_stdout(self) -> None:
        """Procesa la salida estándar del proceso."""
        if self.process:
            data = self.process.readAllStandardOutput().data().decode(errors="replace")
            self.output_ready.emit(data)

            # Detectar patrón de conexión exitosa
            if "Authenticated to" in data:
                self.connection_status.emit(True, "Conectado")
                self.reconnect_attempts = 0  # Resetear contador de intentos

    def _handle_stderr(self) -> None:
        """Procesa la salida de error del proceso."""
        if self.process:
            data = self.process.readAllStandardError().data().decode(errors="replace")
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

    def _handle_error(self, error: QProcess.ProcessError) -> None:
        """Maneja fallos al lanzar el proceso SSH (binario ausente, permisos...)."""
        if error == QProcess.ProcessError.FailedToStart:
            self.error_ready.emit(
                "No se pudo iniciar 'ssh'. Comprueba que está instalado y los permisos."
            )
            self.connection_status.emit(False, "Error al iniciar")

    def _handle_finished(
        self, exit_code: int, exit_status: QProcess.ExitStatus
    ) -> None:
        """
        Maneja la finalización del proceso.

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
        """Intenta reconectar automáticamente después de una desconexión."""
        self.reconnect_timer.stop()
        self.reconnect_attempts += 1

        self.output_ready.emit(
            f"Intento de reconexión {self.reconnect_attempts}/{self.max_reconnect_attempts}..."
        )

        if not self.reconnect():
            if self.reconnect_attempts < self.max_reconnect_attempts:
                # Aumentar el tiempo de espera en cada intento (5s, 10s, 15s...)
                self.reconnect_timer.start(5000 * self.reconnect_attempts)
            else:
                self.output_ready.emit(
                    "Se alcanzó el número máximo de intentos de reconexión"
                )
                self.connection_status.emit(False, "Desconectado (max. intentos)")
