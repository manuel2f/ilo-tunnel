# ilo_tunnel/gui/widgets/connection_form.py
import os
from typing import List, Tuple

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ...models.profile import ConnectionProfile
from ...models.server_types import get_server_description, get_server_types
from .port_selector import PortSelectorWidget


class ConnectionFormWidget(QWidget):
    """Editor completo de un perfil de conexión.

    Único formulario reutilizable por la ventana principal (en línea) y por el
    diálogo de creación de perfiles. Organiza los campos en **Básico** y
    **Avanzado** (colapsable) e incorpora el selector de puertos, con etiquetas
    y tooltips claros.
    """

    changed = pyqtSignal()

    def __init__(
        self,
        include_name: bool = False,
        show_port_status: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self._include_name = include_name
        self._build_ui(show_port_status)

    def _build_ui(self, show_port_status: bool) -> None:
        root = QVBoxLayout(self)

        # --- Grupo Básico ---------------------------------------------------
        basic = QGroupBox("Básico")
        basic_form = QFormLayout(basic)

        if self._include_name:
            self.profile_name = QLineEdit()
            self.profile_name.textChanged.connect(self.changed)
            basic_form.addRow("Nombre del perfil:", self.profile_name)
        else:
            self.profile_name = None

        self.ilo_ip = QLineEdit()
        self.ilo_ip.setToolTip(
            "Dirección IP de la interfaz de gestión (iLO/iDRAC/iBMC) del servidor."
        )
        self.ilo_ip.textChanged.connect(self.changed)
        basic_form.addRow("IP de gestión (iLO):", self.ilo_ip)

        self.ssh_user = QLineEdit()
        self.ssh_user.setToolTip("Usuario para autenticarse en el gateway SSH.")
        self.ssh_user.textChanged.connect(self.changed)
        basic_form.addRow("Usuario SSH:", self.ssh_user)

        self.gateway_ip = QLineEdit()
        self.gateway_ip.setToolTip(
            "Host SSH intermedio (gateway) a través del cual se crea el túnel."
        )
        self.gateway_ip.textChanged.connect(self.changed)
        basic_form.addRow("IP de gateway:", self.gateway_ip)

        root.addWidget(basic)

        # --- Grupo Avanzado (colapsable) ------------------------------------
        self.advanced = QGroupBox("Avanzado")
        self.advanced.setCheckable(True)
        self.advanced.setChecked(False)
        adv_form = QFormLayout(self.advanced)

        self.ssh_port = QSpinBox()
        self.ssh_port.setRange(1, 65535)
        self.ssh_port.setValue(22)
        self.ssh_port.valueChanged.connect(self.changed)
        adv_form.addRow("Puerto SSH:", self.ssh_port)

        key_row = QHBoxLayout()
        self.key_path = QLineEdit("~/.ssh/id_rsa")
        self.key_path.setToolTip("Ruta a la clave privada SSH usada para autenticarse.")
        self.key_path.textChanged.connect(self.changed)
        key_row.addWidget(self.key_path, 1)
        browse = QPushButton("…")
        browse.setMaximumWidth(30)
        browse.clicked.connect(self._browse_key)
        key_row.addWidget(browse)
        key_widget = QWidget()
        key_widget.setLayout(key_row)
        adv_form.addRow("Clave SSH:", key_widget)

        self.local_ip = QComboBox()
        self.local_ip.setEditable(True)
        self.local_ip.addItem("127.0.0.1")
        self.local_ip.setToolTip(
            "Dirección local (bind) donde se exponen los puertos tunelizados.\n"
            "Normalmente 127.0.0.1 (solo accesible desde este equipo)."
        )
        self.local_ip.currentTextChanged.connect(self.changed)
        adv_form.addRow("IP de escucha local (bind):", self.local_ip)

        self.server_type = QComboBox()
        self.server_type.addItems(get_server_types())
        self.server_type.currentTextChanged.connect(self._on_server_type_changed)
        adv_form.addRow("Tipo de servidor:", self.server_type)

        self.server_type_desc = QLabel()
        self.server_type_desc.setWordWrap(True)
        adv_form.addRow("", self.server_type_desc)

        # Opciones SSH (por perfil)
        options = QWidget()
        opt_layout = QVBoxLayout(options)
        opt_layout.setContentsMargins(0, 0, 0, 0)
        self.use_sudo = QCheckBox("Usar sudo (necesario para puertos < 1024)")
        self.use_sudo.setChecked(True)
        self.compress = QCheckBox("Compresión SSH")
        self.verbose = QCheckBox("Modo detallado (verbose)")
        self.identity_only = QCheckBox("Usar solo la identidad especificada")
        self.identity_only.setChecked(True)
        self.strict_host_key = QCheckBox("Verificación estricta de clave de host")
        for cb in (
            self.use_sudo,
            self.compress,
            self.verbose,
            self.identity_only,
            self.strict_host_key,
        ):
            cb.toggled.connect(self.changed)
            opt_layout.addWidget(cb)
        adv_form.addRow("Opciones SSH:", options)

        self.connect_timeout = QSpinBox()
        self.connect_timeout.setRange(5, 120)
        self.connect_timeout.setValue(30)
        self.connect_timeout.setSuffix(" s")
        self.connect_timeout.valueChanged.connect(self.changed)
        adv_form.addRow("Timeout de conexión:", self.connect_timeout)

        root.addWidget(self.advanced)

        # --- Grupo Puertos --------------------------------------------------
        ports_group = QGroupBox("Puertos")
        ports_layout = QVBoxLayout(ports_group)
        self.port_selector = PortSelectorWidget(show_status=show_port_status)
        self.port_selector.portsChanged.connect(self.changed)
        ports_layout.addWidget(self.port_selector)
        root.addWidget(ports_group)

        self._update_description()

    # ------------------------------------------------------------- handlers
    def _browse_key(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar clave SSH",
            os.path.expanduser("~/.ssh"),
            "Claves SSH (id_rsa id_dsa *.pem *.key);;Todos los archivos (*)",
        )
        if path:
            self.key_path.setText(path)

    def _on_server_type_changed(self, server_type: str) -> None:
        self._update_description()
        self.port_selector.set_server_type(server_type)
        self.changed.emit()

    def _update_description(self) -> None:
        self.server_type_desc.setText(
            get_server_description(self.server_type.currentText())
        )

    # ----------------------------------------------------------------- API
    def refresh_server_types(self) -> None:
        """Repuebla el combo de tipos de servidor conservando la selección."""
        current = self.server_type.currentText()
        self.server_type.blockSignals(True)
        self.server_type.clear()
        self.server_type.addItems(get_server_types())
        if current in get_server_types():
            self.server_type.setCurrentText(current)
        self.server_type.blockSignals(False)
        self._update_description()

    def set_local_ip_options(self, ips: List[str]) -> None:
        """Rellena las IP locales sugeridas conservando el valor actual."""
        current = self.local_ip.currentText()
        self.local_ip.blockSignals(True)
        self.local_ip.clear()
        self.local_ip.addItems(ips or ["127.0.0.1"])
        self.local_ip.setCurrentText(current or "127.0.0.1")
        self.local_ip.blockSignals(False)

    def set_data(self, data: dict) -> None:
        """Carga el formulario desde un dict de perfil (to_dict)."""
        profile = ConnectionProfile.from_dict(data)
        if self.profile_name is not None:
            self.profile_name.setText(profile.name)
        self.ilo_ip.setText(profile.ilo_ip)
        self.ssh_user.setText(profile.ssh_user)
        self.gateway_ip.setText(profile.gateway_ip)
        self.ssh_port.setValue(profile.ssh_port)
        self.key_path.setText(profile.key_path)
        self.local_ip.setCurrentText(profile.local_ip)
        if profile.server_type in get_server_types():
            self.server_type.setCurrentText(profile.server_type)
        self.use_sudo.setChecked(profile.use_sudo)
        self.compress.setChecked(profile.compress)
        self.verbose.setChecked(profile.verbose)
        self.identity_only.setChecked(profile.identity_only)
        self.strict_host_key.setChecked(profile.strict_host_key)
        self.connect_timeout.setValue(profile.connect_timeout)
        self._update_description()
        self.port_selector.load(
            profile.server_type, profile.ports, profile.custom_ports
        )

    def get_data(self) -> dict:
        """Devuelve el contenido del formulario como dict de perfil."""
        data = {
            "name": self.profile_name.text() if self.profile_name is not None else "",
            "ilo_ip": self.ilo_ip.text(),
            "ssh_user": self.ssh_user.text(),
            "gateway_ip": self.gateway_ip.text(),
            "server_type": self.server_type.currentText(),
            "ssh_port": self.ssh_port.value(),
            "local_ip": self.local_ip.currentText(),
            "key_path": self.key_path.text(),
            "ports": self.port_selector.get_ports(),
            "custom_ports": True,  # el selector ya refleja la selección exacta
            "use_sudo": self.use_sudo.isChecked(),
            "compress": self.compress.isChecked(),
            "verbose": self.verbose.isChecked(),
            "identity_only": self.identity_only.isChecked(),
            "strict_host_key": self.strict_host_key.isChecked(),
            "connect_timeout": self.connect_timeout.value(),
        }
        return data

    def get_profile(self) -> ConnectionProfile:
        """Devuelve el perfil construido a partir del formulario."""
        return ConnectionProfile.from_dict(self.get_data())

    def validate(self) -> Tuple[bool, str]:
        """Valida los campos obligatorios. Returns (ok, mensaje_de_error)."""
        if self.profile_name is not None and not self.profile_name.text().strip():
            return False, "El nombre del perfil es obligatorio."
        if not self.ilo_ip.text().strip():
            return False, "La IP de gestión (iLO) es obligatoria."
        if not self.ssh_user.text().strip():
            return False, "El usuario SSH es obligatorio."
        if not self.gateway_ip.text().strip():
            return False, "La IP del gateway es obligatoria."
        if not self.port_selector.selected_ports():
            return False, "Debes seleccionar al menos un puerto para tunelizar."
        return True, ""
