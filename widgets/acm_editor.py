"""Allowed Collision Matrix editor widget."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QLabel,
    QSlider,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QDialog,
    QFormLayout,
    QLineEdit,
    QDialogButtonBox,
    QAbstractItemView,
    QComboBox,
)


class AddACMEntryDialog(QDialog):
    """Dialog to add an allowed collision entry."""

    def __init__(self, links: list[str] | None = None, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Add Allowed Collision Entry")
        self.resize(400, 150)
        self._links = sorted(links) if links else []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.link1_combo = QComboBox()
        self.link1_combo.addItems(self._links)
        self.link1_combo.setEditable(True)

        self.link2_combo = QComboBox()
        self.link2_combo.addItems(self._links)
        self.link2_combo.setEditable(True)

        self.reason_edit = QLineEdit()
        self.reason_edit.setText("User defined")

        form.addRow("Link 1:", self.link1_combo)
        form.addRow("Link 2:", self.link2_combo)
        form.addRow("Reason:", self.reason_edit)
        layout.addLayout(form)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def get_entry(self) -> tuple[str, str, str] | None:
        """Return (link1, link2, reason) or None if cancelled."""
        if self.exec() == QDialog.DialogCode.Accepted:
            return (
                self.link1_combo.currentText().strip(),
                self.link2_combo.currentText().strip(),
                self.reason_edit.text().strip(),
            )
        return None


class ACMEditorWidget(QWidget):
    """Editor for Allowed Collision Matrix."""

    entry_added = Signal(str, str, str)  # link1, link2, reason
    entry_removed = Signal(str, str)  # link1, link2
    matrix_applied = Signal()
    generate_requested = Signal(int)  # resolution

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._links: list[str] = []
        self._setup_ui()

    def set_links(self, links: list[str]):
        """Set available links for dropdown selection."""
        self._links = sorted(links)

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Resolution controls
        res_frame = QFrame()
        res_frame.setFrameShape(QFrame.Shape.NoFrame)
        res_layout = QHBoxLayout(res_frame)
        res_layout.setContentsMargins(0, 0, 0, 0)

        res_layout.addWidget(QLabel("Resolution:"))

        self.resolution_slider = QSlider(Qt.Orientation.Horizontal)
        self.resolution_slider.setMinimum(1000)
        self.resolution_slider.setMaximum(10000)
        self.resolution_slider.setValue(8000)
        res_layout.addWidget(self.resolution_slider)

        self.generate_btn = QPushButton("Generate")
        self.generate_btn.setMinimumWidth(80)
        self.generate_btn.clicked.connect(self._on_generate)
        res_layout.addWidget(self.generate_btn)

        layout.addWidget(res_frame)

        # ACM table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Link 1", "Link 2", "Reason"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table, 1)

        # Action buttons
        btn_frame = QFrame()
        btn_frame.setFrameShape(QFrame.Shape.NoFrame)
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setContentsMargins(0, 0, 0, 0)

        btn_layout.addStretch()

        self.add_btn = QPushButton("Add")
        self.add_btn.setMinimumWidth(80)
        self.add_btn.clicked.connect(self._on_add)
        btn_layout.addWidget(self.add_btn)

        self.remove_btn = QPushButton("Remove")
        self.remove_btn.setMinimumWidth(80)
        self.remove_btn.clicked.connect(self._on_remove)
        btn_layout.addWidget(self.remove_btn)

        self.apply_btn = QPushButton("Apply")
        self.apply_btn.setMinimumWidth(80)
        self.apply_btn.clicked.connect(self._on_apply)
        btn_layout.addWidget(self.apply_btn)

        layout.addWidget(btn_frame)

    def _on_generate(self):
        self.generate_requested.emit(self.resolution_slider.value())

    def _on_add(self):
        dlg = AddACMEntryDialog(self._links, self)
        entry = dlg.get_entry()
        if entry and entry[0] and entry[1]:
            self.add_entry(*entry)
            self.entry_added.emit(*entry)

    def _on_remove(self):
        rows = set(idx.row() for idx in self.table.selectedIndexes())
        for row in sorted(rows, reverse=True):
            link1 = self.table.item(row, 0).text()
            link2 = self.table.item(row, 1).text()
            self.table.removeRow(row)
            self.entry_removed.emit(link1, link2)

    def _on_apply(self):
        self.matrix_applied.emit()

    def add_entry(self, link1: str, link2: str, reason: str = ""):
        """Add an entry to the table."""
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(link1))
        self.table.setItem(row, 1, QTableWidgetItem(link2))
        self.table.setItem(row, 2, QTableWidgetItem(reason))

    def clear(self):
        """Clear all entries."""
        self.table.setRowCount(0)

    def set_entries(self, entries: list[tuple[str, str, str]]):
        """Set ACM entries from list of (link1, link2, reason)."""
        self.clear()
        for link1, link2, reason in entries:
            self.add_entry(link1, link2, reason)

    def get_entries(self) -> list[tuple[str, str, str]]:
        """Get all entries as list of (link1, link2, reason)."""
        entries = []
        for row in range(self.table.rowCount()):
            link1 = self.table.item(row, 0).text()
            link2 = self.table.item(row, 1).text()
            reason = self.table.item(row, 2).text()
            entries.append((link1, link2, reason))
        return entries
