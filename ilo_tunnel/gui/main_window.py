def updateFolderCombos(self):
    """Actualiza ambos combos de carpetas"""
    folders = self.profile_manager.get_folders()

    # Guardar selección actual
    current_main = ""
    current_profiles = ""

    if hasattr(self, "folder_combo") and self.folder_combo is not None:
        current_main = self.folder_combo.currentText()

    if (
        hasattr(self, "profiles_folder_combo")
        and self.profiles_folder_combo is not None
    ):
        current_profiles = self.profiles_folder_combo.currentText()

    # Actualizar combos
    if hasattr(self, "folder_combo") and self.folder_combo is not None:
        self.folder_combo.clear()
        self.folder_combo.addItems(folders)

    if (
        hasattr(self, "profiles_folder_combo")
        and self.profiles_folder_combo is not None
    ):
        self.profiles_folder_combo.clear()
        self.profiles_folder_combo.addItems(folders)

    # Restaurar selección
    if current_main and hasattr(self, "folder_combo") and self.folder_combo is not None:
        if current_main in folders:
            self.folder_combo.setCurrentText(current_main)

    if (
        hasattr(self, "profiles_folder_combo")
        and self.profiles_folder_combo is not None
    ):
        if current_profiles and current_profiles in folders:
            self.profiles_folder_combo.setCurrentText(current_profiles)
        elif folders:
            self.profiles_folder_combo.setCurrentText(
                folders[0]
            )  # Seleccionar el primero por defectofrom .widgets import PortStatusWidget, ConnectionStatusBar# ilo_tunnel/gui/main_window.py


import sys
import os
import platform
import webbrowser
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QCheckBox,
    QMessageBox,
    QGridLayout,
    QFormLayout,
    QComboBox,
    QListWidget,
    QInputDialog,
    QSplitter,
    QGroupBox,
    QScrollArea,
    QMenu,
    QToolBar,
    QStatusBar,
    QFileDialog,
    QDialogButtonBox,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, QProcess, QSettings, QTimer, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QAction, QColor, QTextCursor, QFont

from ..models.profile import ConnectionProfile
from ..models.profile_manager import ProfileManager
from ..ssh_manager import SSHManager
from ..models.server_types import (
    get_server_types,
    get_server_ports,
    get_server_description,
    get_server_essential_ports,
)
from .widgets import PortStatusWidget


