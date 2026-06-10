# ilo_tunnel/gui/theme.py
"""Tema visual unificado de la aplicación (modo oscuro moderno).

Centraliza *toda* la declaración de estilos, separada de la disposición de los
widgets (que vive en los módulos de ``gui/widgets``). El resto de la UI solo
referencia:

* :class:`Palette`  — la paleta de colores semántica.
* :func:`apply_theme` — aplica estilo base + hoja QSS a la ``QApplication``.
* :func:`icon`       — crea iconos vectoriales (qtawesome) tintados con la paleta.

Para personalizar la apariencia basta con tocar este archivo.
"""
from pathlib import Path

import qtawesome as qta
from PyQt6.QtGui import QColor, QIcon, QPalette
from PyQt6.QtWidgets import QApplication

_ASSETS = Path(__file__).parent / "assets"


class Palette:
    """Paleta de colores del modo oscuro (estilo VS Code / Windows 11)."""

    # Superficies
    WINDOW = "#1E1E2E"        # fondo principal de la ventana
    CARD = "#252538"          # tarjetas / paneles
    INPUT = "#2C2C42"         # fondo de campos de entrada (diferenciado)
    HOVER = "#2F2F47"         # hover sutil sobre superficies
    BORDER = "#35354A"        # borde/divisoria sutil (apenas más claro que el fondo)
    BORDER_STRONG = "#43435C"  # borde de foco/realce

    # Texto
    TEXT = "#E4E4EF"          # texto primario
    TEXT_MUTED = "#9A9AB0"    # texto secundario / etiquetas
    TEXT_FAINT = "#6E6E86"    # placeholders / deshabilitado

    # Acento (violeta tecnológico)
    ACCENT = "#7C5CFC"
    ACCENT_HOVER = "#8E72FF"
    ACCENT_PRESSED = "#6B4FE8"
    ACCENT_SOFT = "#332B5C"    # selección suave de lista
    ON_ACCENT = "#FFFFFF"

    # Semánticos (estado)
    SUCCESS = "#3FB950"        # conectado / listo
    WARNING = "#D6A23A"        # espera / conectando
    DANGER = "#F25C5C"         # desconectado / error


def icon(name: str, color: str | None = None) -> QIcon:
    """Devuelve un icono vectorial de qtawesome tintado con la paleta.

    Args:
        name: nombre del icono (p. ej. ``"mdi6.lan-connect"``).
        color: color en hex; por defecto el texto primario de la paleta.
    """
    return qta.icon(name, color=color or Palette.TEXT)


