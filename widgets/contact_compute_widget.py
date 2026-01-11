"""Contact results compute widget."""

from __future__ import annotations

from PySide6.QtCore import Qt
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
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLabel,
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

        # Contact Results Table
        results_frame = QFrame()
        results_layout = QVBoxLayout(results_frame)
        results_layout.setContentsMargins(0, 0, 0, 0)

        # Results count label
        self.results_count_label = QLabel("Results: 0")
        results_layout.addWidget(self.results_count_label)

        # Results table
        self.contact_results_widget = QTableWidget()
        self.contact_results_widget.setColumnCount(6)
        self.contact_results_widget.setHorizontalHeaderLabels(
            ["Link1", "Link2", "Distance", "Point1", "Point2", "Normal"]
        )

        # Configure table headers
        header = self.contact_results_widget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)

        self.contact_results_widget.setAlternatingRowColors(True)
        self.contact_results_widget.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.contact_results_widget.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding
        )

        results_layout.addWidget(self.contact_results_widget)
        layout.addWidget(results_frame, stretch=1)

    def clear_results(self):
        """Clear the contact results table."""
        self.contact_results_widget.setRowCount(0)
        self.results_count_label.setText("Results: 0")

    def add_result(self, link1, link2, distance, pt1, pt2, normal):
        """Add a contact result to the table.

        Args:
            link1: Name of first link
            link2: Name of second link
            distance: Contact distance
            pt1: Contact point on link1 (x, y, z)
            pt2: Contact point on link2 (x, y, z)
            normal: Contact normal vector (x, y, z)
        """
        row = self.contact_results_widget.rowCount()
        self.contact_results_widget.insertRow(row)

        # Format point/normal as strings
        pt1_str = f"({pt1[0]:.3f}, {pt1[1]:.3f}, {pt1[2]:.3f})"
        pt2_str = f"({pt2[0]:.3f}, {pt2[1]:.3f}, {pt2[2]:.3f})"
        normal_str = f"({normal[0]:.3f}, {normal[1]:.3f}, {normal[2]:.3f})"

        # Add items to row
        self.contact_results_widget.setItem(row, 0, QTableWidgetItem(str(link1)))
        self.contact_results_widget.setItem(row, 1, QTableWidgetItem(str(link2)))
        self.contact_results_widget.setItem(row, 2, QTableWidgetItem(f"{distance:.6f}"))
        self.contact_results_widget.setItem(row, 3, QTableWidgetItem(pt1_str))
        self.contact_results_widget.setItem(row, 4, QTableWidgetItem(pt2_str))
        self.contact_results_widget.setItem(row, 5, QTableWidgetItem(normal_str))

    def set_result_count(self, count):
        """Update the results count label.

        Args:
            count: Number of results
        """
        self.results_count_label.setText(f"Results: {count}")
