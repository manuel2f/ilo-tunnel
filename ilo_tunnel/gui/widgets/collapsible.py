# ilo_tunnel/gui/widgets/collapsible.py
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..theme import Palette, icon


class CollapsibleSection(QFrame):
    """Sección colapsable (accordion) con cabecera y cuerpo plegable.

    Sustituye al ``QGroupBox`` "checkable" (que solo atenuaba en gris): al
    colapsar, el contenido se oculta por completo con elegancia. El estado de
    los widgets internos no cambia, de modo que la lógica de datos del
    formulario sigue leyéndolos igual.
    """

    toggled = pyqtSignal(bool)

    def __init__(self, title: str, expanded: bool = False, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._expanded = expanded

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._header = QPushButton(title)
        self._header.setObjectName("sectionHeader")
        self._header.setCursor(Qt.CursorShape.PointingHandCursor)
        self._header.clicked.connect(self.toggle)
        root.addWidget(self._header)

        self._body = QWidget()
        self._body_layout = QVBoxLayout(self._body)
        self._body_layout.setContentsMargins(16, 4, 16, 16)
        root.addWidget(self._body)

        self._update_state()

    # --------------------------------------------------------------- API
    def set_content_layout(self, layout) -> None:
        """Coloca ``layout`` como contenido plegable de la sección."""
        self._body_layout.addLayout(layout)

    def add_widget(self, widget: QWidget) -> None:
        self._body_layout.addWidget(widget)

    def setExpanded(self, expanded: bool) -> None:
        if expanded != self._expanded:
            self._expanded = expanded
            self._update_state()
            self.toggled.emit(expanded)

    def isExpanded(self) -> bool:
        return self._expanded

    def toggle(self) -> None:
        self.setExpanded(not self._expanded)

    # ----------------------------------------------------------- interno
    def _update_state(self) -> None:
        self._body.setVisible(self._expanded)
        name = "mdi6.chevron-down" if self._expanded else "mdi6.chevron-right"
        self._header.setIcon(icon(name, Palette.TEXT_MUTED))
