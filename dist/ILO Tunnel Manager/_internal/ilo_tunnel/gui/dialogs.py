# ilo_tunnel/gui/dialogs.py
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QFormLayout,
    QCheckBox,
    QMessageBox,
    QGridLayout,
    QComboBox,
    QDialogButtonBox,
    QListWidget,
    QInputDialog,
    QWidget,
    QTabWidget,
    QFileDialog,
    QRadioButton,
    QButtonGroup,
    QGroupBox,
)
from PyQt6.QtCore import Qt

import os

from ..models.server_types import (
    get_server_types,
    get_server_ports,
    get_server_description,
)


class ConnectionProfileDialog(QDialog):
    """Diálogo para crear o editar perfiles de conexión"""

    def __init__(
        self, parent=None, profile_data=None, folders=None, current_folder="DEFAULT"
    ):
        super().__init__(parent)
        self.profile_data = profile_data or {}
        self.folders = folders or ["DEFAULT"]
        self.current_folder = current_folder

        self.setWindowTitle("Perfil de Conexión")
        self.setMinimumWidth(450)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        # Crear pestañas
        tabs = QTabWidget()

        # Pestaña de configuración básica
        basic_tab = QWidget()
        basic_layout = QFormLayout(basic_tab)

        # Carpeta
        self.folder_combo = QComboBox()
        self.folder_combo.addItems(self.folders)
        if self.current_folder in self.folders:
            self.folder_combo.setCurrentText(self.current_folder)
        basic_layout.addRow("Carpeta:", self.folder_combo)

        # Nombre del perfil
        self.profile_name = QLineEdit()
        self.profile_name.setText(self.profile_data.get("name", ""))
        basic_layout.addRow("Nombre del perfil:", self.profile_name)

        # Detalles de conexión
        self.ilo_ip = QLineEdit()
        self.ilo_ip.setText(self.profile_data.get("ilo_ip", ""))
        basic_layout.addRow("IP de ILO:", self.ilo_ip)

        # Selector de tipo de servidor
        server_type_layout = QHBoxLayout()
        self.server_type_combo = QComboBox()
        self.server_type_combo.addItems(get_server_types())
        self.server_type_combo.setCurrentText(
            self.profile_data.get("server_type", "HP/Huawei")
        )
        self.server_type_combo.currentTextChanged.connect(self.server_type_changed)
        server_type_layout.addWidget(self.server_type_combo)

        self.use_custom_ports = QCheckBox("Usar puertos personalizados")
        self.use_custom_ports.setChecked(self.profile_data.get("custom_ports", False))
        self.use_custom_ports.stateChanged.connect(self.toggle_custom_ports)
        server_type_layout.addWidget(self.use_custom_ports)

        basic_layout.addRow("Tipo de servidor:", server_type_layout)

        # Descripción del tipo de servidor
        self.server_type_desc = QLabel()
        self.server_type_desc.setWordWrap(True)
        self.update_server_description()
        basic_layout.addRow("", self.server_type_desc)

        self.ssh_user = QLineEdit()
        self.ssh_user.setText(self.profile_data.get("ssh_user", ""))
        basic_layout.addRow("Usuario SSH:", self.ssh_user)

        self.gateway_ip = QLineEdit()
        self.gateway_ip.setText(self.profile_data.get("gateway_ip", ""))
        basic_layout.addRow("IP de Gateway:", self.gateway_ip)

        self.ssh_port = QSpinBox()
        self.ssh_port.setRange(1, 65535)
        self.ssh_port.setValue(self.profile_data.get("ssh_port", 22))
        basic_layout.addRow("Puerto SSH:", self.ssh_port)

        self.local_ip = QLineEdit()
        self.local_ip.setText(self.profile_data.get("local_ip", "127.0.0.1"))
        basic_layout.addRow("IP Local:", self.local_ip)

        # Ruta de la clave SSH con botón de exploración
        key_path_layout = QHBoxLayout()
        self.key_path = QLineEdit()
        self.key_path.setText(self.profile_data.get("key_path", "~/.ssh/id_rsa"))
        key_path_layout.addWidget(
            self.key_path, 1
        )  # El 1 hace que tome el espacio disponible

        browse_key_btn = QPushButton("...")
        browse_key_btn.setMaximumWidth(30)
        browse_key_btn.clicked.connect(self.browse_key_file)
        key_path_layout.addWidget(browse_key_btn)

        # Añadir el layout como campo del formulario
        key_path_widget = QWidget()
        key_path_widget.setLayout(key_path_layout)
        basic_layout.addRow("Ruta de la clave SSH:", key_path_widget)

        # Añadir pestaña básica
        tabs.addTab(basic_tab, "Básico")

        # Pestaña de puertos
        ports_tab = QWidget()
        ports_layout = QVBoxLayout(ports_tab)

        # Puertos para tunelizar
        ports_grid = QGridLayout()
        ports_grid.setVerticalSpacing(2)  # Reducir espacio vertical
        ports_grid.setHorizontalSpacing(10)  # Mantener espacio horizontal razonable

        # Definir puertos comunes de ILO
        self.port_checkboxes = {}
        common_ports = {
            "SSH (22)": 22,
            "Telnet (23)": 23,
            "HTTP (80)": 80,
            "HTTPS (443)": 443,
            "RDP (3389)": 3389,
            "ILO (17988)": 17988,
            "ILO (9300)": 9300,
            "ILO (17990)": 17990,
            "ILO (3002)": 3002,
            "ILO (2198)": 2198,
        }

        saved_ports = self.profile_data.get("ports", {})

        row, col = 0, 0
        for name, port in common_ports.items():
            checkbox = QCheckBox(name)
            # Si hay datos de perfil, usar estado guardado, sino por defecto True
            is_checked = saved_ports.get(str(port), True)
            checkbox.setChecked(is_checked)
            checkbox.port = port
            self.port_checkboxes[port] = checkbox
            ports_grid.addWidget(checkbox, row, col)
            col += 1
            if col > 3:  # Aumentar a 4 columnas
                col = 0
                row += 1

            # Reducir la altura de los checkboxes
            checkbox.setMaximumHeight(20)

        ports_layout.addWidget(QLabel("Puertos a tunelizar:"))
        ports_layout.addLayout(ports_grid)

        # Opciones de selección rápida
        quick_select_layout = QHBoxLayout()

        select_all_btn = QPushButton("Seleccionar todos")
        select_all_btn.clicked.connect(self.select_all_ports)
        quick_select_layout.addWidget(select_all_btn)

        select_none_btn = QPushButton("Deseleccionar todos")
        select_none_btn.clicked.connect(self.select_no_ports)
        quick_select_layout.addWidget(select_none_btn)

        select_default_btn = QPushButton("Valores predeterminados")
        select_default_btn.clicked.connect(self.select_default_ports)
        quick_select_layout.addWidget(select_default_btn)

        ports_layout.addLayout(quick_select_layout)

        # Puertos personalizados
        custom_port_layout = QHBoxLayout()
        custom_port_layout.addWidget(QLabel("Puerto personalizado:"))

        self.custom_port = QSpinBox()
        self.custom_port.setRange(1, 65535)
        self.custom_port.setValue(8080)
        custom_port_layout.addWidget(self.custom_port)

        add_port_btn = QPushButton("Añadir")
        add_port_btn.clicked.connect(self.add_custom_port)
        custom_port_layout.addWidget(add_port_btn)

        ports_layout.addLayout(custom_port_layout)

        # Añadir pestaña de puertos
        tabs.addTab(ports_tab, "Puertos")

        # Añadir pestañas al layout principal
        layout.addWidget(tabs)

        # Inicializar el estado de los puertos según tipo de servidor
        self.toggle_custom_ports(self.use_custom_ports.isChecked())

        # Botones de diálogo
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def update_server_description(self):
        """Actualiza la descripción del tipo de servidor seleccionado"""
        server_type = self.server_type_combo.currentText()
        description = get_server_description(server_type)
        self.server_type_desc.setText(description)

    def server_type_changed(self, server_type):
        """Maneja el cambio del tipo de servidor"""
        self.update_server_description()

        # Si no se están usando puertos personalizados, actualizar según el tipo de servidor
        if not self.use_custom_ports.isChecked():
            self.update_ports_for_server_type(server_type)

    def update_ports_for_server_type(self, server_type):
        """Actualiza los puertos según el tipo de servidor seleccionado"""
        # Obtener los puertos para el tipo de servidor
        ports = get_server_ports(server_type)

        # Actualizar los checkboxes
        for port_checkbox in self.port_checkboxes.values():
            port = port_checkbox.port
            if port in ports:
                port_checkbox.setChecked(True)
                port_checkbox.setText(f"{ports[port]} ({port})")
            else:
                port_checkbox.setChecked(False)

    def toggle_custom_ports(self, state):
        """Activa o desactiva la configuración personalizada de puertos"""
        use_custom = state == Qt.CheckState.Checked

        # Actualizar puertos si cambiamos a modo automático
        if not use_custom:
            self.update_ports_for_server_type(self.server_type_combo.currentText())

        # Opcional: Deshabilitar/habilitar los checkboxes de puertos si queremos hacer que no sean modificables
        # en modo automático. Descomentando estas líneas se evitaría que el usuario pueda modificar los puertos
        # cuando está seleccionado un tipo de servidor específico.
        #
        # for checkbox in self.port_checkboxes.values():
        #     checkbox.setEnabled(use_custom)

    def browse_key_file(self):
        """Abre un diálogo para seleccionar el archivo de clave SSH"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar clave SSH",
            os.path.expanduser("~/.ssh"),
            "Archivos de clave SSH (id_rsa id_dsa *.pem *.key);;Todos los archivos (*)",
        )

        if file_path:
            self.key_path.setText(file_path)

    def select_all_ports(self):
        """Selecciona todos los puertos"""
        for checkbox in self.port_checkboxes.values():
            checkbox.setChecked(True)

    def select_no_ports(self):
        """Deselecciona todos los puertos"""
        for checkbox in self.port_checkboxes.values():
            checkbox.setChecked(False)

    def select_default_ports(self):
        """Selecciona los puertos predeterminados (HTTP, HTTPS, SSH)"""
        default_ports = [22, 80, 443]
        for port, checkbox in self.port_checkboxes.items():
            checkbox.setChecked(port in default_ports)

    def add_custom_port(self):
        """Añade un puerto personalizado a la lista"""
        port = self.custom_port.value()

        # Comprobar si ya existe
        if port in self.port_checkboxes:
            # Seleccionar el existente
            self.port_checkboxes[port].setChecked(True)
            QMessageBox.information(
                self,
                "Puerto ya existente",
                f"El puerto {port} ya está en la lista y ha sido seleccionado.",
            )
            return

        # Añadir nuevo puerto
        # TODO: Implementar adición de puertos personalizados
        QMessageBox.information(
            self,
            "Funcionalidad no implementada",
            "La adición de puertos personalizados es una característica planificada para futuras versiones.",
        )

    def get_profile_data(self):
        """Recoge todos los datos del perfil"""
        ports_data = {}
        for port, checkbox in self.port_checkboxes.items():
            ports_data[str(port)] = checkbox.isChecked()

        return {
            "name": self.profile_name.text(),
            "ilo_ip": self.ilo_ip.text(),
            "ssh_user": self.ssh_user.text(),
            "gateway_ip": self.gateway_ip.text(),
            "server_type": self.server_type_combo.currentText(),
            "ssh_port": self.ssh_port.value(),
            "local_ip": self.local_ip.text(),
            "key_path": self.key_path.text(),
            "ports": ports_data,
            "custom_ports": self.use_custom_ports.isChecked(),
        }

    def get_selected_folder(self):
        """Obtiene la carpeta seleccionada"""
        return self.folder_combo.currentText()

    def validate(self):
        """Valida los campos obligatorios del formulario"""
        if not self.profile_name.text():
            QMessageBox.warning(self, "Error", "El nombre del perfil es obligatorio.")
            return False

        if not self.ilo_ip.text():
            QMessageBox.warning(self, "Error", "La IP de ILO es obligatoria.")
            return False

        if not self.ssh_user.text():
            QMessageBox.warning(self, "Error", "El usuario SSH es obligatorio.")
            return False

        if not self.gateway_ip.text():
            QMessageBox.warning(self, "Error", "La IP del gateway es obligatoria.")
            return False

        # Verificar si hay al menos un puerto seleccionado cuando se usan puertos personalizados
        if self.use_custom_ports.isChecked():
            any_port_selected = any(
                checkbox.isChecked() for checkbox in self.port_checkboxes.values()
            )
            if not any_port_selected:
                QMessageBox.warning(
                    self, "Error", "Debe seleccionar al menos un puerto para tunelizar."
                )
                return False

        return True

    def accept(self):
        """Valida y acepta el diálogo"""
        if self.validate():
            super().accept()


class FolderManagementDialog(QDialog):
    """Diálogo para gestionar carpetas de perfiles"""

    def __init__(self, parent=None, profile_manager=None):
        super().__init__(parent)
        self.profile_manager = profile_manager

        self.setWindowTitle("Gestión de Carpetas")
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        # Lista de carpetas
        self.folder_list = QListWidget()
        self.folder_list.addItems(self.profile_manager.get_folders())
        layout.addWidget(QLabel("Carpetas:"))
        layout.addWidget(self.folder_list)

        # Botones de acción
        buttons_layout = QHBoxLayout()

        self.add_button = QPushButton("Añadir")
        self.add_button.clicked.connect(self.add_folder)
        buttons_layout.addWidget(self.add_button)

        self.rename_button = QPushButton("Renombrar")
        self.rename_button.clicked.connect(self.rename_folder)
        buttons_layout.addWidget(self.rename_button)

        self.delete_button = QPushButton("Eliminar")
        self.delete_button.clicked.connect(self.delete_folder)
        buttons_layout.addWidget(self.delete_button)

        layout.addLayout(buttons_layout)

        # Información sobre carpetas
        info_label = QLabel(
            "La carpeta 'DEFAULT' es la carpeta predeterminada y no puede eliminarse. "
            "Las carpetas permiten organizar tus perfiles de conexión."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Botones de diálogo
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def add_folder(self):
        """Añade una nueva carpeta"""
        folder_name, ok = QInputDialog.getText(
            self, "Nueva Carpeta", "Nombre de la carpeta:"
        )

        if ok and folder_name:
            if self.profile_manager.add_folder(folder_name):
                self.refresh_folder_list()
            else:
                QMessageBox.warning(
                    self, "Error", "Ya existe una carpeta con ese nombre."
                )

    def rename_folder(self):
        """Renombra la carpeta seleccionada"""
        current_row = self.folder_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Selecciona una carpeta para renombrar.")
            return

        old_name = self.folder_list.item(current_row).text()
        if old_name == "DEFAULT":
            QMessageBox.warning(
                self, "Error", "No se puede renombrar la carpeta por defecto."
            )
            return

        new_name, ok = QInputDialog.getText(
            self, "Renombrar Carpeta", "Nuevo nombre:", text=old_name
        )

        if ok and new_name:
            if self.profile_manager.rename_folder(old_name, new_name):
                self.refresh_folder_list()
            else:
                QMessageBox.warning(self, "Error", "No se pudo renombrar la carpeta.")

    def delete_folder(self):
        """Elimina la carpeta seleccionada"""
        current_row = self.folder_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Selecciona una carpeta para eliminar.")
            return

        folder_name = self.folder_list.item(current_row).text()
        if folder_name == "DEFAULT":
            QMessageBox.warning(
                self, "Error", "No se puede eliminar la carpeta por defecto."
            )
            return

        confirm = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Estás seguro de que deseas eliminar la carpeta '{folder_name}'?\n"
            "Todos los perfiles en esta carpeta se perderán.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if confirm == QMessageBox.StandardButton.Yes:
            if self.profile_manager.delete_folder(folder_name):
                self.refresh_folder_list()
            else:
                QMessageBox.warning(self, "Error", "No se pudo eliminar la carpeta.")

    def refresh_folder_list(self):
        """Actualiza la lista de carpetas"""
        self.folder_list.clear()
        self.folder_list.addItems(self.profile_manager.get_folders())
