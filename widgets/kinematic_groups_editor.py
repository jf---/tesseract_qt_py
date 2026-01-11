"""Kinematic groups editor widget."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QFrame,
    QLabel,
    QLineEdit,
    QTabWidget,
    QComboBox,
    QPushButton,
    QListWidget,
    QAbstractItemView,
    QSpacerItem,
    QSizePolicy,
)


class KinematicGroupsEditorWidget(QWidget):
    """Editor for kinematic groups."""

    group_added = Signal(str, str, object)  # name, type, data
    group_removed = Signal(str)  # name
    group_modified = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()

    def _connect_signals(self):
        self.addJointPushButton.clicked.connect(self._on_add_joint)
        self.removeJointPushButton.clicked.connect(self._on_remove_joint)
        self.addLinkPushButton.clicked.connect(self._on_add_link)
        self.removeLinkPushButton.clicked.connect(self._on_remove_link)
        self.addGroupPushButton.clicked.connect(self._on_add_group)
        self.removeGroupPushButton.clicked.connect(self._on_remove_group)
        self.applyPushButton.clicked.connect(self._on_apply)

    def _on_add_joint(self):
        joint = self.jointComboBox.currentText()
        if joint and joint not in [
            self.jointListWidget.item(i).text() for i in range(self.jointListWidget.count())
        ]:
            self.jointListWidget.addItem(joint)

    def _on_remove_joint(self):
        for item in self.jointListWidget.selectedItems():
            self.jointListWidget.takeItem(self.jointListWidget.row(item))

    def _on_add_link(self):
        link = self.linkComboBox.currentText()
        if link and link not in [
            self.linkListWidget.item(i).text() for i in range(self.linkListWidget.count())
        ]:
            self.linkListWidget.addItem(link)

    def _on_remove_link(self):
        for item in self.linkListWidget.selectedItems():
            self.linkListWidget.takeItem(self.linkListWidget.row(item))

    def _on_add_group(self):
        name = self.groupNameLineEdit.text().strip()
        if not name:
            return
        tab = self.kinGroupTabWidget.currentIndex()
        if tab == 0:  # CHAIN
            data = (self.baseLinkNameComboBox.currentText(), self.tipLinkNameComboBox.currentText())
            self.group_added.emit(name, "chain", data)
        elif tab == 1:  # JOINTS
            joints = [
                self.jointListWidget.item(i).text() for i in range(self.jointListWidget.count())
            ]
            self.group_added.emit(name, "joints", joints)
        else:  # LINKS
            links = [self.linkListWidget.item(i).text() for i in range(self.linkListWidget.count())]
            self.group_added.emit(name, "links", links)

    def _on_remove_group(self):
        name = self.groupNameLineEdit.text().strip()
        if name:
            self.group_removed.emit(name)

    def _on_apply(self):
        self.group_modified.emit()

    def set_links(self, links: list[str]):
        for combo in [self.baseLinkNameComboBox, self.tipLinkNameComboBox, self.linkComboBox]:
            combo.clear()
            combo.addItems(sorted(links))

    def set_joints(self, joints: list[str]):
        self.jointComboBox.clear()
        self.jointComboBox.addItems(sorted(joints))

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Top frame: Group name
        top_frame = QFrame()
        top_frame.setFrameShape(QFrame.Shape.NoFrame)
        top_layout = QHBoxLayout(top_frame)
        top_layout.setContentsMargins(0, 0, 0, 0)

        self.groupNameLabel = QLabel("Group Name:")
        top_layout.addWidget(self.groupNameLabel)

        self.groupNameLineEdit = QLineEdit()
        top_layout.addWidget(self.groupNameLineEdit)

        layout.addWidget(top_frame)

        # Tab widget
        self.kinGroupTabWidget = QTabWidget()
        self.kinGroupTabWidget.setCurrentIndex(2)

        # CHAIN tab
        chain_tab = QWidget()
        chain_layout = QGridLayout(chain_tab)
        chain_layout.setRowStretch(2, 0)
        chain_layout.setColumnStretch(0, 0)
        chain_layout.setColumnStretch(1, 1)

        self.baseLinkNameLabel = QLabel("Base Link:")
        chain_layout.addWidget(self.baseLinkNameLabel, 0, 0)

        self.baseLinkNameComboBox = QComboBox()
        chain_layout.addWidget(self.baseLinkNameComboBox, 0, 1)

        self.tipLinkNameLabel = QLabel("Tip Link:")
        chain_layout.addWidget(self.tipLinkNameLabel, 1, 0)

        self.tipLinkNameComboBox = QComboBox()
        chain_layout.addWidget(self.tipLinkNameComboBox, 1, 1)

        chain_spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        chain_layout.addItem(chain_spacer, 2, 0)

        self.kinGroupTabWidget.addTab(chain_tab, "CHAIN")

        # JOINTS tab
        joints_tab = QWidget()
        joints_layout = QGridLayout(joints_tab)
        joints_layout.setColumnStretch(0, 0)
        joints_layout.setColumnStretch(1, 1)
        joints_layout.setColumnStretch(2, 0)
        joints_layout.setColumnStretch(3, 0)

        self.jointLabel = QLabel("Joint:")
        joints_layout.addWidget(self.jointLabel, 0, 0)

        self.jointComboBox = QComboBox()
        joints_layout.addWidget(self.jointComboBox, 0, 1)

        self.addJointPushButton = QPushButton("Add Joint")
        self.addJointPushButton.setMinimumWidth(100)
        joints_layout.addWidget(self.addJointPushButton, 0, 2)

        self.removeJointPushButton = QPushButton("Remove Joint")
        self.removeJointPushButton.setMinimumWidth(100)
        joints_layout.addWidget(self.removeJointPushButton, 0, 3)

        self.jointListWidget = QListWidget()
        self.jointListWidget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        joints_layout.addWidget(self.jointListWidget, 1, 0, 1, 4)

        self.kinGroupTabWidget.addTab(joints_tab, "JOINTS")

        # LINKS tab
        links_tab = QWidget()
        links_layout = QGridLayout(links_tab)
        links_layout.setColumnStretch(0, 0)
        links_layout.setColumnStretch(1, 1)
        links_layout.setColumnStretch(2, 0)
        links_layout.setColumnStretch(3, 0)

        self.linkLabel = QLabel("Link:")
        links_layout.addWidget(self.linkLabel, 0, 0)

        self.linkComboBox = QComboBox()
        links_layout.addWidget(self.linkComboBox, 0, 1)

        self.addLinkPushButton = QPushButton("Add Link")
        self.addLinkPushButton.setMinimumWidth(100)
        links_layout.addWidget(self.addLinkPushButton, 0, 2)

        self.removeLinkPushButton = QPushButton("Remove Link")
        self.removeLinkPushButton.setMinimumWidth(100)
        links_layout.addWidget(self.removeLinkPushButton, 0, 3)

        self.linkListWidget = QListWidget()
        self.linkListWidget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        links_layout.addWidget(self.linkListWidget, 1, 0, 1, 4)

        self.kinGroupTabWidget.addTab(links_tab, "LINKS")

        layout.addWidget(self.kinGroupTabWidget)

        # Bottom frame: Action buttons
        bottom_frame = QFrame()
        bottom_frame.setFrameShape(QFrame.Shape.NoFrame)
        bottom_layout = QHBoxLayout(bottom_frame)
        bottom_layout.setContentsMargins(0, 0, 0, 0)

        bottom_spacer = QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        bottom_layout.addItem(bottom_spacer)

        self.addGroupPushButton = QPushButton("Add Group")
        self.addGroupPushButton.setMinimumWidth(100)
        bottom_layout.addWidget(self.addGroupPushButton)

        self.removeGroupPushButton = QPushButton("Remove Group")
        self.removeGroupPushButton.setMinimumWidth(100)
        bottom_layout.addWidget(self.removeGroupPushButton)

        self.applyPushButton = QPushButton("Apply")
        bottom_layout.addWidget(self.applyPushButton)

        layout.addWidget(bottom_frame)

        # Kinematic groups widget (placeholder)
        self.kinGroupsWidget = QWidget()
        self.kinGroupsWidget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        layout.addWidget(self.kinGroupsWidget, 1)
