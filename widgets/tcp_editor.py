"""TCP (Tool Center Point) editor widget."""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QGroupBox,
)

from widgets.cartesian_editor import CartesianEditorWidget


class TCPEditorWidget(QWidget):
    """Widget for editing TCP link and offset."""

    tcp_changed = Signal(str)  # link_name
    offset_changed = Signal(float, float, float, float, float, float)  # x,y,z,rx,ry,rz

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(3, 3, 3, 3)

        # TCP Link selector
        link_group = QGroupBox("TCP Link")
        link_layout = QHBoxLayout(link_group)

        link_layout.addWidget(QLabel("Link:"))
        self.link_combo = QComboBox()
        self.link_combo.currentTextChanged.connect(self._on_link_changed)
        link_layout.addWidget(self.link_combo, 1)

        layout.addWidget(link_group)

        # Offset editor
        offset_group = QGroupBox("TCP Offset")
        offset_layout = QVBoxLayout(offset_group)
        offset_layout.setContentsMargins(3, 3, 3, 3)

        self.offset_editor = CartesianEditorWidget()
        self.offset_editor.x_spin.valueChanged.connect(self._on_offset_changed)
        self.offset_editor.y_spin.valueChanged.connect(self._on_offset_changed)
        self.offset_editor.z_spin.valueChanged.connect(self._on_offset_changed)
        self.offset_editor.roll_spin.valueChanged.connect(self._on_offset_changed)
        self.offset_editor.pitch_spin.valueChanged.connect(self._on_offset_changed)
        self.offset_editor.yaw_spin.valueChanged.connect(self._on_offset_changed)
        offset_layout.addWidget(self.offset_editor)

        layout.addWidget(offset_group, 1)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setMinimumWidth(80)
        self.reset_btn.clicked.connect(self._on_reset)
        btn_layout.addWidget(self.reset_btn)

        self.apply_btn = QPushButton("Apply Offset")
        self.apply_btn.setMinimumWidth(80)
        self.apply_btn.clicked.connect(self._on_apply)
        btn_layout.addWidget(self.apply_btn)

        layout.addLayout(btn_layout)

    def _on_link_changed(self, link_name: str):
        if link_name:
            self.tcp_changed.emit(link_name)

    def _on_offset_changed(self):
        x, y, z, rx, ry, rz = self.get_offset()
        self.offset_changed.emit(x, y, z, rx, ry, rz)

    def _on_reset(self):
        self.offset_editor.x_spin.setValue(0.0)
        self.offset_editor.y_spin.setValue(0.0)
        self.offset_editor.z_spin.setValue(0.0)
        self.offset_editor.roll_spin.setValue(0.0)
        self.offset_editor.pitch_spin.setValue(0.0)
        self.offset_editor.yaw_spin.setValue(0.0)

    def _on_apply(self):
        self._on_offset_changed()

    def set_links(self, links: list[str]):
        """Set available TCP links."""
        current = self.link_combo.currentText()
        self.link_combo.clear()
        self.link_combo.addItems(links)
        if current in links:
            self.link_combo.setCurrentText(current)

    def set_tcp(self, link_name: str):
        """Set current TCP link."""
        idx = self.link_combo.findText(link_name)
        if idx >= 0:
            self.link_combo.setCurrentIndex(idx)

    def get_offset(self) -> tuple[float, float, float, float, float, float]:
        """Get current offset as (x,y,z,rx,ry,rz)."""
        return (
            self.offset_editor.x_spin.value(),
            self.offset_editor.y_spin.value(),
            self.offset_editor.z_spin.value(),
            self.offset_editor.roll_spin.value(),
            self.offset_editor.pitch_spin.value(),
            self.offset_editor.yaw_spin.value(),
        )
