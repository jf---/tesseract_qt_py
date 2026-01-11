"""Load environment dialog and widget."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings, QStandardPaths
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class LoadEnvironmentWidget(QWidget):
    """Widget for selecting URDF and SRDF files."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._urdf_filepath = ""
        self._srdf_filepath = ""
        self._default_directory = ""
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        """Setup widget UI."""
        layout = QGridLayout(self)

        # URDF row (row 0)
        urdf_label = QLabel("URDF File:")
        self.urdf_line_edit = QLineEdit()
        self.urdf_line_edit.setReadOnly(True)
        urdf_browse_btn = QPushButton("Browse")
        urdf_browse_btn.setMinimumWidth(80)
        urdf_browse_btn.clicked.connect(self._on_browse_urdf)

        layout.addWidget(urdf_label, 0, 0)
        layout.addWidget(self.urdf_line_edit, 0, 1)
        layout.addWidget(urdf_browse_btn, 0, 2)

        # SRDF row (row 1)
        srdf_label = QLabel("SRDF File:")
        self.srdf_line_edit = QLineEdit()
        self.srdf_line_edit.setReadOnly(True)
        srdf_browse_btn = QPushButton("Browse")
        srdf_browse_btn.setMinimumWidth(80)
        srdf_browse_btn.clicked.connect(self._on_browse_srdf)

        layout.addWidget(srdf_label, 1, 0)
        layout.addWidget(self.srdf_line_edit, 1, 1)
        layout.addWidget(srdf_browse_btn, 1, 2)

    def _load_settings(self):
        """Load default directory from QSettings."""
        settings = QSettings()
        settings.beginGroup("LoadEnvironmentWidget")
        doc_locations = QStandardPaths.standardLocations(
            QStandardPaths.StandardLocation.DocumentsLocation
        )
        default_doc = doc_locations[0] if doc_locations else ""
        self._default_directory = settings.value("default_directory", default_doc)
        settings.endGroup()

    def _save_settings(self):
        """Save default directory to QSettings."""
        settings = QSettings()
        settings.beginGroup("LoadEnvironmentWidget")
        settings.setValue("default_directory", self._default_directory)
        settings.endGroup()

    def _on_browse_urdf(self):
        """Handle URDF browse button click."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open URDF",
            self._default_directory,
            "URDF (*.urdf)",
        )
        if file_path:
            self._urdf_filepath = file_path
            self.urdf_line_edit.setText(file_path)
            path_obj = Path(file_path)
            if path_obj.exists():
                self._default_directory = str(path_obj.parent)

    def _on_browse_srdf(self):
        """Handle SRDF browse button click."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open SRDF",
            self._default_directory,
            "SRDF (*.srdf)",
        )
        if file_path:
            self._srdf_filepath = file_path
            self.srdf_line_edit.setText(file_path)
            path_obj = Path(file_path)
            if path_obj.exists():
                self._default_directory = str(path_obj.parent)

    @property
    def urdf_filepath(self) -> str:
        """Get selected URDF file path."""
        return self._urdf_filepath

    @property
    def srdf_filepath(self) -> str:
        """Get selected SRDF file path."""
        return self._srdf_filepath

    def __del__(self):
        """Save settings on destruction."""
        try:
            self._save_settings()
        except Exception:
            pass


class LoadEnvironmentDialog(QDialog):
    """Dialog for loading URDF/SRDF environment."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Load Environment")
        self._setup_ui()

    def _setup_ui(self):
        """Setup dialog UI."""
        layout = QVBoxLayout(self)

        # Add load widget
        self.load_widget = LoadEnvironmentWidget()
        layout.addWidget(self.load_widget)

        # Add button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    @property
    def urdf_filepath(self) -> str:
        """Get selected URDF file path."""
        return self.load_widget.urdf_filepath

    @property
    def srdf_filepath(self) -> str:
        """Get selected SRDF file path."""
        return self.load_widget.srdf_filepath
