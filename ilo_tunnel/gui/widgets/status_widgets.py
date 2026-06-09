# ilo_tunnel/gui/widgets/status_widgets.py
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtGui import QColor, QPainter, QBrush
from PyQt6.QtCore import Qt

from ..theme import Palette


class PortStatusWidget(QWidget):
    """
    Indicador circular del estado de un puerto tunelizado.

    Estados: disconnected (gris), connecting (amarillo), connected (verde),
    error (rojo). El tooltip describe el estado para mayor claridad.
    """

    STATUS_TOOLTIPS = {
        "disconnected": "Desconectado",
        "connecting": "Conectando…",
        "connected": "Conectado",
        "error": "Error",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.status = "disconnected"
        self.setFixedSize(16, 16)

        self.status_colors = {
            "disconnected": QColor(Palette.TEXT_FAINT),  # idle (neutro) por puerto
            "connecting": QColor(Palette.WARNING),
            "connected": QColor(Palette.SUCCESS),
            "error": QColor(Palette.DANGER),
        }
        self.setToolTip(self.STATUS_TOOLTIPS["disconnected"])

    def setStatus(self, status):
        """Establece el estado del puerto y actualiza color + tooltip."""
        if status in self.status_colors:
            self.status = status
            self.setToolTip(self.STATUS_TOOLTIPS.get(status, status))
            self.update()
            return True
        return False

    def paintEvent(self, event):
        """Dibuja el indicador de estado."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = self.status_colors.get(self.status, self.status_colors["disconnected"])
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(2, 2, self.width() - 4, self.height() - 4)


class ConnectionStatusBar(QWidget):
    """Barra que muestra el estado de conexión actual y un mensaje.

    Usa color semántico tanto en el indicador como en el texto: verde para
    conectado/listo, ámbar para espera y rojo para desconectado/error.
    """

    # Color de texto por estado (el indicador desconectado se tiñe de rojo aquí,
    # a diferencia del indicador por puerto que permanece neutro en reposo).
    # "ready" es el estado de reposo positivo (verde) usado al inicio.
    _TEXT_COLORS = {
        "ready": Palette.SUCCESS,
        "disconnected": Palette.DANGER,
        "connecting": Palette.WARNING,
        "connected": Palette.SUCCESS,
        "error": Palette.DANGER,
    }

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(8)

        self.status_indicator = PortStatusWidget()
        # Semántica de la barra: "desconectado" en rojo, "listo" en verde.
        self.status_indicator.status_colors["disconnected"] = QColor(Palette.DANGER)
        self.status_indicator.status_colors["ready"] = QColor(Palette.SUCCESS)
        layout.addWidget(self.status_indicator)

        self.status_label = QLabel("Desconectado")
        self.status_label.setStyleSheet("font-weight: 600;")
        layout.addWidget(self.status_label)

        layout.addStretch()
        self.setStatus("ready", "Listo")

    def setStatus(self, status, message=""):
        """Actualiza el indicador y el mensaje de estado."""
        self.status_indicator.setStatus(status)
        color = self._TEXT_COLORS.get(status, Palette.TEXT_MUTED)
        self.status_label.setStyleSheet(f"font-weight: 600; color: {color};")
        self.status_label.setText(message)