def _build_stylesheet() -> str:
    p = Palette
    check_url = (_ASSETS / "check.svg").as_posix()
    return f"""
    /* ---------------------------------------------------------- base ---- */
    QWidget {{
        background-color: {p.WINDOW};
        color: {p.TEXT};
        font-size: 13px;
        selection-background-color: {p.ACCENT};
        selection-color: {p.ON_ACCENT};
    }}
    QToolTip {{
        background-color: {p.CARD};
        color: {p.TEXT};
        border: 1px solid {p.BORDER};
        border-radius: 6px;
        padding: 6px 8px;
    }}

    /* ------------------------------------------------------- toolbar ---- */
    QToolBar {{
        background-color: {p.WINDOW};
        border: none;
        border-bottom: 1px solid {p.BORDER};
        padding: 8px 10px;
        spacing: 6px;
    }}
    QToolBar::separator {{
        background-color: {p.BORDER};
        width: 1px;
        margin: 4px 8px;
    }}
    QToolButton {{
        background-color: transparent;
        color: {p.TEXT};
        border: none;
        border-radius: 6px;
        padding: 6px 12px;
    }}
    QToolButton:hover {{ background-color: {p.HOVER}; }}
    QToolButton:pressed {{ background-color: {p.ACCENT_SOFT}; }}
    QToolButton:disabled {{ color: {p.TEXT_FAINT}; }}

    /* -------------------------------------------------------- cards ----- */
    /* Los QGroupBox se renderizan como tarjetas independientes. */
    QGroupBox {{
        background-color: {p.CARD};
        border: 1px solid {p.BORDER};
        border-radius: 8px;
        margin-top: 14px;
        padding: 16px;
        font-weight: 600;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 14px;
        padding: 0 4px;
        color: {p.TEXT_MUTED};
    }}

    /* ------------------------------------------------------- inputs ----- */
    QLineEdit, QSpinBox, QComboBox {{
        background-color: {p.INPUT};
        color: {p.TEXT};
        border: 1px solid {p.BORDER};
        border-radius: 6px;
        padding: 7px 10px;
        min-height: 20px;
        selection-background-color: {p.ACCENT};
    }}
    QLineEdit:hover, QSpinBox:hover, QComboBox:hover {{
        border-color: {p.BORDER_STRONG};
    }}
    QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
        border-color: {p.ACCENT};
    }}
    QLineEdit:disabled, QSpinBox:disabled, QComboBox:disabled {{
        color: {p.TEXT_FAINT};
        background-color: {p.WINDOW};
    }}
    QLineEdit::placeholder {{ color: {p.TEXT_FAINT}; }}
    QComboBox::drop-down {{ border: none; width: 22px; }}
    QComboBox QAbstractItemView {{
        background-color: {p.CARD};
        border: 1px solid {p.BORDER};
        border-radius: 6px;
        outline: none;
        selection-background-color: {p.ACCENT_SOFT};
        selection-color: {p.TEXT};
        padding: 4px;
    }}
    QSpinBox::up-button, QSpinBox::down-button {{
        background-color: transparent;
        border: none;
        width: 16px;
    }}

    /* ------------------------------------------------------ buttons ----- */
    /* Por defecto: secundario (outlined / neutro sutil). */
    QPushButton {{
        background-color: transparent;
        color: {p.TEXT};
        border: 1px solid {p.BORDER_STRONG};
        border-radius: 6px;
        padding: 7px 16px;
        min-height: 18px;
    }}
    QPushButton:hover {{ background-color: {p.HOVER}; border-color: {p.ACCENT}; }}
    QPushButton:pressed {{ background-color: {p.ACCENT_SOFT}; }}
    QPushButton:disabled {{ color: {p.TEXT_FAINT}; border-color: {p.BORDER}; }}

    /* Acción principal: relleno con el color de acento. */
    QPushButton#primary {{
        background-color: {p.ACCENT};
        color: {p.ON_ACCENT};
        border: none;
        font-weight: 600;
    }}
    QPushButton#primary:hover {{ background-color: {p.ACCENT_HOVER}; }}
    QPushButton#primary:pressed {{ background-color: {p.ACCENT_PRESSED}; }}
    QPushButton#primary:disabled {{
        background-color: {p.BORDER};
        color: {p.TEXT_FAINT};
    }}

    /* Botones-icono compactos (gestión de perfiles). */
    QPushButton#iconButton {{
        border: 1px solid {p.BORDER};
        border-radius: 6px;
        padding: 6px;
        min-width: 16px;
    }}
    QPushButton#iconButton:hover {{
        background-color: {p.HOVER};
        border-color: {p.ACCENT};
    }}

    /* --------------------------------------------------- checkboxes ----- */
    QCheckBox {{ spacing: 8px; padding: 3px 0; }}
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border: 1px solid {p.BORDER_STRONG};
        border-radius: 5px;
        background-color: {p.INPUT};
    }}
    QCheckBox::indicator:hover {{ border-color: {p.ACCENT}; }}
    QCheckBox::indicator:checked {{
        background-color: {p.ACCENT};
        border-color: {p.ACCENT};
        image: url({check_url});
    }}
    QCheckBox::indicator:disabled {{ border-color: {p.BORDER}; }}

    /* --------------------------------------------------- tree/list ----- */
    QTreeWidget, QListWidget {{
        background-color: {p.CARD};
        border: 1px solid {p.BORDER};
        border-radius: 8px;
        outline: none;
        padding: 4px;
    }}
    QTreeWidget::item, QListWidget::item {{
        border-radius: 6px;
        padding: 6px 8px;
        margin: 1px 2px;
        color: {p.TEXT};
    }}
    QTreeWidget::item:hover, QListWidget::item:hover {{
        background-color: {p.HOVER};
    }}
    QTreeWidget::item:selected, QListWidget::item:selected {{
        background-color: {p.ACCENT_SOFT};
        color: {p.TEXT};
    }}
    QTreeWidget::branch {{ background: transparent; }}

    /* ----------------------------------------- collapsible (card) ------ */
    QFrame#card {{
        background-color: {p.CARD};
        border: 1px solid {p.BORDER};
        border-radius: 8px;
    }}
    QPushButton#sectionHeader {{
        background-color: transparent;
        border: none;
        border-radius: 8px;
        padding: 12px 16px;
        text-align: left;
        font-weight: 600;
        color: {p.TEXT};
    }}
    QPushButton#sectionHeader:hover {{ background-color: {p.HOVER}; }}
    QPushButton#sectionHeader:pressed {{ background-color: {p.ACCENT_SOFT}; }}

    /* -------------------------------------------------- splitter -------- */
    QSplitter::handle {{ background-color: transparent; }}
    QSplitter::handle:horizontal {{ width: 10px; }}
    QSplitter::handle:vertical {{ height: 10px; }}

    /* ------------------------------------------------- console ---------- */
    QTextEdit {{
        background-color: #16161F;
        color: {p.TEXT};
        border: 1px solid {p.BORDER};
        border-radius: 8px;
        padding: 8px;
    }}

    /* --------------------------------------------------- statusbar ------ */
    QStatusBar {{
        background-color: {p.WINDOW};
        border-top: 1px solid {p.BORDER};
        color: {p.TEXT_MUTED};
    }}
    QStatusBar::item {{ border: none; }}

    /* --------------------------------------------------- scrollbar ------ */
    QScrollArea {{ border: none; background-color: transparent; }}
    QScrollBar:vertical {{
        background: transparent; width: 10px; margin: 2px;
    }}
    QScrollBar::handle:vertical {{
        background: {p.BORDER_STRONG}; border-radius: 5px; min-height: 28px;
    }}
    QScrollBar::handle:vertical:hover {{ background: {p.ACCENT}; }}
    QScrollBar:horizontal {{
        background: transparent; height: 10px; margin: 2px;
    }}
    QScrollBar::handle:horizontal {{
        background: {p.BORDER_STRONG}; border-radius: 5px; min-width: 28px;
    }}
    QScrollBar::handle:horizontal:hover {{ background: {p.ACCENT}; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
    QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

    /* ------------------------------------------------------ dialogs ----- */
    QDialog {{ background-color: {p.WINDOW}; }}
    QMenu {{
        background-color: {p.CARD};
        border: 1px solid {p.BORDER};
        border-radius: 8px;
        padding: 4px;
    }}
    QMenu::item {{ padding: 6px 24px; border-radius: 6px; }}
    QMenu::item:selected {{ background-color: {p.ACCENT_SOFT}; }}
    """


