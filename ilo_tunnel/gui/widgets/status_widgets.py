# ilo_tunnel/gui/widgets/status_widgets.py
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtGui import QColor, QPainter, QBrush
from PyQt6.QtCore import Qt


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
            "disconnected": QColor(150, 150, 150),
            "connecting": QColor(255, 200, 0),
            "connected": QColor(0, 180, 0),
            "error": QColor(220, 0, 0),
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
    """Barra que muestra el estado de conexión actual y un mensaje."""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)

        self.status_indicator = PortStatusWidget()
        layout.addWidget(self.status_indicator)

        self.status_label = QLabel("Desconectado")
        layout.addWidget(self.status_label)

        layout.addStretch()
        self.setStatus("disconnected", "Listo")

    def setStatus(self, status, message=""):
        """Actualiza el indicador y el mensaje de estado."""
        self.status_indicator.setStatus(status)
        self.status_label.setText(message)
