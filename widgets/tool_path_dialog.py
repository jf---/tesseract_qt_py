"""Tool path file dialog widget."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)


class ToolPathFileDialog(QDialog):
    """Dialog for selecting tool path file and link."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Dialog")
        self.resize(400, 116)
        self._setup_ui()

    def _setup_ui(self):
        # Main layout
        layout = QVBoxLayout(self)

        # Frame with grid layout
        frame = QFrame()
        frame.setFrameShape(QFrame.NoFrame)
        frame.setFrameShadow(QFrame.Raised)

        grid = QGridLayout(frame)

        # Row 0: Link name
        self.frame_label = QLabel("Link Name:")
        self.frame_combo_box = QComboBox()
        grid.addWidget(self.frame_label, 0, 0)
        grid.addWidget(self.frame_combo_box, 0, 1)

        # Row 1: File path
        self.file_path_label = QLabel("File Path:")
        self.file_path_line_edit = QLineEdit()
        self.file_path_line_edit.setReadOnly(True)
        self.file_path_push_button = QPushButton("Browse")
        grid.addWidget(self.file_path_label, 1, 0)
        grid.addWidget(self.file_path_line_edit, 1, 1)
        grid.addWidget(self.file_path_push_button, 1, 2)

        layout.addWidget(frame)

        # Dialog buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
