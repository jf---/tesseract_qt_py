"""Log viewer widget for displaying loguru logs."""

from __future__ import annotations

from collections import deque

from PySide6.QtCore import Slot
from PySide6.QtGui import QColor, QFont, QTextCharFormat
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# Log levels in order (lowest to highest)
LOG_LEVELS = ["DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]

# Color scheme with foreground and background for contrast in light/dark modes
LOG_STYLES = {
    "DEBUG": {"fg": "#888888", "bg": "#F0F0F0"},
    "INFO": {"fg": "#1A1A1A", "bg": "#FFFFFF"},
    "SUCCESS": {"fg": "#155724", "bg": "#D4EDDA"},
    "WARNING": {"fg": "#856404", "bg": "#FFF3CD"},
    "ERROR": {"fg": "#721C24", "bg": "#F8D7DA"},
    "CRITICAL": {"fg": "#FFFFFF", "bg": "#DC3545"},
}


class LogWidget(QWidget):
    """Widget for displaying application logs with color-coding."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._min_level = 0  # Show all by default (DEBUG)
        self._max_messages = 5000
        self._messages: deque[tuple[str, str]] = deque(maxlen=self._max_messages)
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

        # Level filter
        toolbar.addWidget(QLabel("Level:"))
        self.level_combo = QComboBox()
        self.level_combo.addItems(LOG_LEVELS)
        self.level_combo.setCurrentIndex(0)  # DEBUG (show all)
        self.level_combo.currentIndexChanged.connect(self._on_level_changed)
        self.level_combo.setToolTip("Show messages at this level and above")
        toolbar.addWidget(self.level_combo)

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
        self._messages.clear()
        self.log_output.clear()

    def _on_level_changed(self, index: int):
        """Handle level filter change - re-render all messages."""
        self._min_level = index
        self._rerender()

    def _rerender(self):
        """Re-render all stored messages with current filter."""
        self.log_output.clear()
        for message, level in self._messages:
            if self._level_index(level) >= self._min_level:
                self._append_formatted(message, level)

    def _level_index(self, level: str) -> int:
        """Get numeric index for a log level."""
        try:
            return LOG_LEVELS.index(level.upper())
        except ValueError:
            return 1  # Default to INFO

    def append_log(self, message: str, level: str = "INFO"):
        """Append a log message with color-coding.

        Args:
            message: The log message text
            level: Log level (DEBUG, INFO, SUCCESS, WARNING, ERROR, CRITICAL)
        """
        # Store message (deque auto-discards oldest when full)
        self._messages.append((message, level))

        # Only display if passes filter
        if self._level_index(level) >= self._min_level:
            self._append_formatted(message, level)

    def _append_formatted(self, message: str, level: str):
        """Append formatted message to display."""
        style = LOG_STYLES.get(level.upper(), LOG_STYLES["INFO"])

        # Create format with foreground and background
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(style["fg"]))
        fmt.setBackground(QColor(style["bg"]))

        # Append with format
        cursor = self.log_output.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(message + "\n", fmt)

        # Auto-scroll if enabled
        if self.auto_scroll_cb.isChecked():
            scrollbar = self.log_output.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def loguru_sink(self, message):
        """Loguru sink function for receiving log messages.

        Usage:
            from loguru import logger
            logger.add(log_widget.loguru_sink, format="{time:HH:mm:ss} | {level: <8} | {message}")
        """
        record = message.record
        level = record["level"].name
        # Extract the formatted message string
        text = str(message).rstrip()
        self.append_log(text, level)