class ILOTunnelApp(QMainWindow):
    """Ventana principal de la aplicación ILO Tunnel Manager"""

    def __init__(self):
        super().__init__()

        # Estado de la aplicación
        self.settings = QSettings("ILOTunnel", "ILOTunnelApp")
        self.profile_manager = ProfileManager()
        self.current_folder = "DEFAULT"
        self.current_profile = None
        self.active_ports = {}  # Para seguimiento de puertos activos

        # Inicializar SSH manager primero para que esté disponible durante la inicialización de UI
        self.ssh_manager = SSHManager()

        # Inicializar variables de miembro importantes
        self.profiles_folder_combo = None
        self.ports_group = None
        self.port_checkboxes = {}
        self.port_status_widgets = {}
        self.server_type_combo = None
        self.use_custom_ports = None

        # Configurar UI
        self.initUI()

        # Conectar señales del SSHManager
        self.ssh_manager.output_ready.connect(self.onSshOutput)
        self.ssh_manager.error_ready.connect(self.onSshError)
        self.ssh_manager.process_finished.connect(self.onProcessFinished)
        self.ssh_manager.connection_status.connect(self.onConnectionStatusChanged)
        self.ssh_manager.status_changed.connect(self.updatePortStatus)

        # Puerto monitor timer
        self.port_monitor_timer = QTimer(self)
        self.port_monitor_timer.timeout.connect(self.checkPortStatus)

        # Cargar configuración
        self.loadSettings()

        # Mostrar mensaje de bienvenida
        self.console.append("ILO Tunnel Manager iniciado. Listo para conectar.")
        self.statusBar().showMessage("Listo", 5000)

    def initUI(self):
        """Inicializa la interfaz de usuario"""
        # Configuración básica
        self.setWindowTitle("ILO Tunnel Manager")
        self.setMinimumSize(800, 600)

        # Crear barra de herramientas
        self.createToolbar()

        # Crear barra de estado
        self.statusBar()

        # Crear widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal
        main_layout = QVBoxLayout(central_widget)

        # Crear tabs
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Crear todas las pestañas primero para que los componentes existan
        self.createConnectionTab()
        self.createProfilesTab()
        self.createHelpTab()
        self.createSettingsTab()

    def createToolbar(self):
        """Crea la barra de herramientas"""
        toolbar = self.addToolBar("Principal")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))

        # Acción conectar
        self.connect_action = QAction("Conectar", self)
        self.connect_action.triggered.connect(self.startTunnel)
        toolbar.addAction(self.connect_action)

        # Acción desconectar
        self.disconnect_action = QAction("Desconectar", self)
        self.disconnect_action.triggered.connect(self.stopTunnel)
        self.disconnect_action.setEnabled(False)
        toolbar.addAction(self.disconnect_action)

        toolbar.addSeparator()

        # Acción abrir navegador
        self.browser_action = QAction("Abrir Navegador", self)
        self.browser_action.triggered.connect(self.openBrowser)
        toolbar.addAction(self.browser_action)

        toolbar.addSeparator()

        # Acciones para perfiles
        self.new_profile_action = QAction("Nuevo Perfil", self)
        self.new_profile_action.triggered.connect(self.createProfile)
        toolbar.addAction(self.new_profile_action)

        self.save_profile_action = QAction("Guardar como Perfil", self)
        self.save_profile_action.triggered.connect(self.saveAsProfile)
        toolbar.addAction(self.save_profile_action)

    def createConnectionTab(self):
        """Crea la pestaña de conexión"""
        connection_tab = QWidget()
        connection_layout = QVBoxLayout(connection_tab)

        # Panel superior: selección de perfil y carpeta
        profile_panel = QWidget()
        profile_layout = QVBoxLayout(profile_panel)
        profile_layout.setContentsMargins(0, 0, 0, 0)

        # Selector de carpeta
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(QLabel("Carpeta:"))

        self.folder_combo = QComboBox()
        self.folder_combo.currentIndexChanged.connect(self.folderChanged)
        folder_layout.addWidget(self.folder_combo)

        self.manage_folders_btn = QPushButton("Gestionar")
        self.manage_folders_btn.clicked.connect(self.manageFolders)
        folder_layout.addWidget(self.manage_folders_btn)

        profile_layout.addLayout(folder_layout)

        # Selector de perfil
        profile_selector_layout = QHBoxLayout()
        profile_selector_layout.addWidget(QLabel("Perfil:"))

        self.profile_combo = QComboBox()
        self.profile_combo.setMinimumWidth(200)
        self.profile_combo.currentIndexChanged.connect(self.loadProfile)
        profile_selector_layout.addWidget(self.profile_combo)

        self.new_profile_btn = QPushButton("Nuevo")
        self.new_profile_btn.clicked.connect(self.createProfile)
        profile_selector_layout.addWidget(self.new_profile_btn)

        self.edit_profile_btn = QPushButton("Editar")
        self.edit_profile_btn.clicked.connect(self.editProfile)
        profile_selector_layout.addWidget(self.edit_profile_btn)

        self.delete_profile_btn = QPushButton("Eliminar")
        self.delete_profile_btn.clicked.connect(self.deleteProfile)
        profile_selector_layout.addWidget(self.delete_profile_btn)

        profile_layout.addLayout(profile_selector_layout)
        connection_layout.addWidget(profile_panel)

        # Splitter para dividir la configuración y la consola
        splitter = QSplitter(Qt.Orientation.Vertical)
        connection_layout.addWidget(splitter, 1)

        # Panel de configuración
        config_panel = QWidget()
        config_layout = QVBoxLayout(config_panel)

        # Grupo de configuración de conexión
        connection_group = QGroupBox("Configuración de Conexión")
        connection_form = QFormLayout(connection_group)

        self.ilo_ip = QLineEdit()
        connection_form.addRow("IP de ILO:", self.ilo_ip)

        # Selector de tipo de servidor
        server_type_layout = QHBoxLayout()
        self.server_type_combo = QComboBox()
        self.server_type_combo.addItems(get_server_types())
        self.server_type_combo.setCurrentIndex(0)  # HP/Huawei por defecto
        self.server_type_combo.currentTextChanged.connect(self.serverTypeChanged)
        server_type_layout.addWidget(self.server_type_combo)

        self.use_custom_ports = QCheckBox("Usar puertos personalizados")
        self.use_custom_ports.setChecked(False)
        self.use_custom_ports.stateChanged.connect(self.toggleCustomPorts)
        server_type_layout.addWidget(self.use_custom_ports)

        connection_form.addRow("Tipo de servidor:", server_type_layout)

        # Descripción del tipo de servidor
        self.server_type_desc = QLabel()
        self.server_type_desc.setWordWrap(True)
        self.updateServerDescription()
        connection_form.addRow("", self.server_type_desc)

        self.ssh_user = QLineEdit()
        connection_form.addRow("Usuario SSH:", self.ssh_user)

        self.gateway_ip = QLineEdit()
        connection_form.addRow("IP de Gateway:", self.gateway_ip)

        self.ssh_port = QSpinBox()
        self.ssh_port.setRange(1, 65535)
        self.ssh_port.setValue(22)
        connection_form.addRow("Puerto SSH:", self.ssh_port)

        self.local_ip = QComboBox()
        self.local_ip.setEditable(True)
        self.local_ip.addItem("127.0.0.1")
        self.updateLocalIPs()  # Añadir IPs locales
        connection_form.addRow("IP Local:", self.local_ip)

        # Campo de clave SSH con layout horizontal para el botón de exploración
        key_path_layout = QHBoxLayout()
        self.key_path = QLineEdit()
        self.key_path.setText(os.path.expanduser("~/.ssh/id_rsa"))
        key_path_layout.addWidget(
            self.key_path, 1
        )  # El 1 hace que tome el espacio disponible

        browse_key_btn = QPushButton("...")
        browse_key_btn.setMaximumWidth(30)
        browse_key_btn.clicked.connect(self.browseKeyFile)
        key_path_layout.addWidget(browse_key_btn)

        # Añadir el layout como campo del formulario
        key_path_widget = QWidget()
        key_path_widget.setLayout(key_path_layout)
        connection_form.addRow("Clave SSH:", key_path_widget)

        # Opciones adicionales
        options_layout = QHBoxLayout()

        self.compress_checkbox = QCheckBox("Usar compresión")
        options_layout.addWidget(self.compress_checkbox)

        self.verbose_checkbox = QCheckBox("Modo verbose")
        options_layout.addWidget(self.verbose_checkbox)

        self.auto_reconnect_checkbox = QCheckBox("Reconexión automática")
        self.auto_reconnect_checkbox.setChecked(True)
        self.auto_reconnect_checkbox.stateChanged.connect(self.toggleAutoReconnect)
        options_layout.addWidget(self.auto_reconnect_checkbox)

        connection_form.addRow("Opciones:", options_layout)

        config_layout.addWidget(connection_group)

        # Grupo de puertos con tamaño reducido
        self.ports_group = QGroupBox("Puertos a Tunelizar (Personalizados)")
        ports_layout = QGridLayout(self.ports_group)
        ports_layout.setVerticalSpacing(2)  # Reducir espacio vertical entre elementos
        ports_layout.setHorizontalSpacing(10)  # Añadir algo de espacio horizontal

        # Definir puertos comunes de ILO
        self.port_checkboxes = {}
        self.port_status_widgets = {}
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

        row, col = 0, 0
        for name, port in common_ports.items():
            port_layout = QHBoxLayout()
            port_layout.setSpacing(2)  # Reducir espacio entre checkbox e indicador
            port_layout.setContentsMargins(0, 0, 0, 0)  # Eliminar márgenes

            # Checkbox para seleccionar puerto
            checkbox = QCheckBox(name)
            checkbox.setChecked(True)
            checkbox.port = port
            self.port_checkboxes[port] = checkbox
            port_layout.addWidget(checkbox)

            # Indicador de estado
            status_widget = PortStatusWidget()
            self.port_status_widgets[port] = status_widget
            port_layout.addWidget(status_widget)

            port_widget = QWidget()
            port_widget.setLayout(port_layout)
            port_widget.setMaximumHeight(22)  # Limitar altura

            ports_layout.addWidget(port_widget, row, col)
            col += 1
            if col > 3:  # Aumentar a 4 columnas en lugar de 3
                col = 0
                row += 1

        # Establecer una altura máxima para el grupo de puertos
        self.ports_group.setMaximumHeight(150)
        config_layout.addWidget(self.ports_group)

        # Inicializar el estado de los puertos según tipo de servidor
        self.updatePortsForServerType(self.server_type_combo.currentText())
        # No llamamos a toggleCustomPorts aquí para evitar problemas
        self.ports_group.setVisible(self.use_custom_ports.isChecked())

        # Botones de acción
        actions_layout = QHBoxLayout()

        self.connect_btn = QPushButton("Conectar")
        self.connect_btn.clicked.connect(self.startTunnel)
        actions_layout.addWidget(self.connect_btn)

        self.disconnect_btn = QPushButton("Desconectar")
        self.disconnect_btn.clicked.connect(self.stopTunnel)
        self.disconnect_btn.setEnabled(False)
        actions_layout.addWidget(self.disconnect_btn)

        self.open_browser_btn = QPushButton("Abrir en Navegador")
        self.open_browser_btn.clicked.connect(self.openBrowser)
        actions_layout.addWidget(self.open_browser_btn)

        self.save_as_profile_btn = QPushButton("Guardar como Perfil")
        self.save_as_profile_btn.clicked.connect(self.saveAsProfile)
        actions_layout.addWidget(self.save_as_profile_btn)

        config_layout.addLayout(actions_layout)

        # Panel de configuración al splitter
        splitter.addWidget(config_panel)

        # Panel de consola
        console_group = QGroupBox("Consola")
        console_layout = QVBoxLayout(console_group)

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        # Usar una fuente monoespaciada del sistema sin especificar nombre
        font = QFont()
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setFixedPitch(True)
        font.setPointSize(9)
        self.console.setFont(font)
        console_layout.addWidget(self.console)

        # Botones de consola
        console_buttons = QHBoxLayout()

        clear_console_btn = QPushButton("Limpiar")
        clear_console_btn.clicked.connect(self.console.clear)
        console_buttons.addWidget(clear_console_btn)

        copy_console_btn = QPushButton("Copiar")
        copy_console_btn.clicked.connect(self.copyConsoleText)
        console_buttons.addWidget(copy_console_btn)

        save_console_btn = QPushButton("Guardar")
        save_console_btn.clicked.connect(self.saveConsoleText)
        console_buttons.addWidget(save_console_btn)

        console_layout.addLayout(console_buttons)

        # Panel de consola al splitter
        splitter.addWidget(console_group)

        # Añadir pestaña de conexión
        self.tabs.addTab(connection_tab, "Conexión")

    def createProfilesTab(self):
        """Crea la pestaña de gestión de perfiles"""
        profiles_tab = QWidget()
        profiles_layout = QVBoxLayout(profiles_tab)

        # Selector de carpeta
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(QLabel("Carpeta:"))

        # Asegurarnos de que ya esté inicializado
        if self.profiles_folder_combo is None:
            self.profiles_folder_combo = QComboBox()

        self.profiles_folder_combo.currentIndexChanged.connect(
            self.profilesFolderChanged
        )
        folder_layout.addWidget(self.profiles_folder_combo)

        create_folder_btn = QPushButton("Nueva carpeta")
        create_folder_btn.clicked.connect(self.createFolder)
        folder_layout.addWidget(create_folder_btn)

        manage_folders_btn = QPushButton("Gestionar carpetas")
        manage_folders_btn.clicked.connect(self.manageFolders)
        folder_layout.addWidget(manage_folders_btn)

        profiles_layout.addLayout(folder_layout)

        # Lista de perfiles
        profiles_layout.addWidget(QLabel("Perfiles guardados:"))

        self.profiles_list = QListWidget()
        self.profiles_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.profiles_list.itemDoubleClicked.connect(self.loadProfileFromList)
        profiles_layout.addWidget(self.profiles_list)

        # Botones de acción para perfiles
        profiles_actions = QHBoxLayout()

        load_profile_btn = QPushButton("Cargar")
        load_profile_btn.clicked.connect(self.loadSelectedProfile)
        profiles_actions.addWidget(load_profile_btn)

        edit_profile_btn = QPushButton("Editar")
        edit_profile_btn.clicked.connect(self.editProfileFromList)
        profiles_actions.addWidget(edit_profile_btn)

        clone_profile_btn = QPushButton("Clonar")
        clone_profile_btn.clicked.connect(self.cloneProfileFromList)
        profiles_actions.addWidget(clone_profile_btn)

        delete_profile_btn = QPushButton("Eliminar")
        delete_profile_btn.clicked.connect(self.deleteProfileFromList)
        profiles_actions.addWidget(delete_profile_btn)

        profiles_layout.addLayout(profiles_actions)

        # Importación/exportación
        import_export_layout = QHBoxLayout()

        import_btn = QPushButton("Importar perfiles")
        import_btn.clicked.connect(self.importProfiles)
        import_export_layout.addWidget(import_btn)

        export_btn = QPushButton("Exportar perfiles")
        export_btn.clicked.connect(self.exportProfiles)
        import_export_layout.addWidget(export_btn)

        profiles_layout.addLayout(import_export_layout)

        # Añadir pestaña de perfiles
        self.tabs.addTab(profiles_tab, "Perfiles")

    def createHelpTab(self):
        """Crea la pestaña de ayuda"""
        help_tab = QWidget()
        help_layout = QVBoxLayout(help_tab)

        # Crear widget de texto para la ayuda
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setHtml(
            """
        <h2>HP ProLiant ILO Tunnel Manager</h2>
        <p>Esta aplicación permite crear túneles SSH para acceder a interfaces ILO de servidores HP ProLiant.</p>
        
        <h3>Instrucciones:</h3>
        <ol>
            <li>Selecciona una carpeta y un perfil existente o crea uno nuevo.</li>
            <li>Introduce la dirección IP de la interfaz ILO a la que quieres conectarte.</li>
            <li>Introduce el usuario SSH para acceder al gateway.</li>
            <li>Introduce la dirección IP del gateway SSH.</li>
            <li>Ajusta el puerto SSH si es necesario (por defecto es 22).</li>
            <li>La IP local por defecto es 127.0.0.1, pero puedes cambiarla si lo necesitas.</li>
            <li>Indica la ruta a tu clave SSH privada.</li>
            <li>Haz clic en "Conectar" para establecer el túnel.</li>
            <li>Utiliza "Abrir en Navegador" para acceder a la interfaz web ILO.</li>
        </ol>
        
        <h3>Gestión de Perfiles:</h3>
        <ul>
            <li><b>Nuevo:</b> Crea un nuevo perfil de conexión.</li>
            <li><b>Editar:</b> Modifica el perfil seleccionado.</li>
            <li><b>Eliminar:</b> Borra el perfil seleccionado.</li>
            <li><b>Guardar como Perfil:</b> Guarda la configuración actual como un nuevo perfil.</li>
        </ul>
        
        <h3>Gestión de Carpetas:</h3>
        <ul>
            <li>Usa el botón "Gestionar" junto al selector de carpetas para crear, renombrar o eliminar carpetas.</li>
            <li>Organiza tus perfiles en diferentes carpetas para una mejor gestión.</li>
        </ul>
        
        <h3>Opciones avanzadas:</h3>
        <ul>
            <li><b>Modo verbose:</b> Muestra información detallada sobre la conexión SSH.</li>
            <li><b>Compresión:</b> Usa compresión SSH para reducir el ancho de banda.</li>
            <li><b>Reconexión automática:</b> Intenta reconectar automáticamente si se pierde la conexión.</li>
        </ul>
        
        <p><b>Nota:</b> Esta aplicación requiere permisos de administrador para crear los túneles.</p>
        """
        )

        help_layout.addWidget(help_text)

        # Añadir pestaña de ayuda
        self.tabs.addTab(help_tab, "Ayuda")

    def createSettingsTab(self):
        """Crea la pestaña de configuración global"""
        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)

        # Grupo de opciones generales
        general_group = QGroupBox("Opciones generales")
        general_layout = QFormLayout(general_group)

        # Opciones de aplicación
        self.auto_start_checkbox = QCheckBox(
            "Iniciar automáticamente con el último perfil"
        )
        general_layout.addRow("", self.auto_start_checkbox)

        self.minimize_to_tray_checkbox = QCheckBox(
            "Minimizar a bandeja del sistema al cerrar"
        )
        general_layout.addRow("", self.minimize_to_tray_checkbox)

        self.show_notifications_checkbox = QCheckBox("Mostrar notificaciones")
        self.show_notifications_checkbox.setChecked(True)
        general_layout.addRow("", self.show_notifications_checkbox)

        self.confirm_exit_checkbox = QCheckBox("Confirmar al salir")
        self.confirm_exit_checkbox.setChecked(True)
        general_layout.addRow("", self.confirm_exit_checkbox)

        settings_layout.addWidget(general_group)

        # Grupo de opciones de SSH
        ssh_group = QGroupBox("Opciones de SSH")
        ssh_layout = QFormLayout(ssh_group)

        self.ssh_timeout_spinbox = QSpinBox()
        self.ssh_timeout_spinbox.setRange(5, 120)
        self.ssh_timeout_spinbox.setValue(30)
        self.ssh_timeout_spinbox.setSuffix(" segundos")
        ssh_layout.addRow("Tiempo de espera de conexión:", self.ssh_timeout_spinbox)

        self.reconnect_attempts_spinbox = QSpinBox()
        self.reconnect_attempts_spinbox.setRange(1, 10)
        self.reconnect_attempts_spinbox.setValue(3)
        self.reconnect_attempts_spinbox.setSuffix(" intentos")
        ssh_layout.addRow("Intentos de reconexión:", self.reconnect_attempts_spinbox)

        self.identity_only_checkbox = QCheckBox("Usar solo la identidad especificada")
        self.identity_only_checkbox.setChecked(True)
        ssh_layout.addRow("", self.identity_only_checkbox)

        self.strict_host_key_checkbox = QCheckBox(
            "Verificación estricta de clave de host"
        )
        self.strict_host_key_checkbox.setChecked(False)
        ssh_layout.addRow("", self.strict_host_key_checkbox)

        settings_layout.addWidget(ssh_group)

        # Grupo de opciones de UI
        ui_group = QGroupBox("Interfaz de Usuario")
        ui_layout = QFormLayout(ui_group)

        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setRange(8, 16)
        self.font_size_spinbox.setValue(9)
        self.font_size_spinbox.valueChanged.connect(self.updateConsoleFont)
        ui_layout.addRow("Tamaño de fuente de consola:", self.font_size_spinbox)

        self.auto_scroll_checkbox = QCheckBox("Auto-scroll de consola")
        self.auto_scroll_checkbox.setChecked(True)
        ui_layout.addRow("", self.auto_scroll_checkbox)

        settings_layout.addWidget(ui_group)

        # Botones de acción
        buttons_layout = QHBoxLayout()

        save_settings_btn = QPushButton("Guardar configuración")
        save_settings_btn.clicked.connect(self.saveGlobalSettings)
        buttons_layout.addWidget(save_settings_btn)

        reset_settings_btn = QPushButton("Restaurar valores predeterminados")
        reset_settings_btn.clicked.connect(self.resetGlobalSettings)
        buttons_layout.addWidget(reset_settings_btn)

        settings_layout.addLayout(buttons_layout)

        # Espaciador para evitar que los widgets se estiren
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        settings_layout.addWidget(spacer)

        # Añadir pestaña de configuración
        self.tabs.addTab(settings_tab, "Configuración")

    def loadSettings(self):
        """Carga la configuración guardada"""
        # Actualizar lista de carpetas
        if hasattr(self, "updateFolderCombos"):
            self.updateFolderCombos()

        # Cargar última carpeta usada
        last_folder = self.settings.value("last_folder", "DEFAULT")
        if self.folder_combo is not None and last_folder in [
            self.folder_combo.itemText(i) for i in range(self.folder_combo.count())
        ]:
            self.folder_combo.setCurrentText(last_folder)
            self.current_folder = last_folder

        # Actualizar la lista de perfiles en la pestaña de perfiles
        if hasattr(self, "updateProfilesListWidget"):
            self.updateProfilesListWidget(self.current_folder)

        # Cargar último perfil usado
        if hasattr(self, "updateProfilesList"):
            self.updateProfilesList()

        last_profile_index = int(self.settings.value("last_profile_index", -1))

        if (
            self.profile_combo is not None
            and last_profile_index >= 0
            and last_profile_index < self.profile_combo.count()
        ):
            self.profile_combo.setCurrentIndex(last_profile_index)
        else:
            # Cargar configuración individual si no hay perfil seleccionado
            self.ilo_ip.setText(self.settings.value("ilo_ip", ""))
            self.ssh_user.setText(self.settings.value("ssh_user", ""))
            self.gateway_ip.setText(self.settings.value("gateway_ip", ""))
            self.ssh_port.setValue(int(self.settings.value("ssh_port", 22)))
            if self.local_ip is not None:
                self.local_ip.setCurrentText(
                    self.settings.value("local_ip", "127.0.0.1")
                )
            self.key_path.setText(
                self.settings.value("key_path", os.path.expanduser("~/.ssh/id_rsa"))
            )

            # Cargar tipo de servidor
            server_type = self.settings.value("server_type", "HP/Huawei")
            if self.server_type_combo is not None and server_type in get_server_types():
                self.server_type_combo.setCurrentText(server_type)

            # Cargar configuración de puertos personalizados
            if self.use_custom_ports is not None:
                use_custom = self.settings.value("custom_ports", False, type=bool)
                self.use_custom_ports.setChecked(use_custom)

            # Cargar estado de puertos
            saved_ports = self.settings.value("ports", {})
            if saved_ports:
                for port, checkbox in self.port_checkboxes.items():
                    checkbox.setChecked(saved_ports.get(str(port), True))

        # Cargar configuración global
        if hasattr(self, "loadGlobalSettings"):
            self.loadGlobalSettings()

        # Activar reconexión automática según configuración
        if (
            hasattr(self, "auto_reconnect_checkbox")
            and self.auto_reconnect_checkbox is not None
        ):
            if (
                hasattr(self, "reconnect_attempts_spinbox")
                and self.reconnect_attempts_spinbox is not None
            ):
                self.ssh_manager.set_auto_reconnect(
                    self.auto_reconnect_checkbox.isChecked(),
                    self.reconnect_attempts_spinbox.value(),
                )

    def loadGlobalSettings(self):
        """Carga la configuración global de la aplicación"""
        # Opciones generales
        self.auto_start_checkbox.setChecked(
            self.settings.value("auto_start", False, type=bool)
        )
        self.minimize_to_tray_checkbox.setChecked(
            self.settings.value("minimize_to_tray", False, type=bool)
        )
        self.show_notifications_checkbox.setChecked(
            self.settings.value("show_notifications", True, type=bool)
        )
        self.confirm_exit_checkbox.setChecked(
            self.settings.value("confirm_exit", True, type=bool)
        )

        # Opciones SSH
        self.ssh_timeout_spinbox.setValue(
            self.settings.value("ssh_timeout", 30, type=int)
        )
        self.reconnect_attempts_spinbox.setValue(
            self.settings.value("reconnect_attempts", 3, type=int)
        )
        self.identity_only_checkbox.setChecked(
            self.settings.value("identity_only", True, type=bool)
        )
        self.strict_host_key_checkbox.setChecked(
            self.settings.value("strict_host_key", False, type=bool)
        )

        # Opciones UI
        font_size = self.settings.value("console_font_size", 9, type=int)
        self.font_size_spinbox.setValue(font_size)
        self.updateConsoleFont(font_size)
        self.auto_scroll_checkbox.setChecked(
            self.settings.value("auto_scroll", True, type=bool)
        )

    def saveGlobalSettings(self):
        """Guarda la configuración global de la aplicación"""
        # Opciones generales
        self.settings.setValue("auto_start", self.auto_start_checkbox.isChecked())
        self.settings.setValue(
            "minimize_to_tray", self.minimize_to_tray_checkbox.isChecked()
        )
        self.settings.setValue(
            "show_notifications", self.show_notifications_checkbox.isChecked()
        )
        self.settings.setValue("confirm_exit", self.confirm_exit_checkbox.isChecked())

        # Opciones SSH
        self.settings.setValue("ssh_timeout", self.ssh_timeout_spinbox.value())
        self.settings.setValue(
            "reconnect_attempts", self.reconnect_attempts_spinbox.value()
        )
        self.settings.setValue("identity_only", self.identity_only_checkbox.isChecked())
        self.settings.setValue(
            "strict_host_key", self.strict_host_key_checkbox.isChecked()
        )

        # Opciones UI
        self.settings.setValue("console_font_size", self.font_size_spinbox.value())
        self.settings.setValue("auto_scroll", self.auto_scroll_checkbox.isChecked())

        # Actualizar reconexión automática
        self.ssh_manager.set_auto_reconnect(
            self.auto_reconnect_checkbox.isChecked(),
            self.reconnect_attempts_spinbox.value(),
        )

        QMessageBox.information(
            self,
            "Configuración guardada",
            "La configuración global se ha guardado correctamente.",
        )

    def resetGlobalSettings(self):
        """Restaura los valores predeterminados de la configuración global"""
        confirm = QMessageBox.question(
            self,
            "Confirmar restauración",
            "¿Estás seguro de que deseas restaurar todos los valores predeterminados?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if confirm == QMessageBox.StandardButton.Yes:
            # Valores predeterminados
            self.auto_start_checkbox.setChecked(False)
            self.minimize_to_tray_checkbox.setChecked(False)
            self.show_notifications_checkbox.setChecked(True)
            self.confirm_exit_checkbox.setChecked(True)
            self.ssh_timeout_spinbox.setValue(30)
            self.reconnect_attempts_spinbox.setValue(3)
            self.identity_only_checkbox.setChecked(True)
            self.strict_host_key_checkbox.setChecked(False)
            self.font_size_spinbox.setValue(9)
            self.updateConsoleFont(9)
            self.auto_scroll_checkbox.setChecked(True)

            # Guardar configuración
            self.saveGlobalSettings()

    def updateConsoleFont(self, size):
        """Actualiza el tamaño de fuente de la consola"""
        font = QFont()
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setFixedPitch(True)
        font.setPointSize(size)
        self.console.setFont(font)

    def updateServerDescription(self):
        """Actualiza la descripción del tipo de servidor seleccionado"""
        server_type = self.server_type_combo.currentText()
        description = get_server_description(server_type)
        self.server_type_desc.setText(description)

    def serverTypeChanged(self, server_type):
        """Maneja el cambio del tipo de servidor"""
        self.updateServerDescription()

        # Si no se están usando puertos personalizados, actualizar según el tipo de servidor
        if not self.use_custom_ports.isChecked():
            self.updatePortsForServerType(server_type)

    def updatePortsForServerType(self, server_type):
        """Actualiza los puertos según el tipo de servidor seleccionado"""
        # Obtener los puertos para el tipo de servidor
        ports = get_server_ports(server_type)

        # Actualizar los checkboxes
        for port, checkbox in self.port_checkboxes.items():
            if port in ports:
                checkbox.setChecked(True)
                checkbox.setText(f"{ports[port]} ({port})")
            else:
                checkbox.setChecked(False)

    def toggleCustomPorts(self, state):
        """Activa o desactiva la configuración personalizada de puertos"""
        use_custom = state == Qt.CheckState.Checked

        # Mostrar u ocultar el grupo de puertos personalizados
        if hasattr(self, "ports_group") and self.ports_group is not None:
            self.ports_group.setVisible(use_custom)

        # Actualizar puertos si cambiamos a modo automático
        if not use_custom:
            if (
                hasattr(self, "server_type_combo")
                and self.server_type_combo is not None
            ):
                self.updatePortsForServerType(self.server_type_combo.currentText())

        # Actualizar habilitación de la sección de puertos
        for port, checkbox in self.port_checkboxes.items():
            checkbox.setEnabled(use_custom)
        """Actualiza ambos combos de carpetas"""
        folders = self.profile_manager.get_folders()

        # Guardar selección actual
        current_main = self.folder_combo.currentText()
        current_profiles = self.profiles_folder_combo.currentText()

        # Actualizar combos
        self.folder_combo.clear()
        self.folder_combo.addItems(folders)
        self.profiles_folder_combo.clear()
        self.profiles_folder_combo.addItems(folders)

        # Restaurar selección
        if current_main in folders:
            self.folder_combo.setCurrentText(current_main)

        if current_profiles in folders:
            self.profiles_folder_combo.setCurrentText(current_profiles)
        else:
            self.profiles_folder_combo.setCurrentText(
                folders[0]
            )  # Seleccionar el primero por defecto

    def updateLocalIPs(self):
        """Actualiza la lista de IPs locales"""
        current_ip = self.local_ip.currentText()

        self.local_ip.clear()
        self.local_ip.addItem("127.0.0.1")

        # Añadir IPs locales usando SSHManager
        for ip in self.ssh_manager.get_local_ip_addresses():
            if ip != "127.0.0.1":  # Ya añadido
                self.local_ip.addItem(ip)

        # Restaurar IP seleccionada
        if current_ip:
            index = self.local_ip.findText(current_ip)
            if index >= 0:
                self.local_ip.setCurrentIndex(index)

    def folderChanged(self, index):
        """Maneja el cambio de carpeta en el combo principal"""
        if index >= 0:
            self.current_folder = self.folder_combo.itemText(index)
            self.settings.setValue("last_folder", self.current_folder)
            self.updateProfilesList()

    def profilesFolderChanged(self, index):
        """Maneja el cambio de carpeta en el combo de la pestaña de perfiles"""
        if index >= 0:
            folder = self.profiles_folder_combo.itemText(index)
            self.updateProfilesListWidget(folder)

    def updateProfilesList(self):
        """Actualiza el combo de perfiles con los de la carpeta actual"""
        if not hasattr(self, "profile_combo") or self.profile_combo is None:
            return

        self.profile_combo.clear()
        self.profile_combo.addItem("-- Seleccionar Perfil --")

        profiles = self.profile_manager.get_profiles(self.current_folder)
        for profile in profiles:
            self.profile_combo.addItem(profile["name"])

    def updateProfilesListWidget(self, folder=None):
        """Actualiza el widget de lista de perfiles"""
        if not hasattr(self, "profiles_list") or self.profiles_list is None:
            return

        if (
            not hasattr(self, "profiles_folder_combo")
            or self.profiles_folder_combo is None
        ):
            return

        if folder is None:
            folder = self.profiles_folder_combo.currentText()
            if not folder:
                return

        self.profiles_list.clear()
        profiles = self.profile_manager.get_profiles(folder)
        for profile in profiles:
            self.profiles_list.addItem(profile["name"])

    def loadProfile(self, index):
        """Carga un perfil seleccionado en el combo principal"""
        if index <= 0:  # Skip the "Select Profile" item
            return

        profiles = self.profile_manager.get_profiles(self.current_folder)
        profile_index = index - 1  # Adjust for the "Select Profile" item

        if profile_index < len(profiles):
            profile_data = profiles[profile_index]
            self.current_profile = ConnectionProfile.from_dict(profile_data)

            # Cargar datos del perfil en la interfaz
            self.ilo_ip.setText(self.current_profile.ilo_ip)
            self.ssh_user.setText(self.current_profile.ssh_user)
            self.gateway_ip.setText(self.current_profile.gateway_ip)
            self.ssh_port.setValue(self.current_profile.ssh_port)
            self.local_ip.setCurrentText(self.current_profile.local_ip)
            self.key_path.setText(self.current_profile.key_path)

            # Configurar tipo de servidor
            self.server_type_combo.setCurrentText(self.current_profile.server_type)
            self.use_custom_ports.setChecked(self.current_profile.custom_ports)

            # Cargar estado de puertos
            for port, checkbox in self.port_checkboxes.items():
                # Valor predeterminado es True si no está especificado
                is_checked = self.current_profile.ports.get(str(port), True)
                checkbox.setChecked(is_checked)

            self.settings.setValue("last_profile_index", index)

    def createProfile(self):
        """Abre el diálogo para crear un nuevo perfil"""
        # Importar aquí para evitar problemas de importación circular
        from ilo_tunnel.gui.dialogs import ConnectionProfileDialog

        folders = self.profile_manager.get_folders()
        dialog = ConnectionProfileDialog(
            self, folders=folders, current_folder=self.current_folder
        )

        if dialog.exec():
            profile_data = dialog.get_profile_data()
            selected_folder = dialog.get_selected_folder()

            # Crear perfil a partir de los datos
            profile = ConnectionProfile.from_dict(profile_data)

            if self.profile_manager.add_profile(profile, selected_folder):
                # Actualizar la carpeta actual si cambió
                if selected_folder != self.current_folder:
                    self.current_folder = selected_folder
                    self.folder_combo.setCurrentText(selected_folder)
                    self.settings.setValue("last_folder", selected_folder)

                self.updateProfilesList()
                # Seleccionar el nuevo perfil
                self.profile_combo.setCurrentText(profile.name)

                self.statusBar().showMessage(
                    f"Perfil '{profile.name}' creado correctamente", 5000
                )
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    "No se pudo crear el perfil. Comprueba que no exista ya un perfil con el mismo nombre.",
                )

    def editProfile(self):
        """Edita el perfil seleccionado en el combo principal"""
        # Importar aquí para evitar problemas de importación circular
        from ilo_tunnel.gui.dialogs import ConnectionProfileDialog

        index = self.profile_combo.currentIndex()
        if index <= 0:
            QMessageBox.warning(
                self, "Error", "Por favor, selecciona un perfil para editar."
            )
            return

        profile_index = index - 1  # Adjust for the "Select Profile" item
        profiles = self.profile_manager.get_profiles(self.current_folder)

        if profile_index < len(profiles):
            profile = ConnectionProfile.from_dict(profiles[profile_index])
            folders = self.profile_manager.get_folders()
            dialog = ConnectionProfileDialog(
                self, profile.to_dict(), folders, self.current_folder
            )

            if dialog.exec():
                updated_profile_data = dialog.get_profile_data()
                selected_folder = dialog.get_selected_folder()
                updated_profile = ConnectionProfile.from_dict(updated_profile_data)

                # Si la carpeta cambió, mover el perfil
                if selected_folder != self.current_folder:
                    # Añadir a la nueva carpeta
                    if self.profile_manager.add_profile(
                        updated_profile, selected_folder
                    ):
                        # Eliminar de la carpeta actual
                        self.profile_manager.delete_profile(
                            self.current_folder, profile_index
                        )

                        # Actualizar a la nueva carpeta
                        self.current_folder = selected_folder
                        self.folder_combo.setCurrentText(selected_folder)
                        self.settings.setValue("last_folder", selected_folder)
                        self.updateProfilesList()

                        # Seleccionar el perfil editado
                        self.profile_combo.setCurrentText(updated_profile.name)

                        self.statusBar().showMessage(
                            f"Perfil '{updated_profile.name}' movido correctamente",
                            5000,
                        )
                    else:
                        QMessageBox.warning(
                            self,
                            "Error",
                            "No se pudo mover el perfil. Comprueba que no exista ya un perfil con el mismo nombre.",
                        )
                else:
                    # Actualizar en la misma carpeta
                    if self.profile_manager.update_profile(
                        self.current_folder, profile_index, updated_profile
                    ):
                        self.updateProfilesList()
                        # Reseleccionar el perfil editado
                        self.profile_combo.setCurrentText(updated_profile.name)
                        self.statusBar().showMessage(
                            f"Perfil '{updated_profile.name}' actualizado correctamente",
                            5000,
                        )
                    else:
                        QMessageBox.warning(
                            self, "Error", "No se pudo actualizar el perfil."
                        )

    def deleteProfile(self):
        """Elimina el perfil seleccionado en el combo principal"""
        index = self.profile_combo.currentIndex()
        if index <= 0:
            QMessageBox.warning(
                self, "Error", "Por favor, selecciona un perfil para eliminar."
            )
            return

        profile_index = index - 1  # Adjust for the "Select Profile" item
        profiles = self.profile_manager.get_profiles(self.current_folder)

        if profile_index < len(profiles):
            profile_name = profiles[profile_index]["name"]
            confirm = QMessageBox.question(
                self,
                "Confirmar eliminación",
                f"¿Estás seguro de que deseas eliminar el perfil '{profile_name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if confirm == QMessageBox.StandardButton.Yes:
                if self.profile_manager.delete_profile(
                    self.current_folder, profile_index
                ):
                    self.updateProfilesList()
                    self.profile_combo.setCurrentIndex(0)
                    self.statusBar().showMessage(
                        f"Perfil '{profile_name}' eliminado correctamente", 5000
                    )
                else:
                    QMessageBox.warning(self, "Error", "No se pudo eliminar el perfil.")

    def saveAsProfile(self):
        """Guarda la configuración actual como un nuevo perfil"""
        # Validar entradas
        if not self.validateInputs():
            return

        # Obtener configuración actual
        ports_data = {}
        for port, checkbox in self.port_checkboxes.items():
            ports_data[str(port)] = checkbox.isChecked()

        # Crear perfil con los datos actuales
        profile_data = {
            "ilo_ip": self.ilo_ip.text(),
            "ssh_user": self.ssh_user.text(),
            "gateway_ip": self.gateway_ip.text(),
            "ssh_port": self.ssh_port.value(),
            "local_ip": self.local_ip.currentText(),
            "key_path": self.key_path.text(),
            "ports": ports_data,
        }

        # Pedir nombre para el perfil
        name, ok = QInputDialog.getText(self, "Guardar perfil", "Nombre del perfil:")

        if ok and name:
            profile_data["name"] = name
            profile = ConnectionProfile.from_dict(profile_data)

            if self.profile_manager.add_profile(profile, self.current_folder):
                self.updateProfilesList()
                # Seleccionar el nuevo perfil
                self.profile_combo.setCurrentText(name)
                self.statusBar().showMessage(
                    f"Perfil '{name}' guardado correctamente", 5000
                )
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    "No se pudo guardar el perfil. Comprueba que no exista ya un perfil con el mismo nombre.",
                )

    def loadProfileFromList(self, item):
        """Carga un perfil seleccionado de la lista de perfiles"""
        profile_name = item.text()
        folder = self.profiles_folder_combo.currentText()

        # Buscar el perfil por nombre
        profile, folder, _ = self.profile_manager.get_profile_by_name(
            profile_name, folder
        )

        if profile:
            # Cambiar a la pestaña de conexión
            self.tabs.setCurrentIndex(0)

            # Actualizar selector de carpeta y perfil en la pestaña de conexión
            self.folder_combo.setCurrentText(folder)
            self.current_folder = folder
            self.updateProfilesList()

            # Cargar el perfil
            index = self.profile_combo.findText(profile_name)
            if index > 0:
                # +1 porque el primer elemento es "-- Seleccionar Perfil --"
                self.profile_combo.setCurrentIndex(index)

                # Guardar índice del último perfil usado
                self.settings.setValue("last_profile_index", index)

    def loadSelectedProfile(self):
        """Carga el perfil seleccionado en la lista de perfiles"""
        current_item = self.profiles_list.currentItem()
        if current_item:
            self.loadProfileFromList(current_item)

    def editProfileFromList(self):
        """Edita el perfil seleccionado en la lista de perfiles"""
        # Importar aquí para evitar problemas de importación circular
        from ilo_tunnel.gui.dialogs import ConnectionProfileDialog

        current_item = self.profiles_list.currentItem()
        if not current_item:
            QMessageBox.warning(
                self, "Error", "Por favor, selecciona un perfil para editar."
            )
            return

        profile_name = current_item.text()
        folder = self.profiles_folder_combo.currentText()

        # Buscar el perfil por nombre
        profile, folder, index = self.profile_manager.get_profile_by_name(
            profile_name, folder
        )

        if profile:
            folders = self.profile_manager.get_folders()
            dialog = ConnectionProfileDialog(self, profile.to_dict(), folders, folder)

            if dialog.exec():
                updated_profile_data = dialog.get_profile_data()
                selected_folder = dialog.get_selected_folder()
                updated_profile = ConnectionProfile.from_dict(updated_profile_data)

                # Si la carpeta cambió, mover el perfil
                if selected_folder != folder:
                    # Añadir a la nueva carpeta
                    if self.profile_manager.add_profile(
                        updated_profile, selected_folder
                    ):
                        # Eliminar de la carpeta actual
                        self.profile_manager.delete_profile(folder, index)

                        # Actualizar listas de perfiles
                        self.updateProfilesListWidget(folder)
                        self.updateProfilesListWidget(selected_folder)

                        # Si la carpeta actual en la pestaña de conexión es la misma, actualizarla también
                        if (
                            self.current_folder == folder
                            or self.current_folder == selected_folder
                        ):
                            self.updateProfilesList()

                        self.statusBar().showMessage(
                            f"Perfil '{updated_profile.name}' movido correctamente",
                            5000,
                        )
                    else:
                        QMessageBox.warning(
                            self,
                            "Error",
                            "No se pudo mover el perfil. Comprueba que no exista ya un perfil con el mismo nombre.",
                        )
                else:
                    # Actualizar en la misma carpeta
                    if self.profile_manager.update_profile(
                        folder, index, updated_profile
                    ):
                        # Actualizar listas de perfiles
                        self.updateProfilesListWidget(folder)

                        # Si la carpeta actual en la pestaña de conexión es la misma, actualizarla también
                        if self.current_folder == folder:
                            self.updateProfilesList()

                        self.statusBar().showMessage(
                            f"Perfil '{updated_profile.name}' actualizado correctamente",
                            5000,
                        )
                    else:
                        QMessageBox.warning(
                            self, "Error", "No se pudo actualizar el perfil."
                        )

    def deleteProfileFromList(self):
        """Elimina el perfil seleccionado en la lista de perfiles"""
        current_item = self.profiles_list.currentItem()
        if not current_item:
            QMessageBox.warning(
                self, "Error", "Por favor, selecciona un perfil para eliminar."
            )
            return

        profile_name = current_item.text()
        folder = self.profiles_folder_combo.currentText()

        # Buscar el perfil por nombre
        profile, folder, index = self.profile_manager.get_profile_by_name(
            profile_name, folder
        )

        if profile:
            confirm = QMessageBox.question(
                self,
                "Confirmar eliminación",
                f"¿Estás seguro de que deseas eliminar el perfil '{profile_name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if confirm == QMessageBox.StandardButton.Yes:
                if self.profile_manager.delete_profile(folder, index):
                    # Actualizar listas de perfiles
                    self.updateProfilesListWidget(folder)

                    # Si la carpeta actual en la pestaña de conexión es la misma, actualizarla también
                    if self.current_folder == folder:
                        self.updateProfilesList()

                    self.statusBar().showMessage(
                        f"Perfil '{profile_name}' eliminado correctamente", 5000
                    )
                else:
                    QMessageBox.warning(self, "Error", "No se pudo eliminar el perfil.")

    def cloneProfileFromList(self):
        """Clona el perfil seleccionado en la lista de perfiles"""
        current_item = self.profiles_list.currentItem()
        if not current_item:
            QMessageBox.warning(
                self, "Error", "Por favor, selecciona un perfil para clonar."
            )
            return

        profile_name = current_item.text()
        folder = self.profiles_folder_combo.currentText()

        # Buscar el perfil por nombre
        profile, folder, _ = self.profile_manager.get_profile_by_name(
            profile_name, folder
        )

        if profile:
            # Crear copia
            profile_copy = ConnectionProfile.from_dict(profile.to_dict())

            # Pedir nuevo nombre
            name, ok = QInputDialog.getText(
                self,
                "Clonar perfil",
                "Nombre del nuevo perfil:",
                text=f"{profile_name} (copia)",
            )

            if ok and name:
                profile_copy.name = name

                if self.profile_manager.add_profile(profile_copy, folder):
                    # Actualizar listas de perfiles
                    self.updateProfilesListWidget(folder)

                    # Si la carpeta actual en la pestaña de conexión es la misma, actualizarla también
                    if self.current_folder == folder:
                        self.updateProfilesList()

                    self.statusBar().showMessage(
                        f"Perfil '{name}' clonado correctamente", 5000
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "Error",
                        "No se pudo clonar el perfil. Comprueba que no exista ya un perfil con el mismo nombre.",
                    )

    def createFolder(self):
        """Crea una nueva carpeta de perfiles"""
        folder_name, ok = QInputDialog.getText(
            self, "Nueva Carpeta", "Nombre de la carpeta:"
        )

        if ok and folder_name:
            if self.profile_manager.add_folder(folder_name):
                self.updateFolderCombos()
                self.profiles_folder_combo.setCurrentText(folder_name)
                self.statusBar().showMessage(
                    f"Carpeta '{folder_name}' creada correctamente", 5000
                )
            else:
                QMessageBox.warning(
                    self, "Error", "Ya existe una carpeta con ese nombre."
                )

    def manageFolders(self):
        """Abre el diálogo de gestión de carpetas"""
        # Importar aquí para evitar problemas de importación circular
        from ilo_tunnel.gui.dialogs import FolderManagementDialog

        dialog = FolderManagementDialog(self, self.profile_manager)
        dialog.exec()

        # Actualizar las carpetas después de la gestión
        current_folder = ""
        if hasattr(self, "folder_combo") and self.folder_combo is not None:
            current_folder = self.folder_combo.currentText()

        # Actualizar combos si el método existe
        if hasattr(self, "updateFolderCombos"):
            self.updateFolderCombos()
        else:
            # Actualización manual
            folders = self.profile_manager.get_folders()

            # Actualizar combos
            if hasattr(self, "folder_combo") and self.folder_combo is not None:
                self.folder_combo.clear()
                self.folder_combo.addItems(folders)

            if (
                hasattr(self, "profiles_folder_combo")
                and self.profiles_folder_combo is not None
            ):
                self.profiles_folder_combo.clear()
                self.profiles_folder_combo.addItems(folders)

        # Intentar mantener la carpeta seleccionada
        if (
            current_folder
            and hasattr(self, "folder_combo")
            and self.folder_combo is not None
        ):
            if current_folder in [
                self.folder_combo.itemText(i) for i in range(self.folder_combo.count())
            ]:
                self.folder_combo.setCurrentText(current_folder)

        # Actualizar los perfiles si el método existe
        if hasattr(self, "updateProfilesList"):
            self.updateProfilesList()

    def importProfiles(self):
        """Importa perfiles desde un archivo JSON"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Importar perfiles",
            "",
            "Archivos JSON (*.json);;Todos los archivos (*)",
        )

        if file_path:
            try:
                with open(file_path, "r") as f:
                    json_data = f.read()

                success, count, errors = self.profile_manager.import_profiles(json_data)

                if success:
                    # Actualizar interfaces
                    self.updateFolderCombos()
                    self.updateProfilesList()
                    self.updateProfilesListWidget()

                    QMessageBox.information(
                        self,
                        "Importación completada",
                        f"Se importaron {count} perfiles correctamente.",
                    )
                else:
                    error_msg = "\n".join(errors)
                    QMessageBox.warning(
                        self,
                        "Error de importación",
                        f"No se pudieron importar los perfiles:\n{error_msg}",
                    )
            except Exception as e:
                QMessageBox.critical(
                    self, "Error de importación", f"Error al leer el archivo: {str(e)}"
                )

    def exportProfiles(self):
        """Exporta perfiles a un archivo JSON"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exportar perfiles", "", "Archivos JSON (*.json)"
        )

        if file_path:
            # Asegurar extensión .json
            if not file_path.lower().endswith(".json"):
                file_path += ".json"

            try:
                json_data = self.profile_manager.export_profiles()

                with open(file_path, "w") as f:
                    f.write(json_data)

                QMessageBox.information(
                    self,
                    "Exportación completada",
                    f"Los perfiles se han exportado correctamente a:\n{file_path}",
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error de exportación",
                    f"Error al guardar el archivo: {str(e)}",
                )

    def browseKeyFile(self):
        """Abre un diálogo para seleccionar el archivo de clave SSH"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar clave SSH",
            os.path.expanduser("~/.ssh"),
            "Archivos de clave SSH (id_rsa id_dsa *.pem *.key);;Todos los archivos (*)",
        )

        if file_path:
            self.key_path.setText(file_path)

    def startTunnel(self):
        """Inicia el túnel SSH con la configuración actual"""
        if not self.validateInputs():
            return

        # Preparar mapeos de puertos
        port_mappings = []

        # Si se usan puertos personalizados, usar los seleccionados en la interfaz
        if self.use_custom_ports.isChecked():
            for port, checkbox in self.port_checkboxes.items():
                if checkbox.isChecked():
                    mapping = f"{self.local_ip.currentText()}:{port}:{self.ilo_ip.text()}:{port}"
                    port_mappings.append(mapping)

                    # Actualizar estado a "conectando"
                    if port in self.port_status_widgets:
                        self.port_status_widgets[port].setStatus("connecting")
        else:
            # Usar los puertos definidos para el tipo de servidor seleccionado
            server_type = self.server_type_combo.currentText()
            server_ports = get_server_ports(server_type)

            for port in server_ports.keys():
                mapping = (
                    f"{self.local_ip.currentText()}:{port}:{self.ilo_ip.text()}:{port}"
                )
                port_mappings.append(mapping)

                # Actualizar estado a "conectando" si existe el widget
                if port in self.port_status_widgets:
                    self.port_status_widgets[port].setStatus("connecting")

        if not port_mappings:
            QMessageBox.warning(
                self,
                "Sin puertos",
                "Debes seleccionar al menos un puerto para tunelizar.",
            )
            return

        # Guardar configuración actual
        self.saveCurrentConfig()

        # Mostrar mensaje sobre puertos monitoreados
        essential_ports = get_server_essential_ports(
            self.server_type_combo.currentText()
        )
        self.console.append(
            f"Nota: Solo se monitoreará el estado de los puertos esenciales: {', '.join(map(str, essential_ports))}"
        )

        # Iniciar túnel usando SSHManager
        if self.ssh_manager.create_tunnel(
            self.key_path.text(),
            self.ssh_port.value(),
            port_mappings,
            self.ssh_user.text(),
            self.gateway_ip.text(),
            self.verbose_checkbox.isChecked(),
            self.compress_checkbox.isChecked(),
            self.identity_only_checkbox.isChecked(),
            self.ssh_timeout_spinbox.value(),
        ):
            # Activar reconexión automática si está habilitada
            self.ssh_manager.set_auto_reconnect(
                self.auto_reconnect_checkbox.isChecked(),
                self.reconnect_attempts_spinbox.value(),
            )

            # Actualizar interfaz
            self.connect_btn.setEnabled(False)
            self.connect_action.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
            self.disconnect_action.setEnabled(True)

            # Iniciar monitor de puertos
            self.port_monitor_timer.start(2000)  # Comprobar cada 2 segundos

            self.statusBar().showMessage("Conectando...", 5000)
        else:
            QMessageBox.critical(
                self,
                "Error de conexión",
                "No se pudo iniciar el túnel SSH. Comprueba la configuración y los permisos.",
            )

    def stopTunnel(self):
        """Detiene el túnel SSH activo"""
        if self.ssh_manager.stop_tunnel():
            self.console.append("Túnel cerrado correctamente.\n")

            # Actualizar interfaz
            self.connect_btn.setEnabled(True)
            self.connect_action.setEnabled(True)
            self.disconnect_btn.setEnabled(False)
            self.disconnect_action.setEnabled(False)

            # Detener monitor de puertos
            self.port_monitor_timer.stop()

            # Resetear estados de puertos
            for port, widget in self.port_status_widgets.items():
                widget.setStatus("disconnected")

            self.statusBar().showMessage("Desconectado", 5000)

    def onSshOutput(self, data):
        """Maneja la salida estándar del proceso SSH"""
        self.console.append(data)

        # Scroll al final si está habilitado el auto-scroll
        if self.auto_scroll_checkbox.isChecked():
            self.console.moveCursor(QTextCursor.MoveOperation.End)

    def onSshError(self, data):
        """Maneja la salida de error del proceso SSH"""
        # Marcar errores en color rojo
        self.console.setTextColor(QColor("red"))
        self.console.append(data)
        self.console.setTextColor(QColor("black"))

        # Scroll al final si está habilitado el auto-scroll
        if self.auto_scroll_checkbox.isChecked():
            self.console.moveCursor(QTextCursor.MoveOperation.End)

    def onProcessFinished(self, exit_code, status_msg):
        """Maneja la finalización del proceso SSH"""
        self.connect_btn.setEnabled(True)
        self.connect_action.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.disconnect_action.setEnabled(False)

        self.console.append(f"Proceso finalizado: {status_msg} (código {exit_code})\n")

        # Detener monitor de puertos
        self.port_monitor_timer.stop()

        # Resetear estados de puertos
        for port, widget in self.port_status_widgets.items():
            widget.setStatus("disconnected")

    def onConnectionStatusChanged(self, connected, message):
        """Maneja los cambios en el estado de la conexión"""
        if connected:
            self.statusBar().showMessage(message, 5000)
            self.console.append(f"Túnel SSH establecido: {message}\n")
        else:
            self.statusBar().showMessage(message, 5000)

    def checkPortStatus(self):
        """Verifica el estado de los puertos tunelizados"""
        if not self.ssh_manager.is_connected():
            self.port_monitor_timer.stop()
            return

        # Obtener puertos esenciales según el tipo de servidor seleccionado
        selected_server_type = self.server_type_combo.currentText()
        essential_ports = get_server_essential_ports(selected_server_type)

        # Preparar mapeos de puertos esenciales
        port_mappings = []
        for port in essential_ports:
            if port in self.port_checkboxes and self.port_checkboxes[port].isChecked():
                local_ip = self.local_ip.currentText()
                mapping = f"{local_ip}:{port}:{self.ilo_ip.text()}:{port}"
                port_mappings.append(mapping)

        # Comprobar estado de los puertos
        if port_mappings:
            self.ssh_manager.check_port_status(port_mappings)

    def updatePortStatus(self, port_name, is_open):
        """Actualiza el indicador de estado de un puerto"""
        parts = port_name.split(":")
        if len(parts) >= 2:
            local_port = int(parts[1])
            if local_port in self.port_status_widgets:
                self.port_status_widgets[local_port].setStatus(
                    "connected" if is_open else "error"
                )

    def openBrowser(self):
        """Abre el navegador para acceder a la interfaz ILO"""
        # URL https por defecto
        url = f"https://{self.local_ip.currentText()}"

        if 443 in self.port_checkboxes and not self.port_checkboxes[443].isChecked():
            # Si el puerto 443 no está seleccionado, intentar con HTTP
            if 80 in self.port_checkboxes and self.port_checkboxes[80].isChecked():
                url = f"http://{self.local_ip.currentText()}"

        try:
            self.console.append(f"Abriendo navegador en {url}\n")
            webbrowser.open(url)
        except Exception as e:
            self.console.append(f"Error al abrir el navegador: {str(e)}\n")

    def validateInputs(self):
        """Valida los campos obligatorios del formulario"""
        if not self.ilo_ip.text():
            QMessageBox.warning(self, "Error", "La IP de ILO es obligatoria.")
            return False

        if not self.ssh_user.text():
            QMessageBox.warning(self, "Error", "El usuario SSH es obligatorio.")
            return False

        if not self.gateway_ip.text():
            QMessageBox.warning(self, "Error", "La IP del gateway es obligatoria.")
            return False

        if not self.key_path.text():
            QMessageBox.warning(
                self, "Error", "La ruta de la clave SSH es obligatoria."
            )
            return False

        # Verificar si hay al menos un puerto seleccionado
        any_port_selected = any(
            checkbox.isChecked() for checkbox in self.port_checkboxes.values()
        )
        if not any_port_selected:
            QMessageBox.warning(
                self, "Error", "Debe seleccionar al menos un puerto para tunelizar."
            )
            return False

        return True

    def saveCurrentConfig(self):
        """Guarda la configuración actual en las preferencias"""
        self.settings.setValue("ilo_ip", self.ilo_ip.text())
        self.settings.setValue("ssh_user", self.ssh_user.text())
        self.settings.setValue("gateway_ip", self.gateway_ip.text())
        self.settings.setValue("ssh_port", self.ssh_port.value())
        self.settings.setValue("local_ip", self.local_ip.currentText())
        self.settings.setValue("key_path", self.key_path.text())
        self.settings.setValue("server_type", self.server_type_combo.currentText())
        self.settings.setValue("custom_ports", self.use_custom_ports.isChecked())

        # Guardar estado de puertos
        ports_data = {}
        for port, checkbox in self.port_checkboxes.items():
            ports_data[str(port)] = checkbox.isChecked()

        self.settings.setValue("ports", ports_data)

    def toggleAutoReconnect(self, state):
        """Activa o desactiva la reconexión automática"""
        is_checked = state == Qt.CheckState.Checked

        # Actualizar el SSHManager solo si hay una conexión activa
        if self.ssh_manager.is_connected():
            self.ssh_manager.set_auto_reconnect(
                is_checked, self.reconnect_attempts_spinbox.value()
            )

    def copyConsoleText(self):
        """Copia el texto de la consola al portapapeles"""
        text = self.console.toPlainText()
        QApplication.clipboard().setText(text)
        self.statusBar().showMessage("Texto copiado al portapapeles", 3000)

    def saveConsoleText(self):
        """Guarda el texto de la consola a un archivo"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar registro",
            "",
            "Archivos de texto (*.txt);;Todos los archivos (*)",
        )

        if file_path:
            # Asegurar extensión .txt
            if not file_path.lower().endswith(".txt"):
                file_path += ".txt"

            try:
                text = self.console.toPlainText()
                with open(file_path, "w") as f:
                    f.write(text)

                self.statusBar().showMessage(f"Registro guardado en {file_path}", 5000)
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"No se pudo guardar el archivo: {str(e)}"
                )

    def closeEvent(self, event):
        """Maneja el cierre de la ventana"""
        # Comprobar si hay una conexión activa
        if self.ssh_manager.is_connected():
            # Confirmar cierre si está habilitada la confirmación
            if self.confirm_exit_checkbox.isChecked():
                confirm = QMessageBox.question(
                    self,
                    "Confirmar salida",
                    "Hay una conexión activa. ¿Deseas cerrarla y salir?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )

                if confirm == QMessageBox.StandardButton.Yes:
                    self.ssh_manager.stop_tunnel()
                else:
                    event.ignore()
                    return
            else:
                # Cerrar túnel sin confirmación
                self.ssh_manager.stop_tunnel()

        # Guardar la configuración antes de salir
        self.saveCurrentConfig()
        event.accept()
