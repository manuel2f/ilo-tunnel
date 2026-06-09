# ilo_tunnel/gui/widgets/port_selector.py
from typing import Dict

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ...models.server_types import get_server_ports
from .status_widgets import PortStatusWidget

DEFAULT_PORTS = [22, 80, 443]
_COLUMNS = 4


class PortSelectorWidget(QWidget):
    """Selector de puertos a tunelizar, reutilizable en la ventana y en diálogos.

    Reemplaza los dos grids de checkboxes duplicados (main_window y dialogs) y
    añade soporte real para puertos personalizados (añadir/quitar).

    Args:
        show_status: si True, muestra un indicador de estado por puerto (vista en vivo).
    """

    portsChanged = pyqtSignal()

    def __init__(self, show_status: bool = False, parent=None):
        super().__init__(parent)
        self._show_status = show_status
        self._server_type = "HP/Huawei"
        self._checkboxes: Dict[int, QCheckBox] = {}
        self._status_widgets: Dict[int, PortStatusWidget] = {}
        # Puertos que no pertenecen al tipo de servidor actual (definidos por el usuario)
        self._custom: set = set()

        self._build_ui()
        self.load(self._server_type, {}, custom_ports=False)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        root.addWidget(QLabel("Puertos a tunelizar:"))

        self._grid = QGridLayout()
        self._grid.setVerticalSpacing(2)
        self._grid.setHorizontalSpacing(10)
        root.addLayout(self._grid)

        # Selección rápida
        quick = QHBoxLayout()
        btn_all = QPushButton("Seleccionar todos")
        btn_all.clicked.connect(self.select_all)
        btn_none = QPushButton("Deseleccionar todos")
        btn_none.clicked.connect(self.select_none)
        btn_def = QPushButton("Valores predeterminados")
        btn_def.clicked.connect(self.select_defaults)
        quick.addWidget(btn_all)
        quick.addWidget(btn_none)
        quick.addWidget(btn_def)
        root.addLayout(quick)

        # Añadir / quitar puerto personalizado
        custom = QHBoxLayout()
        custom.addWidget(QLabel("Puerto personalizado:"))
        self._custom_spin = QSpinBox()
        self._custom_spin.setRange(1, 65535)
        self._custom_spin.setValue(8080)
        custom.addWidget(self._custom_spin)
        btn_add = QPushButton("Añadir")
        btn_add.clicked.connect(self._on_add_custom)
        custom.addWidget(btn_add)
        btn_remove = QPushButton("Quitar")
        btn_remove.setToolTip(
            "Quita el puerto personalizado indicado (no los del tipo de servidor)"
        )
        btn_remove.clicked.connect(self._on_remove_custom)
        custom.addWidget(btn_remove)
        root.addLayout(custom)

    # ------------------------------------------------------------------ build
    def _port_label(self, port: int, names: Dict[int, str]) -> str:
        name = names.get(port)
        return f"{name} ({port})" if name else f"Puerto ({port})"

    def _rebuild_grid(self, checked: Dict[int, bool]) -> None:
        # Vaciar el grid
        while self._grid.count():
            item = self._grid.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        self._checkboxes.clear()
        self._status_widgets.clear()

        names = get_server_ports(self._server_type)
        all_ports = sorted(set(names) | self._custom)

        row = col = 0
        for port in all_ports:
            cell = QWidget()
            cell_layout = QHBoxLayout(cell)
            cell_layout.setContentsMargins(0, 0, 0, 0)
            cell_layout.setSpacing(4)

            checkbox = QCheckBox(self._port_label(port, names))
            checkbox.setChecked(checked.get(port, port in names))
            checkbox.setMaximumHeight(20)
            checkbox.toggled.connect(self.portsChanged)
            self._checkboxes[port] = checkbox
            cell_layout.addWidget(checkbox)

            if self._show_status:
                status = PortStatusWidget()
                self._status_widgets[port] = status
                cell_layout.addWidget(status)

            cell_layout.addStretch()
            self._grid.addWidget(cell, row, col)
            col += 1
            if col >= _COLUMNS:
                col = 0
                row += 1

    # ------------------------------------------------------------------- API
    def load(
        self, server_type: str, ports: Dict[str, bool], custom_ports: bool
    ) -> None:
        """Carga el estado de puertos para un tipo de servidor.

        Args:
            server_type: tipo de servidor cuyos puertos conocidos se muestran.
            ports: dict {str(puerto): seleccionado}. Puertos que no pertenezcan al
                tipo de servidor se tratan como personalizados.
            custom_ports: si False, los puertos del tipo de servidor se marcan por
                defecto; si True se respeta exactamente el dict ``ports``.
        """
        self._server_type = server_type
        names = get_server_ports(server_type)

        checked: Dict[int, bool] = {}
        self._custom = set()
        for key, value in ports.items():
            try:
                port = int(key)
            except (TypeError, ValueError):
                continue
            checked[port] = bool(value)
            if port not in names:
                self._custom.add(port)

        if not custom_ports:
            # Modo automático: marcar los puertos del tipo de servidor
            for port in names:
                checked.setdefault(port, True)

        self._rebuild_grid(checked)

    def set_server_type(self, server_type: str) -> None:
        """Cambia el tipo de servidor conservando los puertos personalizados."""
        current = self.get_ports()
        self.load(server_type, current, custom_ports=True)
        # En cambio de tipo, marcar por defecto los puertos del nuevo tipo
        for port in get_server_ports(server_type):
            if port in self._checkboxes:
                self._checkboxes[port].setChecked(True)

    def get_ports(self) -> Dict[str, bool]:
        """Devuelve el estado actual como {str(puerto): seleccionado}."""
        return {str(port): cb.isChecked() for port, cb in self._checkboxes.items()}

    def selected_ports(self) -> list:
        """Lista de puertos (int) actualmente marcados."""
        return [port for port, cb in self._checkboxes.items() if cb.isChecked()]

    # ----------------------------------------------------------- selección
    def select_all(self) -> None:
        for cb in self._checkboxes.values():
            cb.setChecked(True)

    def select_none(self) -> None:
        for cb in self._checkboxes.values():
            cb.setChecked(False)

    def select_defaults(self) -> None:
        for port, cb in self._checkboxes.items():
            cb.setChecked(port in DEFAULT_PORTS)

    # ------------------------------------------------------------- custom
    def _on_add_custom(self) -> None:
        port = self._custom_spin.value()
        if port in self._checkboxes:
            self._checkboxes[port].setChecked(True)
            return
        self._custom.add(port)
        checked = {p: cb.isChecked() for p, cb in self._checkboxes.items()}
        checked[port] = True
        self._rebuild_grid(checked)
        self.portsChanged.emit()

    def _on_remove_custom(self) -> None:
        port = self._custom_spin.value()
        names = get_server_ports(self._server_type)
        if port in names or port not in self._checkboxes:
            return  # Solo se pueden quitar puertos personalizados
        self._custom.discard(port)
        checked = {p: cb.isChecked() for p, cb in self._checkboxes.items() if p != port}
        self._rebuild_grid(checked)
        self.portsChanged.emit()

    # -------------------------------------------------------------- estado
    def set_port_status(self, port: int, status: str) -> None:
        """Actualiza el indicador de estado de un puerto (si show_status=True)."""
        widget = self._status_widgets.get(port)
        if widget is not None:
            widget.setStatus(status)

    def reset_status(self) -> None:
        """Pone todos los indicadores en 'disconnected'."""
        for widget in self._status_widgets.values():
            widget.setStatus("disconnected")
