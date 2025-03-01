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

class ConnectionProfileDialog(QDialog):
    def __init__(self, parent=None, profile_data=None):
        super().__init__(parent)
        self.profile_data = profile_data or {}
        self.setWindowTitle("Perfil de Conexión")
        self.setMinimumWidth(400)
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
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
        
        # Ports to tunnel
        ports_group = QWidget()
        ports_layout = QGridLayout(ports_group)
        
        # Define common ILO ports
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
            "ILO (2198)": 2198
        }
        
        saved_ports = self.profile_data.get("ports", {})
        
        row, col = 0, 0
        for name, port in common_ports.items():
            checkbox = QCheckBox(name)
            # If profile data exists, use saved port state, otherwise default to True
            is_checked = saved_ports.get(str(port), True)
            checkbox.setChecked(is_checked)
            checkbox.port = port
            self.port_checkboxes[port] = checkbox
            ports_layout.addWidget(checkbox, row, col)
            col += 1
            if col > 2:
                col = 0
                row += 1
        
        layout.addWidget(QLabel("Puertos a tunelizar:"))
        layout.addWidget(ports_group)
        
        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_profile_data(self):
        # Collect all profile data
        ports_data = {}
        for port, checkbox in self.port_checkboxes.items():
            ports_data[str(port)] = checkbox.isChecked()
            
        return {
            "name": self.profile_name.text(),
            "ilo_ip": self.ilo_ip.text(),
            "ssh_user": self.ssh_user.text(),
            "gateway_ip": self.gateway_ip.text(),
            "ssh_port": self.ssh_port.value(),
            "local_ip": self.local_ip.text(),
            "key_path": self.key_path.text(),
            "ports": ports_data
        }
    
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
        self.settings = QSettings("ILOTunnel.1", "ILOTunnelApp")
        
    def get_profiles(self):
        profiles_json = self.settings.value("connection_profiles", "[]")
        try:
            return json.loads(profiles_json)
        except:
            return []
    
    def save_profiles(self, profiles):
        self.settings.setValue("connection_profiles", json.dumps(profiles))
    
    def add_profile(self, profile_data):
        profiles = self.get_profiles()
        profiles.append(profile_data)
        self.save_profiles(profiles)
    
    def update_profile(self, index, profile_data):
        profiles = self.get_profiles()
        if 0 <= index < len(profiles):
            profiles[index] = profile_data
            self.save_profiles(profiles)
    
    def delete_profile(self, index):
        profiles = self.get_profiles()
        if 0 <= index < len(profiles):
            del profiles[index]
            self.save_profiles(profiles)
    
    def get_profile_names(self):
        return [profile["name"] for profile in self.get_profiles()]


class ILOTunnelApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.process = None
        self.settings = QSettings("ILOTunnel.1", "ILOTunnelApp")
        self.profile_manager = ProfileManager()
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
        
        # Ports to tunnel
        ports_group = QWidget()
        ports_layout = QGridLayout(ports_group)
        
        # Define common ILO ports
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
            "ILO (2198)": 2198
        }
        
        row, col = 0, 0
        for name, port in common_ports.items():
            checkbox = QCheckBox(name)
            checkbox.setChecked(True)
            checkbox.port = port
            self.port_checkboxes[port] = checkbox
            ports_layout.addWidget(checkbox, row, col)
            col += 1
            if col > 2:
                col = 0
                row += 1
                
        connection_layout.addWidget(QLabel("Puertos a tunelizar:"))
        connection_layout.addWidget(ports_group)
        
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
        
        # Help tab
        help_tab = QWidget()
        help_layout = QVBoxLayout(help_tab)
        
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setHtml("""
        <h2>HP ProLiant ILO Tunnel Manager</h2>
        <p>Esta aplicación permite crear túneles SSH para acceder a interfaces ILO de servidores HP ProLiant.</p>
        
        <h3>Instrucciones:</h3>
        <ol>
            <li>Selecciona un perfil existente o crea uno nuevo.</li>
            <li>Introduce la dirección IP de la interfaz ILO a la que quieres conectarte.</li>
            <li>Introduce el usuario SSH para acceder al gateway.</li>
            <li>Introduce la dirección IP del gateway SSH.</li>
            <li>Ajusta el puerto SSH si es necesario (por defecto es 22).</li>
            <li>La IP local por defecto es 127.0.0.1, pero puedes cambiarla si lo necesitas.</li>
            <li>Indica la ruta a tu clave SSH privada.</li>
            <li>Marca los puertos que quieras tunelizar.</li>
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
        
        <p><b>Nota:</b> Esta aplicación requiere permisos de administrador para crear los túneles.</p>
        """)
        
        help_layout.addWidget(help_text)
        tabs.addTab(help_tab, "Ayuda")
        
        # Manage profiles tab
        profiles_tab = QWidget()
        profiles_layout = QVBoxLayout(profiles_tab)
        
        self.profiles_list = QListWidget()
        self.profiles_list.currentRowChanged.connect(self.profile_selected)
        profiles_layout.addWidget(QLabel("Perfiles guardados:"))
        profiles_layout.addWidget(self.profiles_list)
        
        profiles_buttons = QHBoxLayout()
        
        clone_button = QPushButton("Clonar")
        clone_button.clicked.connect(self.clone_profile)
        profiles_buttons.addWidget(clone_button)
        
        import_button = QPushButton("Importar")
        import_button.clicked.connect(self.import_profiles)
        profiles_buttons.addWidget(import_button)
        
        export_button = QPushButton("Exportar")
        export_button.clicked.connect(self.export_profiles)
        profiles_buttons.addWidget(export_button)
        
        profiles_layout.addLayout(profiles_buttons)
        
        tabs.addTab(profiles_tab, "Perfiles")
        
        # Central widget
        self.setCentralWidget(central_widget)
        
        # Initialize SSH manager
        self.ssh_manager = SSHManager()
        self.ssh_manager.output_ready.connect(self.onSshOutput)
        self.ssh_manager.error_ready.connect(self.onSshError)
        self.ssh_manager.process_finished.connect(self.onProcessFinished)
        
    def loadSettings(self):
        # Load last used profile
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
            
            # Load checkbox states
            for port, checkbox in self.port_checkboxes.items():
                saved_state = self.settings.value(f"port_{port}", True)
                # Convert to bool as QSettings saves as string
                if isinstance(saved_state, str):
                    saved_state = saved_state.lower() == 'true'
                checkbox.setChecked(saved_state)
    
    def update_profiles_list(self):
        # Update both the combo box and list widget
        profiles = self.profile_manager.get_profiles()
        
        # Update combo box
        self.profile_combo.clear()
        self.profile_combo.addItem("-- Seleccionar Perfil --")
        for profile in profiles:
            self.profile_combo.addItem(profile["name"])
        
        # Update list widget
        self.profiles_list.clear()
        for profile in profiles:
            self.profiles_list.addItem(profile["name"])
    
    def load_profile(self, index):
        if index <= 0:  # Skip the "Select Profile" item
            return
        
        profiles = self.profile_manager.get_profiles()
        profile_index = index - 1  # Adjust for the "Select Profile" item
        
        if profile_index < len(profiles):
            profile = profiles[profile_index]
            self.ilo_ip.setText(profile.get("ilo_ip", ""))
            self.ssh_user.setText(profile.get("ssh_user", ""))
            self.gateway_ip.setText(profile.get("gateway_ip", ""))
            self.ssh_port.setValue(profile.get("ssh_port", 22))
            self.local_ip.setText(profile.get("local_ip", "127.0.0.1"))
            self.key_path.setText(profile.get("key_path", "~/.ssh/id_rsa"))
            
            # Load port states
            ports = profile.get("ports", {})
            for port, checkbox in self.port_checkboxes.items():
                # Default to True if not specified
                is_checked = ports.get(str(port), True)
                checkbox.setChecked(is_checked)
            
            self.settings.setValue("last_profile_index", index)
    
    def create_profile(self):
        dialog = ConnectionProfileDialog(self)
        if dialog.exec():
            profile_data = dialog.get_profile_data()
            self.profile_manager.add_profile(profile_data)
            self.update_profiles_list()
            # Select the new profile
            self.profile_combo.setCurrentText(profile_data["name"])
    
    def edit_profile(self):
        index = self.profile_combo.currentIndex()
        if index <= 0:
            QMessageBox.warning(self, "Error", "Por favor, selecciona un perfil para editar.")
            return
        
        profile_index = index - 1  # Adjust for the "Select Profile" item
        profiles = self.profile_manager.get_profiles()
        
        if profile_index < len(profiles):
            profile = profiles[profile_index]
            dialog = ConnectionProfileDialog(self, profile)
            
            if dialog.exec():
                updated_profile = dialog.get_profile_data()
                self.profile_manager.update_profile(profile_index, updated_profile)
                self.update_profiles_list()
                # Reselect the edited profile
                self.profile_combo.setCurrentText(updated_profile["name"])
    
    def delete_profile(self):
        index = self.profile_combo.currentIndex()
        if index <= 0:
            QMessageBox.warning(self, "Error", "Por favor, selecciona un perfil para eliminar.")
            return
        
        profile_index = index - 1  # Adjust for the "Select Profile" item
        profiles = self.profile_manager.get_profiles()
        
        if profile_index < len(profiles):
            profile_name = profiles[profile_index]["name"]
            confirm = QMessageBox.question(
                self, "Confirmar eliminación",
                f"¿Estás seguro de que deseas eliminar el perfil '{profile_name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if confirm == QMessageBox.StandardButton.Yes:
                self.profile_manager.delete_profile(profile_index)
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
        
        # Get port states
        for port, checkbox in self.port_checkboxes.items():
            profile_data["ports"][str(port)] = checkbox.isChecked()
        
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