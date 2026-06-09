# ilo_tunnel/gui/dialogs.py
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
)

from .widgets import ConnectionFormWidget


class ConnectionProfileDialog(QDialog):
    """Diálogo para crear o editar perfiles de conexión.

    Reutiliza ConnectionFormWidget (el mismo editor de la ventana principal), de
    modo que no hay formulario ni grid de puertos duplicados.
    """

    def __init__(
        self, parent=None, profile_data=None, folders=None, current_folder="DEFAULT"
    ):
        super().__init__(parent)
        self.profile_data = profile_data or {}
        self.folders = folders or ["DEFAULT"]
        self.current_folder = current_folder

        self.setWindowTitle("Perfil de Conexión")
        self.setMinimumWidth(500)
        self.setMinimumHeight(560)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        folder_form = QFormLayout()
        self.folder_combo = QComboBox()
        self.folder_combo.addItems(self.folders)
        if self.current_folder in self.folders:
            self.folder_combo.setCurrentText(self.current_folder)
        folder_form.addRow("Carpeta:", self.folder_combo)
        layout.addLayout(folder_form)

        self.form = ConnectionFormWidget(include_name=True)
        if self.profile_data:
            self.form.set_data(self.profile_data)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.form)
        layout.addWidget(scroll)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_profile_data(self) -> dict:
        """Devuelve los datos del perfil del formulario."""
        return self.form.get_data()

    def get_selected_folder(self) -> str:
        """Devuelve la carpeta seleccionada."""
        return self.folder_combo.currentText()

    def accept(self) -> None:
        """Valida antes de aceptar."""
        ok, msg = self.form.validate()
        if not ok:
            QMessageBox.warning(self, "Datos incompletos", msg)
            return
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
