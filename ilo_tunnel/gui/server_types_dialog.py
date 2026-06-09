# ilo_tunnel/gui/server_types_dialog.py
from typing import Dict, List, Optional, Tuple

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)

from ..models.server_types import (
    delete_user_server_type,
    get_server_description,
    get_server_essential_ports,
    get_server_ports,
    is_builtin,
    save_user_server_type,
)


def _parse_ports(text: str) -> Dict[int, str]:
    """Parsea líneas ``puerto=Nombre`` (o solo ``puerto``) a {int: str}."""
    ports: Dict[int, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if "=" in line:
            num, name = line.split("=", 1)
        else:
            num, name = line, ""
        try:
            ports[int(num.strip())] = name.strip()
        except ValueError:
            continue
    return ports


def _parse_essential(text: str) -> List[int]:
    result = []
    for token in text.replace(";", ",").split(","):
        token = token.strip()
        if not token:
            continue
        try:
            result.append(int(token))
        except ValueError:
            continue
    return result or [22, 80, 443]


class ServerTypeEditDialog(QDialog):
    """Editor de un tipo de servidor definido por el usuario."""

    def __init__(self, parent=None, name: str = "", editing: bool = False):
        super().__init__(parent)
        self.setWindowTitle("Tipo de servidor")
        self.setMinimumWidth(420)
        self._editing = editing
        self._build_ui()
        if name:
            self.name_edit.setText(name)
            self.name_edit.setReadOnly(editing)
            self.desc_edit.setText(get_server_description(name))
            ports = get_server_ports(name)
            self.ports_edit.setPlainText(
                "\n".join(f"{p}={n}" if n else str(p) for p, n in sorted(ports.items()))
            )
            self.essential_edit.setText(
                ", ".join(str(p) for p in get_server_essential_ports(name))
            )

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.name_edit = QLineEdit()
        form.addRow("Nombre:", self.name_edit)
        self.desc_edit = QLineEdit()
        form.addRow("Descripción:", self.desc_edit)
        layout.addLayout(form)

        layout.addWidget(
            QLabel("Puertos (una línea por puerto, formato 'puerto=Nombre'):")
        )
        self.ports_edit = QPlainTextEdit()
        self.ports_edit.setPlaceholderText("22=SSH\n443=HTTPS\n8080=Web")
        layout.addWidget(self.ports_edit)

        ess_form = QFormLayout()
        self.essential_edit = QLineEdit("22, 80, 443")
        self.essential_edit.setToolTip("Puertos a monitorear, separados por comas.")
        ess_form.addRow("Puertos esenciales:", self.essential_edit)
        layout.addLayout(ess_form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self) -> Tuple[str, Dict[int, str], str, List[int]]:
        return (
            self.name_edit.text().strip(),
            _parse_ports(self.ports_edit.toPlainText()),
            self.desc_edit.text().strip(),
            _parse_essential(self.essential_edit.text()),
        )

    def accept(self) -> None:
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "El nombre es obligatorio.")
            return
        if not self._editing and is_builtin(name):
            QMessageBox.warning(
                self, "Error", "Ese nombre coincide con un tipo predefinido."
            )
            return
        if not _parse_ports(self.ports_edit.toPlainText()):
            QMessageBox.warning(self, "Error", "Define al menos un puerto válido.")
            return
        super().accept()


class ServerTypesDialog(QDialog):
    """Gestiona los tipos de servidor definidos por el usuario."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tipos de servidor")
        self.setMinimumSize(420, 340)
        self._build_ui()
        self._refresh()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Tipos definidos por el usuario:"))
        self.list = QListWidget()
        layout.addWidget(self.list)

        actions = QHBoxLayout()
        add_btn = QPushButton("Añadir")
        add_btn.clicked.connect(self._add)
        edit_btn = QPushButton("Editar")
        edit_btn.clicked.connect(self._edit)
        del_btn = QPushButton("Eliminar")
        del_btn.clicked.connect(self._delete)
        actions.addWidget(add_btn)
        actions.addWidget(edit_btn)
        actions.addWidget(del_btn)
        actions.addStretch()
        layout.addLayout(actions)

        info = QLabel(
            "Los tipos predefinidos (HP/Huawei, Dell, …) no se muestran aquí porque "
            "no pueden modificarse."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

    def _refresh(self) -> None:
        from ..models.server_types import _load_user_types

        self.list.clear()
        self.list.addItems(sorted(_load_user_types().keys()))

    def _selected(self) -> Optional[str]:
        item = self.list.currentItem()
        return item.text() if item else None

    def _add(self) -> None:
        dialog = ServerTypeEditDialog(self, editing=False)
        if dialog.exec():
            name, ports, desc, essential = dialog.values()
            save_user_server_type(name, ports, desc, essential)
            self._refresh()

    def _edit(self) -> None:
        name = self._selected()
        if not name:
            return
        dialog = ServerTypeEditDialog(self, name=name, editing=True)
        if dialog.exec():
            new_name, ports, desc, essential = dialog.values()
            save_user_server_type(new_name, ports, desc, essential)
            self._refresh()

    def _delete(self) -> None:
        name = self._selected()
        if not name:
            return
        if delete_user_server_type(name):
            self._refresh()
