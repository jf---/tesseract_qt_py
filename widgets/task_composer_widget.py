"""Task composer widget for motion planning."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class TaskComposerWidget(QWidget):
    """Task composer widget for motion planning configuration and execution."""

    execute_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._setup_ui()

    def _setup_ui(self):
        """Setup widget layout."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setCurrentIndex(0)

        # Config tab
        config_tab = QWidget()
        config_layout = QFormLayout(config_tab)

        # Executor
        self.executor_label = QLabel("Executor:")
        self.executor_combo_box = QComboBox()
        config_layout.addRow(self.executor_label, self.executor_combo_box)

        # Task
        self.task_label = QLabel("Task:")
        self.task_combo_box = QComboBox()
        task_policy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        task_policy.setHorizontalStretch(1)
        self.task_combo_box.setSizePolicy(task_policy)
        config_layout.addRow(self.task_label, self.task_combo_box)

        # Environment
        self.environment_label = QLabel("Environment:")
        env_frame = QFrame()
        env_frame.setFrameShape(QFrame.Shape.NoFrame)
        env_frame.setFrameShadow(QFrame.Shadow.Raised)
        env_layout = QHBoxLayout(env_frame)
        env_layout.setContentsMargins(0, 0, 0, 0)

        self.environment_line_edit = QLineEdit()
        self.environment_line_edit.setPlaceholderText("Log Environment")
        env_layout.addWidget(self.environment_line_edit)

        self.environment_push_button = QPushButton("...")
        self.environment_push_button.setMinimumSize(25, 0)
        self.environment_push_button.setMaximumSize(25, 16777215)
        self.environment_push_button.setToolTip("Pick Environment")
        env_layout.addWidget(self.environment_push_button)

        config_layout.addRow(self.environment_label, env_frame)

        # Namespace
        self.ns_label = QLabel("Namespace:")
        self.ns_line_edit = QLineEdit()
        config_layout.addRow(self.ns_label, self.ns_line_edit)

        # Description
        self.desc_label = QLabel("Description:")
        self.desc_line_edit = QLineEdit()
        config_layout.addRow(self.desc_label, self.desc_line_edit)

        # Dot Graph
        self.dotgraph_label = QLabel("Dot Graph:")
        self.dotgraph_check_box = QCheckBox()
        self.dotgraph_check_box.setChecked(True)
        config_layout.addRow(self.dotgraph_label, self.dotgraph_check_box)

        self.tab_widget.addTab(config_tab, "Config")

        # Logs tab
        logs_tab = QWidget()
        logs_layout = QVBoxLayout(logs_tab)

        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setPlaceholderText("Planning output will appear here...")
        logs_layout.addWidget(self.log_output)

        self.tab_widget.addTab(logs_tab, "Logs")

        main_layout.addWidget(self.tab_widget)

        # Bottom section
        bottom_frame = QFrame()
        bottom_frame.setFrameShape(QFrame.Shape.NoFrame)
        bottom_frame.setFrameShadow(QFrame.Shadow.Raised)
        bottom_layout = QHBoxLayout(bottom_frame)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setStretch(0, 0)
        bottom_layout.setStretch(1, 0)
        bottom_layout.setStretch(2, 1)
        bottom_layout.setStretch(3, 0)

        self.log_label = QLabel("Log:")
        bottom_layout.addWidget(self.log_label)

        self.ns_combo_box = QComboBox()
        self.ns_combo_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.ns_combo_box.setToolTip("Namespace")
        bottom_layout.addWidget(self.ns_combo_box)

        self.log_combo_box = QComboBox()
        self.log_combo_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.log_combo_box.setToolTip("Log")
        bottom_layout.addWidget(self.log_combo_box)

        self.task_run_push_button = QPushButton("run")
        self.task_run_push_button.setMaximumSize(50, 16777215)
        self.task_run_push_button.clicked.connect(self.execute_requested.emit)
        bottom_layout.addWidget(self.task_run_push_button)

        main_layout.addWidget(bottom_frame)

    def log(self, message: str):
        """Append message to log output."""
        self.log_output.appendPlainText(message)

    def clear_log(self):
        """Clear log output."""
        self.log_output.clear()

    def set_executors(self, executors: list[str], default: str | None = None):
        """Set available executors."""
        self.executor_combo_box.clear()
        self.executor_combo_box.addItems(executors)
        if default and default in executors:
            self.executor_combo_box.setCurrentText(default)

    def set_tasks(self, tasks: list[str], default: str | None = None):
        """Set available tasks."""
        self.task_combo_box.clear()
        self.task_combo_box.addItems(tasks)
        if default and default in tasks:
            self.task_combo_box.setCurrentText(default)

    def current_executor(self) -> str:
        """Get selected executor name."""
        return self.executor_combo_box.currentText()

    def current_task(self) -> str:
        """Get selected task name."""
        return self.task_combo_box.currentText()

    def set_environment_name(self, name: str):
        """Set environment display name."""
        self.environment_line_edit.setText(name)
