# ilo_tunnel/gui/widgets.py
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtGui import QColor, QPainter, QBrush
from PyQt6.QtCore import Qt, QSize


class PortStatusWidget(QWidget):
    """
    Widget para mostrar el estado de un puerto tunelizado.

    Estados posibles:
    - disconnected: Desconectado (gris)
    - connecting: Conectando (amarillo)
    - connected: Conectado (verde)
    - error: Error (rojo)
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.status = "disconnected"
        self.setFixedSize(16, 16)

        # Definir colores para cada estado
        self.status_colors = {
            "disconnected": QColor(150, 150, 150),  # Gris
            "connecting": QColor(255, 200, 0),  # Amarillo
            "connected": QColor(0, 180, 0),  # Verde
            "error": QColor(220, 0, 0),  # Rojo
        }

    def setStatus(self, status):
        """Establece el estado del puerto"""
        if status in self.status_colors:
            self.status = status
            self.update()  # Actualizar el widget
            return True
        return False

    def paintEvent(self, event):
        """Dibuja el indicador de estado"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Dibujar el círculo con el color del estado actual
        color = self.status_colors.get(self.status, self.status_colors["disconnected"])
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)

        # Dibujar círculo que ocupe todo el widget
        painter.drawEllipse(2, 2, self.width() - 4, self.height() - 4)


class ConnectionStatusBar(QWidget):
    """
    Barra de estado de conexión que muestra el estado actual y mensaje
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(4, 2, 4, 2)

        # Indicador de estado
        self.status_indicator = PortStatusWidget()
        self.layout.addWidget(self.status_indicator)

        # Etiqueta con mensaje de estado
        self.status_label = QLabel("Desconectado")
        self.layout.addWidget(self.status_label)

        # Espaciador para alinear a la izquierda
        self.layout.addStretch()

        # Estado inicial
        self.setStatus("disconnected", "Listo")

    def setStatus(self, status, message=""):
        """
        Actualiza el estado y mensaje

        Args:
            status: disconnected, connecting, connected, error
            message: Mensaje a mostrar
        """
        self.status_indicator.setStatus(status)
        self.status_label.setText(message)


class LogTextEdit(QWidget):
    """
    Widget de texto avanzado para mostrar logs con colores y filtrado
    """

    # TODO: Implementar un widget de texto avanzado para logs
    pass
