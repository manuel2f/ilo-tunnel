import sys
import subprocess
import platform
import webbrowser
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                           QSpinBox, QTabWidget, QTextEdit, QCheckBox,
                           QMessageBox, QGridLayout, QFormLayout, QComboBox,
                           QDialog, QDialogButtonBox, QListWidget, QInputDialog)
from PyQt6.QtCore import Qt, QProcess, QSettings
from PyQt6.QtCore import QObject, QProcess, pyqtSignal

class ConnectionProfileDialog(QDialog):
    def __init__(self, parent=None, profile_data=None, folders=None, current_folder="DEFAULT"):
        super().__init__(parent)
        self.port_checkboxes = {}
        self.profile_data = profile_data or {}
        self.folders = folders or ["DEFAULT"]
        self.current_folder = current_folder
        self.setWindowTitle("Perfil de Conexión")
        self.setMinimumWidth(400)
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        # Carpeta
        self.folder_combo = QComboBox()
        self.folder_combo.addItems(self.folders)
        if self.current_folder in self.folders:
            self.folder_combo.setCurrentText(self.current_folder)
        form_layout.addRow("Carpeta:", self.folder_combo)
        
        # Profile name
        self.profile_name = QLineEdit()
        self.profile_name.setText(self.profile_data.get("name", ""))
        form_layout.addRow("Nombre del perfil:", self.profile_name)
        
        # Connection details
        self.ilo_ip = QLineEdit()
        self.ilo_ip.setText(self.profile_data.get("ilo_ip", ""))
        form_layout.addRow("IP de ILO:", self.ilo_ip)
        
        self.ssh_user = QLineEdit()
        self.ssh_user.setText(self.profile_data.get("ssh_user", ""))
        form_layout.addRow("Usuario SSH:", self.ssh_user)
        
        self.gateway_ip = QLineEdit()
        self.gateway_ip.setText(self.profile_data.get("gateway_ip", ""))
        form_layout.addRow("IP de Gateway:", self.gateway_ip)
        
        self.ssh_port = QSpinBox()
        self.ssh_port.setRange(1, 65535)
        self.ssh_port.setValue(self.profile_data.get("ssh_port", 22))
        form_layout.addRow("Puerto SSH:", self.ssh_port)
        
        self.local_ip = QLineEdit()
        self.local_ip.setText(self.profile_data.get("local_ip", "127.0.0.1"))
        form_layout.addRow("IP Local:", self.local_ip)
        
        self.key_path = QLineEdit()
        self.key_path.setText(self.profile_data.get("key_path", "~/.ssh/id_rsa"))
        form_layout.addRow("Ruta de la clave SSH:", self.key_path)
        
        layout.addLayout(form_layout)
        
        # Los puertos se manejan internamente y no se muestran en la interfaz
        self.port_data = self.profile_data.get("ports", {})
        if not self.port_data:
            # Establecer todos los puertos a True por defecto
            common_ports = [22, 23, 80, 443, 3389, 17988, 9300, 17990, 3002, 2198]
            for port in common_ports:
                self.port_data[str(port)] = True
        
        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_profile_data(self):
        # Collect all profile data
        return {
            "name": self.profile_name.text(),
            "ilo_ip": self.ilo_ip.text(),
            "ssh_user": self.ssh_user.text(),
            "gateway_ip": self.gateway_ip.text(),
            "ssh_port": self.ssh_port.value(),
            "local_ip": self.local_ip.text(),
            "key_path": self.key_path.text(),
            "ports": self.port_data
        }
    
    def get_selected_folder(self):
        return self.folder_combo.currentText()
    
    def validate(self):
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
        
        return True
    
    def accept(self):
        if self.validate():
            super().accept()


