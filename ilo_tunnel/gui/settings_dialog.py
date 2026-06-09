# ilo_tunnel/gui/settings_dialog.py
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)


class SettingsDialog(QDialog):
    """Diálogo de ajustes globales de la aplicación.

    Reúne en un único sitio los ajustes que antes estaban dispersos en la
    pestaña "Configuración". Las opciones de conexión SSH ya NO viven aquí:
    son por perfil y se editan en el formulario de conexión.
    """

    def __init__(self, app_settings, parent=None):
        super().__init__(parent)
        self.settings = app_settings
        self.setWindowTitle("Ajustes")
        self.setMinimumWidth(420)
        self._build_ui()
        self._load()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        general = QGroupBox("General")
        gen_form = QFormLayout(general)
        self.auto_start = QCheckBox("Iniciar automáticamente con el último perfil")
        self.minimize_to_tray = QCheckBox("Minimizar a la bandeja al cerrar")
        self.show_notifications = QCheckBox("Mostrar notificaciones")
        self.confirm_exit = QCheckBox("Confirmar al salir si hay conexión activa")
        for cb in (
            self.auto_start,
            self.minimize_to_tray,
            self.show_notifications,
            self.confirm_exit,
        ):
            gen_form.addRow("", cb)
        layout.addWidget(general)

        reconnect = QGroupBox("Reconexión")
        rec_form = QFormLayout(reconnect)
        self.auto_reconnect = QCheckBox(
            "Reconectar automáticamente al perder la conexión"
        )
        rec_form.addRow("", self.auto_reconnect)
        self.reconnect_attempts = QSpinBox()
        self.reconnect_attempts.setRange(1, 10)
        self.reconnect_attempts.setSuffix(" intentos")
        rec_form.addRow("Intentos de reconexión:", self.reconnect_attempts)
        layout.addWidget(reconnect)

        ui = QGroupBox("Interfaz")
        ui_form = QFormLayout(ui)
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 16)
        ui_form.addRow("Tamaño de fuente de la consola:", self.font_size)
        self.auto_scroll = QCheckBox("Auto-desplazar la consola")
        ui_form.addRow("", self.auto_scroll)
        layout.addWidget(ui)

        actions = QHBoxLayout()
        reset_btn = QPushButton("Restaurar predeterminados")
        reset_btn.clicked.connect(self._reset)
        server_types_btn = QPushButton("Gestionar tipos de servidor…")
        server_types_btn.clicked.connect(self._manage_server_types)
        actions.addWidget(reset_btn)
        actions.addWidget(server_types_btn)
        actions.addStretch()
        layout.addLayout(actions)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load(self) -> None:
        self.auto_start.setChecked(self.settings.get("auto_start"))
        self.minimize_to_tray.setChecked(self.settings.get("minimize_to_tray"))
        self.show_notifications.setChecked(self.settings.get("show_notifications"))
        self.confirm_exit.setChecked(self.settings.get("confirm_exit"))
        self.auto_reconnect.setChecked(self.settings.get("auto_reconnect"))
        self.reconnect_attempts.setValue(self.settings.get("reconnect_attempts"))
        self.font_size.setValue(self.settings.get("console_font_size"))
        self.auto_scroll.setChecked(self.settings.get("auto_scroll"))

    def _reset(self) -> None:
        self.settings.reset()
        self._load()

    def _manage_server_types(self) -> None:
        from .server_types_dialog import ServerTypesDialog

        ServerTypesDialog(self).exec()

    def _save_and_accept(self) -> None:
        self.settings.set("auto_start", self.auto_start.isChecked())
        self.settings.set("minimize_to_tray", self.minimize_to_tray.isChecked())
        self.settings.set("show_notifications", self.show_notifications.isChecked())
        self.settings.set("confirm_exit", self.confirm_exit.isChecked())
        self.settings.set("auto_reconnect", self.auto_reconnect.isChecked())
        self.settings.set("reconnect_attempts", self.reconnect_attempts.value())
        self.settings.set("console_font_size", self.font_size.value())
        self.settings.set("auto_scroll", self.auto_scroll.isChecked())
        self.accept()