def _apply_palette(app: QApplication) -> None:
    """Ajusta la QPalette base para que los diálogos nativos hereden el tema."""
    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window, QColor(Palette.WINDOW))
    pal.setColor(QPalette.ColorRole.WindowText, QColor(Palette.TEXT))
    pal.setColor(QPalette.ColorRole.Base, QColor(Palette.INPUT))
    pal.setColor(QPalette.ColorRole.AlternateBase, QColor(Palette.CARD))
    pal.setColor(QPalette.ColorRole.Text, QColor(Palette.TEXT))
    pal.setColor(QPalette.ColorRole.Button, QColor(Palette.CARD))
    pal.setColor(QPalette.ColorRole.ButtonText, QColor(Palette.TEXT))
    pal.setColor(QPalette.ColorRole.ToolTipBase, QColor(Palette.CARD))
    pal.setColor(QPalette.ColorRole.ToolTipText, QColor(Palette.TEXT))
    pal.setColor(QPalette.ColorRole.Highlight, QColor(Palette.ACCENT))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor(Palette.ON_ACCENT))
    pal.setColor(QPalette.ColorRole.PlaceholderText, QColor(Palette.TEXT_FAINT))
    app.setPalette(pal)


def apply_theme(app: QApplication) -> None:
    """Aplica el tema oscuro completo a la aplicación.

    Usa el estilo base *Fusion* (necesario para que la QSS se renderice de forma
    consistente entre plataformas, especialmente en macOS) y luego la hoja de
    estilos centralizada.
    """
    app.setStyle("Fusion")
    _apply_palette(app)
    app.setStyleSheet(_build_stylesheet())