class ProfileManager:
    def __init__(self):
        self.settings = QSettings("ILOTunnel", "ILOTunnelApp")
        
    def get_profiles(self, folder=None):
        profiles_json = self.settings.value("connection_profiles", "{}")
        try:
            profiles_data = json.loads(profiles_json)
            
            # Si no hay estructura de carpetas, convertir al nuevo formato
            if isinstance(profiles_data, list):
                profiles_data = {"DEFAULT": profiles_data}
                self.save_profiles_data(profiles_data)
            
            if folder:
                return profiles_data.get(folder, [])
            else:
                return profiles_data
        except:
            # Inicializar con estructura de carpetas vacía
            return {"DEFAULT": []}
    
    def get_folders(self):
        profiles_data = self.get_profiles()
        return list(profiles_data.keys())
    
    def save_profiles_data(self, profiles_data):
        self.settings.setValue("connection_profiles", json.dumps(profiles_data))
    
    def add_profile(self, profile_data, folder="DEFAULT"):
        profiles_data = self.get_profiles()
        if folder not in profiles_data:
            profiles_data[folder] = []
        profiles_data[folder].append(profile_data)
        self.save_profiles_data(profiles_data)
    
    def update_profile(self, folder, index, profile_data):
        profiles_data = self.get_profiles()
        if folder in profiles_data and 0 <= index < len(profiles_data[folder]):
            profiles_data[folder][index] = profile_data
            self.save_profiles_data(profiles_data)
    
    def delete_profile(self, folder, index):
        profiles_data = self.get_profiles()
        if folder in profiles_data and 0 <= index < len(profiles_data[folder]):
            del profiles_data[folder][index]
            self.save_profiles_data(profiles_data)
    
    def get_profile_names(self, folder="DEFAULT"):
        return [profile["name"] for profile in self.get_profiles(folder)]
    
    def add_folder(self, folder_name):
        if not folder_name:
            return False
            
        profiles_data = self.get_profiles()
        if folder_name not in profiles_data:
            profiles_data[folder_name] = []
            self.save_profiles_data(profiles_data)
            return True
        return False
    
    def rename_folder(self, old_name, new_name):
        if not new_name or old_name == new_name:
            return False
            
        profiles_data = self.get_profiles()
        if old_name in profiles_data and new_name not in profiles_data:
            profiles_data[new_name] = profiles_data.pop(old_name)
            self.save_profiles_data(profiles_data)
            return True
        return False
    
    def delete_folder(self, folder_name):
        if folder_name == "DEFAULT":
            return False  # No permitir eliminar la carpeta por defecto
            
        profiles_data = self.get_profiles()
        if folder_name in profiles_data:
            del profiles_data[folder_name]
            self.save_profiles_data(profiles_data)
            return True
        return False
    
    def move_profile(self, source_folder, index, target_folder):
        profiles_data = self.get_profiles()
        if (source_folder in profiles_data and 
            target_folder in profiles_data and 
            0 <= index < len(profiles_data[source_folder])):
            
            profile = profiles_data[source_folder].pop(index)
            profiles_data[target_folder].append(profile)
            self.save_profiles_data(profiles_data)
            return True
        return False

