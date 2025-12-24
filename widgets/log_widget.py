"""Log viewer widget for displaying loguru logs."""
from __future__ import annotations

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QTextCharFormat, QColor, QFont
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPlainTextEdit,
    QPushButton,
    QCheckBox,
)


# Color scheme matching status bar
LOG_COLORS = {
    "DEBUG": "#888888",
    "INFO": "#000000",
    "SUCCESS": "#228B22",
    "WARNING": "#FFA500",
    "ERROR": "#FF0000",
    "CRITICAL": "#8B0000",
}


class LogWidget(QWidget):
    """Widget for displaying application logs with color-coding."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(3)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(5)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setMaximumWidth(60)
        self.clear_btn.clicked.connect(self.clear)
        toolbar.addWidget(self.clear_btn)

        self.auto_scroll_cb = QCheckBox("Auto-scroll")
        self.auto_scroll_cb.setChecked(True)
        toolbar.addWidget(self.auto_scroll_cb)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Log output
        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.log_output.setMaximumBlockCount(5000)  # Limit memory usage

        # Monospace font
        font = QFont("Menlo, Monaco, Consolas, monospace")
        font.setPointSize(10)
        self.log_output.setFont(font)

        layout.addWidget(self.log_output)

    @Slot()
    def clear(self):
        """Clear all log output."""
        self.log_output.clear()

    def append_log(self, message: str, level: str = "INFO"):
        """Append a log message with color-coding.

        Args:
            message: The log message text
            level: Log level (DEBUG, INFO, SUCCESS, WARNING, ERROR, CRITICAL)
        """
        color = LOG_COLORS.get(level.upper(), "#000000")

        # Create colored text format
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))

        # Append with format
        cursor = self.log_output.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(message + "\n", fmt)

        # Auto-scroll if enabled
        if self.auto_scroll_cb.isChecked():
            scrollbar = self.log_output.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
