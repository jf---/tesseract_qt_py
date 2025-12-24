"""Scene graph tree widget."""
from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTreeWidget,
    QTreeWidgetItem,
    QHeaderView,
    QMenu,
    QLineEdit,
)
from PySide6.QtGui import QAction


class SceneTreeWidget(QWidget):
    """Tree view of scene graph links and joints."""

    linkSelected = Signal(str)  # link name
    linkVisibilityChanged = Signal(str, bool)  # link name, visible
    linkFrameToggled = Signal(str, bool)  # link name, show frame
    linkDeleteRequested = Signal(str)  # link name

    def __init__(self, parent=None):
        super().__init__(parent)
        self._env = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Search filter
        self.search = QLineEdit()
        self.search.setPlaceholderText("Filter...")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._on_filter)
        layout.addWidget(self.search)

        # Tree widget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Name", "Type"])
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.setAlternatingRowColors(True)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._on_context_menu)
        self.tree.itemSelectionChanged.connect(self._on_selection_changed)
        self.tree.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self.tree)

    def load_environment(self, env):
        """Load scene graph from environment."""
        self._env = env
        self.tree.clear()

        scene_graph = env.getSceneGraph()
        root_link = scene_graph.getRoot()

        # Build tree recursively
        root_item = self._create_link_item(root_link, scene_graph)
        self.tree.addTopLevelItem(root_item)
        root_item.setExpanded(True)

        # Expand first few levels
        self._expand_levels(root_item, 2)

    def _create_link_item(self, link_name: str, scene_graph) -> QTreeWidgetItem:
        """Create tree item for link and its children."""
        link = scene_graph.getLink(link_name)

        item = QTreeWidgetItem()
        item.setText(0, link_name)
        item.setText(1, "Link")
        item.setData(0, Qt.ItemDataRole.UserRole, ("link", link_name))
        item.setCheckState(0, Qt.CheckState.Checked)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)

        # Add joints and child links
        for joint in scene_graph.getOutboundJoints(link_name):
            joint_item = QTreeWidgetItem()
            joint_item.setText(0, joint.getName())
            joint_item.setText(1, self._joint_type_str(joint.type))
            joint_item.setData(0, Qt.ItemDataRole.UserRole, ("joint", joint.getName()))
            item.addChild(joint_item)

            # Add child link
            child_link_item = self._create_link_item(joint.child_link_name, scene_graph)
            joint_item.addChild(child_link_item)

        return item

    def _joint_type_str(self, joint_type) -> str:
        """Convert joint type to string."""
        return str(joint_type).split(".")[-1].title()

    def _expand_levels(self, item: QTreeWidgetItem, levels: int):
        """Expand tree to specified depth."""
        if levels <= 0:
            return
        item.setExpanded(True)
        for i in range(item.childCount()):
            self._expand_levels(item.child(i), levels - 1)

    def _on_filter(self, text: str):
        """Filter tree items by name."""
        self._set_item_visibility(self.tree.invisibleRootItem(), text.lower())

    def _set_item_visibility(self, item: QTreeWidgetItem, filter_text: str) -> bool:
        """Recursively set item visibility based on filter."""
        # Check children first
        any_child_visible = False
        for i in range(item.childCount()):
            child = item.child(i)
            if self._set_item_visibility(child, filter_text):
                any_child_visible = True

        # Check this item
        if item.parent() is not None:  # Skip root
            text = item.text(0).lower()
            matches = not filter_text or filter_text in text
            visible = matches or any_child_visible
            item.setHidden(not visible)
            if matches and filter_text:
                item.setExpanded(True)
            return visible

        return True

    def _on_selection_changed(self):
        """Handle selection change."""
        items = self.tree.selectedItems()
        if items:
            data = items[0].data(0, Qt.ItemDataRole.UserRole)
            if data and data[0] == "link":
                self.linkSelected.emit(data[1])

    def _on_item_changed(self, item: QTreeWidgetItem, column: int):
        """Handle item check state change."""
        if column == 0:
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if data and data[0] == "link":
                visible = item.checkState(0) == Qt.CheckState.Checked
                self.linkVisibilityChanged.emit(data[1], visible)

    def _on_context_menu(self, pos):
        """Show context menu."""
        item = self.tree.itemAt(pos)
        if not item:
            return

        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return

        menu = QMenu(self)

        if data[0] == "link":
            link_name = data[1]

            # Delete Link
            action_delete = QAction("Delete Link", self)
            action_delete.triggered.connect(lambda: self.linkDeleteRequested.emit(link_name))
            menu.addAction(action_delete)

            # Toggle Visibility
            is_visible = item.checkState(0) == Qt.CheckState.Checked
            action_toggle = QAction("Toggle Visibility", self)
            action_toggle.triggered.connect(lambda: self.linkVisibilityChanged.emit(link_name, not is_visible))
            menu.addAction(action_toggle)

            # Show Frame
            action_frame = QAction("Show Frame", self)
            action_frame.triggered.connect(lambda: self.linkFrameToggled.emit(link_name, True))
            menu.addAction(action_frame)

        menu.exec_(self.tree.mapToGlobal(pos))

    def _show_only(self, link_name: str):
        """Hide all links except specified."""
        self._set_all_visibility(self.tree.invisibleRootItem(), False)
        self.linkVisibilityChanged.emit(link_name, True)

    def _show_all(self):
        """Show all links."""
        self._set_all_visibility(self.tree.invisibleRootItem(), True)

    def _set_all_visibility(self, item: QTreeWidgetItem, visible: bool):
        """Set visibility for all link items."""
        for i in range(item.childCount()):
            child = item.child(i)
            data = child.data(0, Qt.ItemDataRole.UserRole)
            if data and data[0] == "link":
                child.setCheckState(0, Qt.CheckState.Checked if visible else Qt.CheckState.Unchecked)
            self._set_all_visibility(child, visible)

    def select_link(self, link_name: str):
        """Select link in tree."""
        item = self._find_link_item(self.tree.invisibleRootItem(), link_name)
        if item:
            self.tree.setCurrentItem(item)
            self.tree.scrollToItem(item)

    def _find_link_item(self, parent: QTreeWidgetItem, link_name: str) -> QTreeWidgetItem | None:
        """Find item for link name."""
        for i in range(parent.childCount()):
            child = parent.child(i)
            data = child.data(0, Qt.ItemDataRole.UserRole)
            if data and data[0] == "link" and data[1] == link_name:
                return child
            result = self._find_link_item(child, link_name)
            if result:
                return result
        return None