class FolderManagementDialog(QDialog):
    def __init__(self, parent=None, profile_manager=None):
        super().__init__(parent)
        self.profile_manager = profile_manager
        self.setWindowTitle("Gestión de Carpetas")
        self.setMinimumWidth(350)
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
        
        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def add_folder(self):
        folder_name, ok = QInputDialog.getText(
            self, "Nueva Carpeta", "Nombre de la carpeta:"
        )
        
        if ok and folder_name:
            if self.profile_manager.add_folder(folder_name):
                self.refresh_folder_list()
            else:
                QMessageBox.warning(self, "Error", "Ya existe una carpeta con ese nombre.")
    
    def rename_folder(self):
        current_row = self.folder_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Selecciona una carpeta para renombrar.")
            return
        
        old_name = self.folder_list.item(current_row).text()
        if old_name == "DEFAULT":
            QMessageBox.warning(self, "Error", "No se puede renombrar la carpeta por defecto.")
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
        current_row = self.folder_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Selecciona una carpeta para eliminar.")
            return
        
        folder_name = self.folder_list.item(current_row).text()
        if folder_name == "DEFAULT":
            QMessageBox.warning(self, "Error", "No se puede eliminar la carpeta por defecto.")
            return
        
        confirm = QMessageBox.question(
            self, "Confirmar eliminación",
            f"¿Estás seguro de que deseas eliminar la carpeta '{folder_name}'?\n"
            "Todos los perfiles en esta carpeta se perderán.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            if self.profile_manager.delete_folder(folder_name):
                self.refresh_folder_list()
            else:
                QMessageBox.warning(self, "Error", "No se pudo eliminar la carpeta.")
    
    def refresh_folder_list(self):
        self.folder_list.clear()
        self.folder_list.addItems(self.profile_manager.get_folders())

class SSHManager(QObject):
    output_ready = pyqtSignal(str)
    error_ready = pyqtSignal(str)
    process_finished = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.process = None
    
    def create_tunnel(self, key_path, ssh_port, port_mappings, user, gateway):
        """
        Create SSH tunnel with specified parameters
        
        Args:
            key_path (str): Path to SSH key
            ssh_port (int): SSH port number
            port_mappings (list): List of port mappings in format "local_ip:local_port:remote_host:remote_port"
            user (str): SSH username
            gateway (str): Gateway address
        """
        cmd = ["sudo", "ssh", "-i", os.path.expanduser(key_path), "-p", str(ssh_port)]
        
        # Add port mappings
        for mapping in port_mappings:
            cmd.extend(["-L", mapping])
        
        # Add destination
        cmd.append(f"{user}@{gateway}")
        
        self.output_ready.emit(f"Running command: {' '.join(cmd)}")
        
        # Start process
        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self._handle_stdout)
        self.process.readyReadStandardError.connect(self._handle_stderr)
        self.process.finished.connect(lambda code, _: self.process_finished.emit(code))
        
        self.process.start(cmd[0], cmd[1:])
    
    def stop_tunnel(self):
        """Stop the running SSH tunnel"""
        if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.terminate()
            if not self.process.waitForFinished(3000):  # Wait 3 seconds
                self.process.kill()
            return True
        return False
    
    def _handle_stdout(self):
        data = self.process.readAllStandardOutput().data().decode()
        self.output_ready.emit(data)
    
    def _handle_stderr(self):
        data = self.process.readAllStandardError().data().decode()
        self.error_ready.emit(data)

class ILOTunnelApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.process = None
        self.settings = QSettings("ILOTunnel", "ILOTunnelApp")
        self.profile_manager = ProfileManager()
        self.current_folder = "DEFAULT"
        self.initUI()
        self.loadSettings()
        
    def initUI(self):
        self.setWindowTitle("HP ProLiant ILO Tunnel Manager")
        self.setMinimumSize(600, 500)
        
        # Create central widget and main layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        
        # Create tabs
        tabs = QTabWidget()
        main_layout.addWidget(tabs)
        
        # Connection tab
        connection_tab = QWidget()
        connection_layout = QVBoxLayout(connection_tab)
        
        # Folder and profile selection
        profile_header = QHBoxLayout()
        
        self.folder_combo = QComboBox()
        self.folder_combo.currentIndexChanged.connect(self.folder_changed)
        profile_header.addWidget(QLabel("Carpeta:"))
        profile_header.addWidget(self.folder_combo)
        
        self.manage_folders_button = QPushButton("Gestionar")
        self.manage_folders_button.clicked.connect(self.manage_folders)
        profile_header.addWidget(self.manage_folders_button)
        
        connection_layout.addLayout(profile_header)
        
        # Profile selection
        profile_layout = QHBoxLayout()
        profile_layout.addWidget(QLabel("Perfil:"))
        
        self.profile_combo = QComboBox()
        self.profile_combo.currentIndexChanged.connect(self.load_profile)
        profile_layout.addWidget(self.profile_combo)
        
        self.new_profile_button = QPushButton("Nuevo")
        self.new_profile_button.clicked.connect(self.create_profile)
        profile_layout.addWidget(self.new_profile_button)
        
        self.edit_profile_button = QPushButton("Editar")
        self.edit_profile_button.clicked.connect(self.edit_profile)
        profile_layout.addWidget(self.edit_profile_button)
        
        self.delete_profile_button = QPushButton("Eliminar")
        self.delete_profile_button.clicked.connect(self.delete_profile)
        profile_layout.addWidget(self.delete_profile_button)
        
        connection_layout.addLayout(profile_layout)
        
        # Connection form
        form_layout = QFormLayout()
        
        self.ilo_ip = QLineEdit()
        form_layout.addRow("IP de ILO:", self.ilo_ip)
        
        self.ssh_user = QLineEdit()
        form_layout.addRow("Usuario SSH:", self.ssh_user)
        
        self.gateway_ip = QLineEdit()
        form_layout.addRow("IP de Gateway:", self.gateway_ip)
        
        self.ssh_port = QSpinBox()
        self.ssh_port.setRange(1, 65535)
        self.ssh_port.setValue(22)
        form_layout.addRow("Puerto SSH:", self.ssh_port)
        
        self.local_ip = QLineEdit()
        self.local_ip.setText("127.0.0.1")
        form_layout.addRow("IP Local:", self.local_ip)
        
        self.key_path = QLineEdit()
        self.key_path.setText("~/.ssh/id_rsa")
        form_layout.addRow("Ruta de la clave SSH:", self.key_path)
        
        connection_layout.addLayout(form_layout)
        
        # La configuración de puertos ya no se muestra en la UI pero se mantiene internamente
        self.port_data = {}
        common_ports = [22, 23, 80, 443, 3389, 17988, 9300, 17990, 3002, 2198]
        for port in common_ports:
            self.port_data[str(port)] = True
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        self.connect_button = QPushButton("Conectar")
        self.connect_button.clicked.connect(self.startTunnel)
        action_layout.addWidget(self.connect_button)
        
        self.disconnect_button = QPushButton("Desconectar")
        self.disconnect_button.clicked.connect(self.stopTunnel)
        self.disconnect_button.setEnabled(False)
        action_layout.addWidget(self.disconnect_button)
        
        self.open_browser_button = QPushButton("Abrir en Navegador")
        self.open_browser_button.clicked.connect(self.openBrowser)
        action_layout.addWidget(self.open_browser_button)
        
        self.save_as_profile_button = QPushButton("Guardar como Perfil")
        self.save_as_profile_button.clicked.connect(self.save_as_profile)
        action_layout.addWidget(self.save_as_profile_button)
        
        connection_layout.addLayout(action_layout)
        
        # Output console
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        connection_layout.addWidget(QLabel("Consola:"))
        connection_layout.addWidget(self.console)
        
        # Add connection tab
        tabs.addTab(connection_tab, "Conexión")
        
        # Help tab (mantiene el código original)
        help_tab = QWidget()
        help_layout = QVBoxLayout(help_tab)
        
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setHtml("""
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
        
        <p><b>Nota:</b> Esta aplicación requiere permisos de administrador para crear los túneles.</p>
        """)
        
        help_layout.addWidget(help_text)
        tabs.addTab(help_tab, "Ayuda")
        
        # Central widget
        self.setCentralWidget(central_widget)
        
        # Initialize SSH manager
        self.ssh_manager = SSHManager()
        self.ssh_manager.output_ready.connect(self.onSshOutput)
        self.ssh_manager.error_ready.connect(self.onSshError)
        self.ssh_manager.process_finished.connect(self.onProcessFinished)
        
    def loadSettings(self):
        # Actualizar lista de carpetas
        self.update_folder_list()
        
        # Cargar última carpeta usada
        last_folder = self.settings.value("last_folder", "DEFAULT")
        if last_folder in [self.folder_combo.itemText(i) for i in range(self.folder_combo.count())]:
            self.folder_combo.setCurrentText(last_folder)
            self.current_folder = last_folder
        
        # Cargar último perfil usado
        self.update_profiles_list()
        last_profile_index = int(self.settings.value("last_profile_index", -1))
        
        if last_profile_index >= 0 and last_profile_index < self.profile_combo.count():
            self.profile_combo.setCurrentIndex(last_profile_index)
        else:
            # Load individual settings if no profile was selected
            self.ilo_ip.setText(self.settings.value("ilo_ip", ""))
            self.ssh_user.setText(self.settings.value("ssh_user", ""))
            self.gateway_ip.setText(self.settings.value("gateway_ip", ""))
            self.ssh_port.setValue(int(self.settings.value("ssh_port", 22)))
            self.local_ip.setText(self.settings.value("local_ip", "127.0.0.1"))
            self.key_path.setText(self.settings.value("key_path", "~/.ssh/id_rsa"))
            
            # Cargar estado de puertos (ahora interno)
            saved_ports = self.settings.value("ports", {})
            if saved_ports:
                self.port_data = saved_ports
    
    def update_folder_list(self):
        folders = self.profile_manager.get_folders()
        self.folder_combo.clear()
        self.folder_combo.addItems(folders)
    
    def folder_changed(self, index):
        if index >= 0:
            self.current_folder = self.folder_combo.itemText(index)
            self.settings.setValue("last_folder", self.current_folder)
            self.update_profiles_list()
    
    def manage_folders(self):
        dialog = FolderManagementDialog(self, self.profile_manager)
        dialog.exec()
        
        # Actualizar la lista de carpetas después de la gestión
        current_folder = self.folder_combo.currentText()
        self.update_folder_list()
        
        # Intentar mantener la carpeta seleccionada
        if current_folder in [self.folder_combo.itemText(i) for i in range(self.folder_combo.count())]:
            self.folder_combo.setCurrentText(current_folder)
        
        self.update_profiles_list()
    
    def update_profiles_list(self):
        # Actualizar lista de perfiles de la carpeta actual
        self.profile_combo.clear()
        self.profile_combo.addItem("-- Seleccionar Perfil --")
        
        profiles = self.profile_manager.get_profiles(self.current_folder)
        for profile in profiles:
            self.profile_combo.addItem(profile["name"])
    
    def load_profile(self, index):
        if index <= 0:  # Skip the "Select Profile" item
            return
        
        profiles = self.profile_manager.get_profiles(self.current_folder)
        profile_index = index - 1  # Adjust for the "Select Profile" item
        
        if profile_index < len(profiles):
            profile = profiles[profile_index]
            self.ilo_ip.setText(profile.get("ilo_ip", ""))
            self.ssh_user.setText(profile.get("ssh_user", ""))
            self.gateway_ip.setText(profile.get("gateway_ip", ""))
            self.ssh_port.setValue(profile.get("ssh_port", 22))
            self.local_ip.setText(profile.get("local_ip", "127.0.0.1"))
            self.key_path.setText(profile.get("key_path", "~/.ssh/id_rsa"))
            
            # Cargar puertos (ahora interno)
            self.port_data = profile.get("ports", {})
            if not self.port_data:
                # Establecer valores por defecto si no hay datos
                common_ports = [22, 23, 80, 443, 3389, 17988, 9300, 17990, 3002, 2198]
                for port in common_ports:
                    self.port_data[str(port)] = True
            
            self.settings.setValue("last_profile_index", index)
    
    def create_profile(self):
        folders = self.profile_manager.get_folders()
        dialog = ConnectionProfileDialog(self, folders=folders, current_folder=self.current_folder)
        if dialog.exec():
            profile_data = dialog.get_profile_data()
            selected_folder = dialog.get_selected_folder()
            self.profile_manager.add_profile(profile_data, selected_folder)
            
            # Actualizar la carpeta actual si cambió
            if selected_folder != self.current_folder:
                self.current_folder = selected_folder
                self.folder_combo.setCurrentText(selected_folder)
                self.settings.setValue("last_folder", selected_folder)
            
            self.update_profiles_list()
            # Select the new profile
            self.profile_combo.setCurrentText(profile_data["name"])
    
    def edit_profile(self):
        index = self.profile_combo.currentIndex()
        if index <= 0:
            QMessageBox.warning(self, "Error", "Por favor, selecciona un perfil para editar.")
            return
        
        profile_index = index - 1  # Adjust for the "Select Profile" item
        profiles = self.profile_manager.get_profiles(self.current_folder)
        
        if profile_index < len(profiles):
            profile = profiles[profile_index]
            folders = self.profile_manager.get_folders()
            dialog = ConnectionProfileDialog(self, profile, folders, self.current_folder)
            
            if dialog.exec():
                updated_profile = dialog.get_profile_data()
                selected_folder = dialog.get_selected_folder()
                
                # Si la carpeta cambió, mover el perfil
                if selected_folder != self.current_folder:
                    # Añadir a la nueva carpeta
                    self.profile_manager.add_profile(updated_profile, selected_folder)
                    # Eliminar de la carpeta actual
                    self.profile_manager.delete_profile(self.current_folder, profile_index)
                    
                    # Actualizar a la nueva carpeta
                    self.current_folder = selected_folder
                    self.folder_combo.setCurrentText(selected_folder)
                    self.settings.setValue("last_folder", selected_folder)
                    self.update_profiles_list()
                else:
                    # Actualizar en la misma carpeta
                    self.profile_manager.update_profile(self.current_folder, profile_index, updated_profile)
                    self.update_profiles_list()
                
                # Reselect the edited profile
                self.profile_combo.setCurrentText(updated_profile["name"])
    
    def delete_profile(self):
        index = self.profile_combo.currentIndex()
        if index <= 0:
            QMessageBox.warning(self, "Error", "Por favor, selecciona un perfil para eliminar.")
            return
        
        profile_index = index - 1  # Adjust for the "Select Profile" item
        profiles = self.profile_manager.get_profiles(self.current_folder)
        
        if profile_index < len(profiles):
            profile_name = profiles[profile_index]["name"]
            confirm = QMessageBox.question(
                self, "Confirmar eliminación",
                f"¿Estás seguro de que deseas eliminar el perfil '{profile_name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if confirm == QMessageBox.StandardButton.Yes:
                self.profile_manager.delete_profile(self.current_folder, profile_index)
                self.update_profiles_list()
                self.profile_combo.setCurrentIndex(0)
    
    def save_as_profile(self):
        # Validate inputs
        if not self.validateInputs():
            return
        
        # Get current configuration
        profile_data = {
            "ilo_ip": self.ilo_ip.text(),
            "ssh_user": self.ssh_user.text(),
            "gateway_ip": self.gateway_ip.text(),
            "ssh_port": self.ssh_port.value(),
            "local_ip": self.local_ip.text(),
            "key_path": self.key_path.text(),
            "ports": {}
        }
        
        # Ask for profile name
        name, ok = QInputDialog.getText(
            self, "Guardar perfil", "Nombre del perfil:"
        )
        
        if ok and name:
            profile_data["name"] = name
            self.profile_manager.add_profile(profile_data)
            self.update_profiles_list()
            # Select the new profile
            self.profile_combo.setCurrentText(name)
            QMessageBox.information(self, "Perfil guardado",
                                  f"El perfil '{name}' ha sido guardado correctamente.")
    
    def profile_selected(self, row):
        if row >= 0:
            # Adjust for the "Select Profile" item in the combo
            self.profile_combo.setCurrentIndex(row + 1)
    
    def clone_profile(self):
        row = self.profiles_list.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Por favor, selecciona un perfil para clonar.")
            return
        
        profiles = self.profile_manager.get_profiles()
        if row < len(profiles):
            profile = profiles[row].copy()
            name, ok = QInputDialog.getText(
                self, "Clonar perfil", 
                "Nombre del nuevo perfil:",
                text=f"{profile['name']} (copia)"
            )
            
            if ok and name:
                profile["name"] = name
                self.profile_manager.add_profile(profile)
                self.update_profiles_list()
                # Select the new profile
                self.profile_combo.setCurrentText(name)
    
    def import_profiles(self):
        # This would typically use a file dialog
        # For simplicity, we'll use a text input for JSON
        import_json, ok = QInputDialog.getMultiLineText(
            self, "Importar perfiles", 
            "Pega el JSON con los perfiles a importar:"
        )
        
        if ok and import_json:
            try:
                imported_profiles = json.loads(import_json)
                
                if not isinstance(imported_profiles, list):
                    raise ValueError("El formato de importación debe ser una lista de perfiles")
                
                for profile in imported_profiles:
                    if not isinstance(profile, dict) or "name" not in profile:
                        raise ValueError("Cada perfil debe ser un objeto con al menos un campo 'name'")
                
                current_profiles = self.profile_manager.get_profiles()
                current_profiles.extend(imported_profiles)
                self.profile_manager.save_profiles(current_profiles)
                self.update_profiles_list()
                
                QMessageBox.information(
                    self, "Importación completada",
                    f"Se importaron {len(imported_profiles)} perfiles correctamente."
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Error de importación",
                    f"No se pudieron importar los perfiles: {str(e)}"
                )
    
    def export_profiles(self):
        profiles = self.profile_manager.get_profiles()
        if not profiles:
            QMessageBox.warning(self, "Exportar perfiles", "No hay perfiles para exportar.")
            return
        
        export_json = json.dumps(profiles, indent=2)
        
        # Display the JSON for copying
        export_dialog = QDialog(self)
        export_dialog.setWindowTitle("Exportar perfiles")
        export_dialog.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(export_dialog)
        layout.addWidget(QLabel("Copia el siguiente JSON:"))
        
        text_edit = QTextEdit()
        text_edit.setPlainText(export_json)
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)
        
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(export_dialog.reject)
        layout.addWidget(button_box)
        
        export_dialog.exec()
    
    def startTunnel(self):
        if not self.validateInputs():
            return
        
        # Prepare port mappings
        port_mappings = []
        for port, checkbox in self.port_checkboxes.items():
            if checkbox.isChecked():
                mapping = f"{self.local_ip.text()}:{port}:{self.ilo_ip.text()}:{port}"
                port_mappings.append(mapping)
        
        # Start tunnel using SSH manager
        self.ssh_manager.create_tunnel(
            self.key_path.text(),
            self.ssh_port.value(),
            port_mappings,
            self.ssh_user.text(),
            self.gateway_ip.text()
        )
        
        self.connect_button.setEnabled(False)
        self.disconnect_button.setEnabled(True)
    
    def stopTunnel(self):
        if self.ssh_manager.stop_tunnel():
            self.console.append("Túnel cerrado.\n")
        
        self.connect_button.setEnabled(True)
        self.disconnect_button.setEnabled(False)
    
    def onSshOutput(self, data):
        self.console.append(data)
    
    def onSshError(self, data):
        self.console.append(data)
    
    def onProcessFinished(self, exit_code):
        self.connect_button.setEnabled(True)
        self.disconnect_button.setEnabled(False)
        self.console.append(f"Proceso finalizado con código {exit_code}\n")
    
    def validateInputs(self):
        if not self.ilo_ip.text():
            QMessageBox.warning(self, "Error", "La IP de ILO es obligatoria.")
            return False
        
        if not self.ssh_user.text():
            QMessageBox.warning(self, "Error", "El usuario SSH es obligatorio.")
            return False
        
        if not self.gateway_ip.text():
            QMessageBox.warning(self, "Error", "La IP del gateway es obligatoria.")
            return False
        
        return True
    
    def openBrowser(self):
        url = f"https://{self.local_ip.text()}"
        self.console.append(f"Abriendo navegador en {url}\n")
        webbrowser.open(url)
    
    def getHomePath(self):
        return os.path.expanduser("~")


def main():
    app = QApplication(sys.argv)
    window = ILOTunnelApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()