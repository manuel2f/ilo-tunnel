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

from ..theme import Palette, icon


class ConsolePanel(QWidget):
    """Consola de salida del túnel con botones de limpiar / copiar / guardar."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._auto_scroll = True
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 0, 18, 12)
        root.setSpacing(8)

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.set_font_size(9)
        root.addWidget(self.console)

        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        clear_btn = QPushButton(icon("mdi6.broom", Palette.TEXT), " Limpiar")
        clear_btn.clicked.connect(self.console.clear)
        copy_btn = QPushButton(icon("mdi6.content-copy", Palette.TEXT), " Copiar")
        copy_btn.clicked.connect(self._copy)
        save_btn = QPushButton(icon("mdi6.tray-arrow-down", Palette.TEXT), " Guardar")
        save_btn.clicked.connect(self._save)
        buttons.addStretch()
        buttons.addWidget(clear_btn)
        buttons.addWidget(copy_btn)
        buttons.addWidget(save_btn)
        root.addLayout(buttons)

    # ------------------------------------------------------------- salida
    def append_output(self, text: str) -> None:
        """Añade texto normal a la consola."""
        self.console.setTextColor(QColor(Palette.TEXT))
        self.console.append(text)
        self._maybe_scroll()

    def append_error(self, text: str) -> None:
        """Añade texto de error (en rojo) a la consola."""
        self.console.setTextColor(QColor(Palette.DANGER))
        self.console.append(text)
        self.console.setTextColor(QColor(Palette.TEXT))
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
