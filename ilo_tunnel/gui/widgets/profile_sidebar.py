# ilo_tunnel/gui/widgets/profile_sidebar.py
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..theme import Palette, icon

# Roles para distinguir carpetas de perfiles en el árbol
_FOLDER_ROLE = Qt.ItemDataRole.UserRole + 1
_PROFILE_ROLE = Qt.ItemDataRole.UserRole + 2


class ProfileSidebar(QWidget):
    """Árbol único de carpetas + perfiles con todo el CRUD.

    Sustituye las tres UIs de gestión de perfiles dispersas (pestaña Conexión,
    pestaña Perfiles y toolbar) por un único punto de entrada.
    """

    profileSelected = pyqtSignal(str, str)  # carpeta, nombre
    newProfileRequested = pyqtSignal()
    editProfileRequested = pyqtSignal(str, str)  # carpeta, nombre
    deleteProfileRequested = pyqtSignal(str, str)  # carpeta, nombre
    manageFoldersRequested = pyqtSignal()

    def __init__(self, profile_manager, parent=None):
        super().__init__(parent)
        self.profile_manager = profile_manager
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 16, 8, 8)
        root.setSpacing(10)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar perfil…")
        self.search.setClearButtonEnabled(True)
        self.search.addAction(
            icon("mdi6.magnify", Palette.TEXT_MUTED),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        self.search.textChanged.connect(self._apply_filter)
        root.addWidget(self.search)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(14)
        self.tree.currentItemChanged.connect(self._on_current_changed)
        self.tree.itemDoubleClicked.connect(self._on_double_click)
        root.addWidget(self.tree)

        actions = QHBoxLayout()
        actions.setSpacing(6)
        self._new_btn = self._icon_button("mdi6.plus", "Nuevo perfil")
        self._new_btn.clicked.connect(self.newProfileRequested)
        self._edit_btn = self._icon_button("mdi6.pencil-outline", "Editar perfil")
        self._edit_btn.clicked.connect(self._emit_edit)
        self._del_btn = self._icon_button("mdi6.trash-can-outline", "Eliminar perfil")
        self._del_btn.clicked.connect(self._emit_delete)
        folders_btn = QPushButton(icon("mdi6.folder-outline", Palette.TEXT), " Carpetas")
        folders_btn.setToolTip("Gestionar carpetas")
        folders_btn.clicked.connect(self.manageFoldersRequested)
        actions.addWidget(self._new_btn)
        actions.addWidget(self._edit_btn)
        actions.addWidget(self._del_btn)
        actions.addStretch()
        actions.addWidget(folders_btn)
        root.addLayout(actions)

    @staticmethod
    def _icon_button(icon_name: str, tooltip: str) -> QPushButton:
        """Crea un botón-icono uniforme para la gestión de perfiles."""
        btn = QPushButton(icon(icon_name, Palette.TEXT), "")
        btn.setObjectName("iconButton")
        btn.setToolTip(tooltip)
        return btn

    # --------------------------------------------------------------- datos
    def refresh(self, select: Optional[tuple] = None) -> None:
        """Reconstruye el árbol desde el ProfileManager.

        Args:
            select: tupla (carpeta, nombre) a seleccionar tras refrescar.
        """
        self.tree.blockSignals(True)
        self.tree.clear()
        profiles_data = self.profile_manager.get_profiles()
        for folder in sorted(profiles_data.keys()):
            folder_item = QTreeWidgetItem([folder])
            folder_item.setData(0, _FOLDER_ROLE, folder)
            folder_item.setFlags(folder_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.tree.addTopLevelItem(folder_item)
            for profile in profiles_data[folder]:
                name = profile.get("name", "")
                child = QTreeWidgetItem([name])
                child.setData(0, _FOLDER_ROLE, folder)
                child.setData(0, _PROFILE_ROLE, name)
                folder_item.addChild(child)
            folder_item.setExpanded(True)
        self.tree.blockSignals(False)

        if select is not None:
            self.select_profile(*select)
        self._apply_filter(self.search.text())

    def select_profile(self, folder: str, name: str) -> None:
        """Selecciona el perfil (carpeta, nombre) si existe."""
        for i in range(self.tree.topLevelItemCount()):
            folder_item = self.tree.topLevelItem(i)
            if folder_item.data(0, _FOLDER_ROLE) != folder:
                continue
            for j in range(folder_item.childCount()):
                child = folder_item.child(j)
                if child.data(0, _PROFILE_ROLE) == name:
                    self.tree.setCurrentItem(child)
                    return

    def current_selection(self) -> Optional[tuple]:
        """Devuelve (carpeta, nombre) del perfil seleccionado, o None."""
        item = self.tree.currentItem()
        if item is None:
            return None
        name = item.data(0, _PROFILE_ROLE)
        if name is None:
            return None
        return item.data(0, _FOLDER_ROLE), name

    # ------------------------------------------------------------ handlers
    def _on_current_changed(self, current, _previous) -> None:
        if current is None:
            return
        name = current.data(0, _PROFILE_ROLE)
        if name is not None:
            self.profileSelected.emit(current.data(0, _FOLDER_ROLE), name)

    def _on_double_click(self, item, _column) -> None:
        name = item.data(0, _PROFILE_ROLE)
        if name is not None:
            self.editProfileRequested.emit(item.data(0, _FOLDER_ROLE), name)

    def _emit_edit(self) -> None:
        sel = self.current_selection()
        if sel is not None:
            self.editProfileRequested.emit(*sel)

    def _emit_delete(self) -> None:
        sel = self.current_selection()
        if sel is not None:
            self.deleteProfileRequested.emit(*sel)

    def _apply_filter(self, text: str) -> None:
        text = (text or "").lower().strip()
        for i in range(self.tree.topLevelItemCount()):
            folder_item = self.tree.topLevelItem(i)
            visible_children = 0
            for j in range(folder_item.childCount()):
                child = folder_item.child(j)
                match = text in child.text(0).lower()
                child.setHidden(not match)
                visible_children += int(match)
            # Ocultar carpetas vacías al filtrar
            folder_item.setHidden(bool(text) and visible_children == 0)
