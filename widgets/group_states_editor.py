"""Group states editor widget."""

from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QHeaderView,
    QAbstractItemView,
    QSpacerItem,
    QSizePolicy,
)


class GroupStatesEditorWidget(QWidget):
    """Editor for group states."""

    state_added = Signal(str, str, dict)  # group, name, values
    state_removed = Signal(str, str)  # group, name
    state_applied = Signal(str, str)  # group, name

    def __init__(self, parent=None):
        super().__init__(parent)
        self._groups = []
        self._states = {}  # {group: {state_name: {joint: value}}}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Group selector
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("Group:"))
        self.group_combo = QComboBox()
        self.group_combo.currentTextChanged.connect(self._on_group_changed)
        top_layout.addWidget(self.group_combo, stretch=1)
        layout.addLayout(top_layout)

        # States table
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["State Name", "Joint Values"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self.table)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addItem(
            QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )

        self.btn_add = QPushButton("Add State")
        self.btn_add.setMinimumWidth(100)
        self.btn_add.clicked.connect(self._on_add_state)
        btn_layout.addWidget(self.btn_add)

        self.btn_remove = QPushButton("Remove State")
        self.btn_remove.setMinimumWidth(100)
        self.btn_remove.clicked.connect(self._on_remove_state)
        btn_layout.addWidget(self.btn_remove)

        self.btn_apply = QPushButton("Apply State")
        self.btn_apply.setMinimumWidth(100)
        self.btn_apply.clicked.connect(self._on_apply_state)
        btn_layout.addWidget(self.btn_apply)

        layout.addLayout(btn_layout)

    def set_groups(self, groups: list[str]):
        """Set available groups."""
        self._groups = groups
        self.group_combo.clear()
        self.group_combo.addItems(groups)

    def set_states(self, states: dict[str, dict[str, dict]]):
        """Set states dict: {group: {state_name: {joint: value}}}."""
        self._states = states
        self._refresh_table()

    def get_states(self) -> dict[str, dict[str, dict]]:
        """Get current states dict."""
        return self._states

    def _on_group_changed(self):
        """Handle group selection change."""
        self._refresh_table()

    def _refresh_table(self):
        """Refresh table for current group."""
        self.table.blockSignals(True)
        self.table.setRowCount(0)

        group = self.group_combo.currentText()
        if not group or group not in self._states:
            self.table.blockSignals(False)
            return

        states = self._states[group]
        self.table.setRowCount(len(states))

        for row, (name, values) in enumerate(sorted(states.items())):
            name_item = QTableWidgetItem(name)
            values_str = ", ".join(f"{j}={v:.3f}" for j, v in sorted(values.items()))
            values_item = QTableWidgetItem(values_str)
            values_item.setFlags(values_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, values_item)

        self.table.blockSignals(False)

    def _on_item_changed(self, item):
        """Handle table item edit (rename state)."""
        if item.column() != 0:
            return

        group = self.group_combo.currentText()
        if not group:
            return

        row = item.row()
        old_names = sorted(self._states[group].keys())
        if row >= len(old_names):
            return

        old_name = old_names[row]
        new_name = item.text().strip()
        if not new_name or new_name == old_name:
            return

        # Rename state
        values = self._states[group].pop(old_name)
        self._states[group][new_name] = values
        self._refresh_table()

    def _on_add_state(self):
        """Add new state."""
        group = self.group_combo.currentText()
        if not group:
            return

        if group not in self._states:
            self._states[group] = {}

        # Create unique name
        i = 1
        while f"state_{i}" in self._states[group]:
            i += 1
        name = f"state_{i}"

        values = {}
        self._states[group][name] = values
        self.state_added.emit(group, name, values)
        self._refresh_table()

    def _on_remove_state(self):
        """Remove selected state."""
        group = self.group_combo.currentText()
        if not group or group not in self._states:
            return

        row = self.table.currentRow()
        if row < 0:
            return

        name = sorted(self._states[group].keys())[row]
        self._states[group].pop(name)
        self.state_removed.emit(group, name)
        self._refresh_table()

    def _on_apply_state(self):
        """Apply selected state."""
        group = self.group_combo.currentText()
        if not group or group not in self._states:
            return

        row = self.table.currentRow()
        if row < 0:
            return

        name = sorted(self._states[group].keys())[row]
        self.state_applied.emit(group, name)
