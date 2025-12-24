"""Contact results compute widget."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QFrame,
    QPushButton,
    QDoubleSpinBox,
    QComboBox,
    QCheckBox,
    QSizePolicy,
)


class ContactComputeWidget(QWidget):
    """Widget for computing contact results."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Contact Request group
        group = QGroupBox("Contact Request")
        group.setCheckable(True)
        group.setChecked(True)
        form = QFormLayout(group)

        # Contact Threshold
        self.contact_threshold = QDoubleSpinBox()
        self.contact_threshold.setDecimals(6)
        self.contact_threshold.setRange(-100, 100)
        self.contact_threshold.setSingleStep(0.001)
        self.contact_threshold.setValue(0)
        form.addRow("Contact Threshold:", self.contact_threshold)

        # Contact Test Type
        self.contact_test_type = QComboBox()
        self.contact_test_type.addItems(["First", "Closest", "All"])
        form.addRow("Contact Test Type:", self.contact_test_type)

        # Calculate Penetration
        self.calc_penetration = QCheckBox()
        self.calc_penetration.setChecked(True)
        form.addRow("Calculate Penetration:", self.calc_penetration)

        # Calculate Distance
        self.calc_distance = QCheckBox()
        self.calc_distance.setChecked(True)
        form.addRow("Calculate Distance:", self.calc_distance)

        layout.addWidget(group)

        # Buttons frame
        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(0, 0, 0, 0)

        self.btn_check_state = QPushButton("Check State")
        button_layout.addWidget(self.btn_check_state)

        button_layout.addStretch()

        self.btn_clear = QPushButton("Clear")
        button_layout.addWidget(self.btn_clear)

        self.btn_compute = QPushButton("Compute")
        button_layout.addWidget(self.btn_compute)

        layout.addWidget(button_frame)

        # Placeholder for contact_results_widget
        self.contact_results_widget = QWidget()
        self.contact_results_widget.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding
        )
        layout.addWidget(self.contact_results_widget, stretch=1)
