# ilo_tunnel/gui/main_window.py
import webbrowser

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QFont
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from ..app_settings import AppSettings
from ..controllers.connection_controller import ConnectionController
from ..models.profile import ConnectionProfile
from ..models.profile_manager import ProfileManager
from .dialogs import ConnectionProfileDialog, FolderManagementDialog
from .settings_dialog import SettingsDialog
from .widgets import (
    ConnectionFormWidget,
    ConnectionStatusBar,
    ConsolePanel,
    ProfileSidebar,
)


class ILOTunnelApp(QMainWindow):
    """Ventana principal: ensambla sidebar de perfiles, formulario y consola.

    Toda la lógica de negocio vive en ConnectionController; la persistencia en
    ProfileManager / AppSettings. Esta clase solo cablea la UI.
    """

    def __init__(self):
        super().__init__()
        self.app_settings = AppSettings()
        self.profile_manager = ProfileManager()
        self.controller = ConnectionController(self.app_settings, self)
        self.current_folder = None
        self.current_profile_name = None

        self._build_ui()
        self._wire_controller()
        self._restore_session()

        self.console.append_output(
            "ILO Tunnel Manager iniciado. Selecciona o crea un perfil."
        )
        self.statusBar().showMessage("Listo", 5000)

    # ----------------------------------------------------------------- UI
    def _build_ui(self) -> None:
        self.setWindowTitle("ILO Tunnel Manager")
        self.setMinimumSize(900, 600)
        self._build_toolbar()

        # Sidebar de perfiles (fuente única de gestión)
        self.sidebar = ProfileSidebar(self.profile_manager)
        self.sidebar.profileSelected.connect(self._on_profile_selected)
        self.sidebar.newProfileRequested.connect(self._on_new_profile)
        self.sidebar.editProfileRequested.connect(self._on_edit_profile)
        self.sidebar.deleteProfileRequested.connect(self._on_delete_profile)
        self.sidebar.manageFoldersRequested.connect(self._on_manage_folders)

        # Formulario del perfil seleccionado
        self.form = ConnectionFormWidget(include_name=False, show_port_status=True)
        self.form.set_local_ip_options(self.controller.local_ip_addresses())
        form_scroll = QScrollArea()
        form_scroll.setWidgetResizable(True)
        form_scroll.setWidget(self.form)

        header = QHBoxLayout()
        self.profile_title = QLabel("(sin perfil seleccionado)")
        title_font = QFont()
        title_font.setBold(True)
        self.profile_title.setFont(title_font)
        self.save_btn = QPushButton("Guardar cambios")
        self.save_btn.clicked.connect(self._on_save_changes)
        header.addWidget(self.profile_title)
        header.addStretch()
        header.addWidget(self.save_btn)

        right_top = QWidget()
        rt_layout = QVBoxLayout(right_top)
        rt_layout.setContentsMargins(0, 0, 0, 0)
        rt_layout.addLayout(header)
        rt_layout.addWidget(form_scroll)

        # Consola
        self.console = ConsolePanel()
        self.console.set_font_size(self.app_settings.get("console_font_size"))
        self.console.set_auto_scroll(self.app_settings.get("auto_scroll"))

        right_split = QSplitter(Qt.Orientation.Vertical)
        right_split.addWidget(right_top)
        right_split.addWidget(self.console)
        right_split.setStretchFactor(0, 3)
        right_split.setStretchFactor(1, 1)

        main_split = QSplitter(Qt.Orientation.Horizontal)
        main_split.addWidget(self.sidebar)
        main_split.addWidget(right_split)
        main_split.setStretchFactor(0, 0)
        main_split.setStretchFactor(1, 1)
        main_split.setSizes([260, 640])
        self.setCentralWidget(main_split)

        self.status_widget = ConnectionStatusBar()
        self.statusBar().addPermanentWidget(self.status_widget)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Principal")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        self.connect_action = QAction("Conectar", self)
        self.connect_action.triggered.connect(self._on_connect)
        toolbar.addAction(self.connect_action)

        self.disconnect_action = QAction("Desconectar", self)
        self.disconnect_action.setEnabled(False)
        self.disconnect_action.triggered.connect(self._on_disconnect)
        toolbar.addAction(self.disconnect_action)

        self.browser_action = QAction("Abrir navegador", self)
        self.browser_action.triggered.connect(self._on_open_browser)
        toolbar.addAction(self.browser_action)

        toolbar.addSeparator()
        settings_action = QAction("Ajustes", self)
        settings_action.triggered.connect(self._on_settings)
        toolbar.addAction(settings_action)

    def _wire_controller(self) -> None:
        self.controller.output.connect(self.console.append_output)
        self.controller.error.connect(self.console.append_error)
        self.controller.connection_changed.connect(self._on_connection_changed)
        self.controller.finished.connect(self._on_finished)
        self.controller.port_status.connect(self._on_port_status)

    def _restore_session(self) -> None:
        last_folder = self.app_settings.get("last_folder")
        last_profile = self.app_settings.get("last_profile")
        if last_profile:
            self.sidebar.select_profile(last_folder, last_profile)

    # --------------------------------------------------------- perfiles
    def _on_profile_selected(self, folder: str, name: str) -> None:
        profile, _f, _idx = self.profile_manager.get_profile_by_name(name, folder)
        if profile is None:
            return
        self.current_folder = folder
        self.current_profile_name = name
        self.form.set_data(profile.to_dict())
        self.profile_title.setText(f"{folder} / {name}")
        self.app_settings.set("last_folder", folder)
        self.app_settings.set("last_profile", name)

    def _on_save_changes(self) -> None:
        if self.current_profile_name is None:
            QMessageBox.information(
                self, "Sin perfil", "Selecciona un perfil para guardar los cambios."
            )
            return
        ok, msg = self.form.validate()
        if not ok:
            QMessageBox.warning(self, "Datos incompletos", msg)
            return
        data = self.form.get_data()
        data["name"] = self.current_profile_name
        profile = ConnectionProfile.from_dict(data)
        _p, folder, idx = self.profile_manager.get_profile_by_name(
            self.current_profile_name, self.current_folder
        )
        if idx >= 0 and self.profile_manager.update_profile(folder, idx, profile):
            self.statusBar().showMessage("Perfil guardado", 3000)
            self.sidebar.refresh(select=(folder, self.current_profile_name))
        else:
            QMessageBox.warning(self, "Error", "No se pudo guardar el perfil.")

    def _on_new_profile(self) -> None:
        dialog = ConnectionProfileDialog(
            self,
            folders=self.profile_manager.get_folders(),
            current_folder=self.current_folder or "DEFAULT",
        )
        if dialog.exec():
            profile = ConnectionProfile.from_dict(dialog.get_profile_data())
            folder = dialog.get_selected_folder()
            if self.profile_manager.add_profile(profile, folder):
                self.sidebar.refresh(select=(folder, profile.name))
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    "No se pudo crear el perfil (¿nombre duplicado o inválido?).",
                )

    def _on_edit_profile(self, folder: str, name: str) -> None:
        profile, _f, idx = self.profile_manager.get_profile_by_name(name, folder)
        if profile is None:
            return
        dialog = ConnectionProfileDialog(
            self,
            profile_data=profile.to_dict(),
            folders=self.profile_manager.get_folders(),
            current_folder=folder,
        )
        if not dialog.exec():
            return
        # Fusionar para conservar campos que el diálogo no edita
        merged = profile.to_dict()
        merged.update(dialog.get_profile_data())
        new_profile = ConnectionProfile.from_dict(merged)
        new_folder = dialog.get_selected_folder()
        if new_folder != folder:
            self.profile_manager.delete_profile(folder, idx)
            self.profile_manager.add_profile(new_profile, new_folder)
        else:
            self.profile_manager.update_profile(folder, idx, new_profile)
        self.sidebar.refresh(select=(new_folder, new_profile.name))

    def _on_delete_profile(self, folder: str, name: str) -> None:
        confirm = QMessageBox.question(
            self,
            "Eliminar perfil",
            f"¿Eliminar el perfil '{name}' de la carpeta '{folder}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        _p, f, idx = self.profile_manager.get_profile_by_name(name, folder)
        if idx >= 0 and self.profile_manager.delete_profile(f, idx):
            if self.current_profile_name == name:
                self.current_profile_name = None
                self.profile_title.setText("(sin perfil seleccionado)")
            self.sidebar.refresh()

    def _on_manage_folders(self) -> None:
        dialog = FolderManagementDialog(self, self.profile_manager)
        dialog.exec()
        self.sidebar.refresh()

    # ----------------------------------------------------------- conexión
    def _current_profile_from_form(self) -> ConnectionProfile:
        data = self.form.get_data()
        data["name"] = self.current_profile_name or "temporal"
        return ConnectionProfile.from_dict(data)

    def _on_connect(self) -> None:
        ok, msg = self.form.validate()
        if not ok:
            QMessageBox.warning(self, "Datos incompletos", msg)
            return
        profile = self._current_profile_from_form()
        for port in self.form.port_selector.selected_ports():
            self.form.port_selector.set_port_status(port, "connecting")
        if self.controller.start(profile):
            self._set_connected_ui(True)
            self.statusBar().showMessage("Conectando…", 5000)
        else:
            self.form.port_selector.reset_status()
            QMessageBox.critical(
                self,
                "Error de conexión",
                "No se pudo iniciar el túnel SSH. Revisa la configuración y los permisos.",
            )

    def _on_disconnect(self) -> None:
        if self.controller.stop():
            self.console.append_output("Túnel cerrado correctamente.")
            self._set_connected_ui(False)
            self.form.port_selector.reset_status()
            self.status_widget.setStatus("disconnected", "Desconectado")

    def _set_connected_ui(self, connected: bool) -> None:
        self.connect_action.setEnabled(not connected)
        self.disconnect_action.setEnabled(connected)
        self.save_btn.setEnabled(not connected)
        self.form.setEnabled(not connected)

    def _on_connection_changed(self, connected: bool, message: str) -> None:
        self.statusBar().showMessage(message, 5000)
        if connected:
            self.status_widget.setStatus("connected", message)
        elif "Error" in message or "error" in message:
            self.status_widget.setStatus("error", message)
        else:
            self.status_widget.setStatus("disconnected", message)

    def _on_finished(self, exit_code: int, status_msg: str) -> None:
        self.console.append_output(
            f"Proceso finalizado: {status_msg} (código {exit_code})"
        )
        self._set_connected_ui(False)
        self.form.port_selector.reset_status()
        self.status_widget.setStatus("disconnected", "Desconectado")

    def _on_port_status(self, port: int, is_open: bool) -> None:
        self.form.port_selector.set_port_status(
            port, "connected" if is_open else "error"
        )

    def _on_open_browser(self) -> None:
        local_ip = self.form.local_ip.currentText()
        selected = self.form.port_selector.selected_ports()
        if 443 in selected:
            url = f"https://{local_ip}"
        elif 80 in selected:
            url = f"http://{local_ip}"
        else:
            url = f"https://{local_ip}"
        try:
            self.console.append_output(f"Abriendo navegador en {url}")
            webbrowser.open(url)
        except OSError as exc:
            self.console.append_error(f"Error al abrir el navegador: {exc}")

    # ------------------------------------------------------------ ajustes
    def _on_settings(self) -> None:
        dialog = SettingsDialog(self.app_settings, self)
        dialog.exec()
        # Reaplicar ajustes que afectan a la UI (pueden haber cambiado los tipos
        # de servidor incluso si se cerró sin "OK")
        self.console.set_font_size(self.app_settings.get("console_font_size"))
        self.console.set_auto_scroll(self.app_settings.get("auto_scroll"))
        self.form.refresh_server_types()

    # -------------------------------------------------------------- cierre
    def closeEvent(self, event) -> None:
        if self.controller.is_connected():
            if self.app_settings.get("confirm_exit"):
                confirm = QMessageBox.question(
                    self,
                    "Confirmar salida",
                    "Hay una conexión activa. ¿Deseas cerrarla y salir?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if confirm != QMessageBox.StandardButton.Yes:
                    event.ignore()
                    return
            self.controller.stop()
        self.controller.shutdown()
        super().closeEvent(event)
