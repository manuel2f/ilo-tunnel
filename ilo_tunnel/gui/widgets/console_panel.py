# ilo_tunnel/gui/widgets/console_panel.py
from PyQt6.QtGui import QColor, QFont, QTextCursor
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class ConsolePanel(QWidget):
    """Consola de salida del túnel con botones de limpiar / copiar / guardar."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._auto_scroll = True
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.set_font_size(9)
        root.addWidget(self.console)

        buttons = QHBoxLayout()
        clear_btn = QPushButton("Limpiar")
        clear_btn.clicked.connect(self.console.clear)
        copy_btn = QPushButton("Copiar")
        copy_btn.clicked.connect(self._copy)
        save_btn = QPushButton("Guardar")
        save_btn.clicked.connect(self._save)
        buttons.addWidget(clear_btn)
        buttons.addWidget(copy_btn)
        buttons.addWidget(save_btn)
        buttons.addStretch()
        root.addLayout(buttons)

    # ------------------------------------------------------------- salida
    def append_output(self, text: str) -> None:
        """Añade texto normal a la consola."""
        self.console.setTextColor(QColor("black"))
        self.console.append(text)
        self._maybe_scroll()

    def append_error(self, text: str) -> None:
        """Añade texto de error (en rojo) a la consola."""
        self.console.setTextColor(QColor("red"))
        self.console.append(text)
        self.console.setTextColor(QColor("black"))
        self._maybe_scroll()

    def _maybe_scroll(self) -> None:
        if self._auto_scroll:
            self.console.moveCursor(QTextCursor.MoveOperation.End)

    # ------------------------------------------------------------ ajustes
    def set_auto_scroll(self, enabled: bool) -> None:
        self._auto_scroll = enabled

    def set_font_size(self, size: int) -> None:
        font = QFont()
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setFixedPitch(True)
        font.setPointSize(size)
        self.console.setFont(font)

    # ------------------------------------------------------------ botones
    def _copy(self) -> None:
        self.console.selectAll()
        self.console.copy()
        cursor = self.console.textCursor()
        cursor.clearSelection()
        self.console.setTextCursor(cursor)

    def _save(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar registro", "ilo-tunnel.log", "Texto (*.log *.txt)"
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(self.console.toPlainText())
        except OSError as exc:
            QMessageBox.warning(
                self, "Error", f"No se pudo guardar el registro:\n{exc}"
            )
