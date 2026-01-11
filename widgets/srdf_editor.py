"""SRDF editor widget."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QToolBox,
    QVBoxLayout,
    QWidget,
)


class AllowedCollisionMatrixEditorWidget(QWidget):
    """Placeholder for ACM editor."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        label = QLabel("Allowed Collision Matrix Editor\n(Coming Soon)")
        layout.addWidget(label)
        layout.addStretch()


class KinematicGroupsEditorWidget(QWidget):
    """Placeholder for kinematic groups editor."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        label = QLabel("Kinematic Groups Editor\n(Coming Soon)")
        layout.addWidget(label)
        layout.addStretch()


class GroupJointStatesEditorWidget(QWidget):
    """Placeholder for group joint states editor."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        label = QLabel("Group Joint States Editor\n(Coming Soon)")
        layout.addWidget(label)
        layout.addStretch()


class SRDFEditorWidget(QWidget):
    """SRDF editor widget with toolbox interface."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(3, 3, 3, 3)

        # Main toolbox
        self.toolbox = QToolBox()
        self.toolbox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Page 1: Load URDF/SRDF
        load_page = QWidget()
        load_page.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        load_layout = QVBoxLayout(load_page)
        load_layout.setContentsMargins(3, 3, 3, 3)

        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.NoFrame)
        frame.setFrameShadow(QFrame.Shadow.Raised)
        grid = QGridLayout(frame)

        # URDF file row
        urdf_label = QLabel("URDF FIle:")
        self.urdf_line_edit = QLineEdit()
        self.urdf_line_edit.setReadOnly(True)
        self.urdf_browse_button = QPushButton("Browse")
        self.urdf_browse_button.setMinimumWidth(80)

        grid.addWidget(urdf_label, 0, 0)
        grid.addWidget(self.urdf_line_edit, 0, 1)
        grid.addWidget(self.urdf_browse_button, 0, 2)

        # SRDF file row
        srdf_label = QLabel("SRDF File:")
        self.srdf_line_edit = QLineEdit()
        self.srdf_line_edit.setReadOnly(True)
        self.srdf_browse_button = QPushButton("Browse")
        self.srdf_browse_button.setMinimumWidth(80)

        grid.addWidget(srdf_label, 1, 0)
        grid.addWidget(self.srdf_line_edit, 1, 1)
        grid.addWidget(self.srdf_browse_button, 1, 2)

        # Load button
        self.load_push_button = QPushButton("Load")
        self.load_push_button.setMinimumWidth(80)
        grid.addWidget(self.load_push_button, 2, 2)

        load_layout.addWidget(frame)
        load_layout.addItem(
            QSpacerItem(20, 37, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        # Page 2: ACM
        acm_page = QWidget()
        acm_page.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        acm_layout = QVBoxLayout(acm_page)
        acm_layout.setContentsMargins(3, 3, 3, 3)
        self.acm_widget = AllowedCollisionMatrixEditorWidget()
        self.acm_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        acm_layout.addWidget(self.acm_widget)

        # Page 3: Kinematic Groups
        groups_page = QWidget()
        groups_page.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        groups_layout = QVBoxLayout(groups_page)
        groups_layout.setContentsMargins(3, 3, 3, 3)
        self.groups_widget = KinematicGroupsEditorWidget()
        self.groups_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        groups_layout.addWidget(self.groups_widget)

        # Page 4: Group Joint States
        states_page = QWidget()
        states_page.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        states_layout = QVBoxLayout(states_page)
        states_layout.setContentsMargins(3, 3, 3, 3)
        self.group_states_widget = GroupJointStatesEditorWidget()
        self.group_states_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        states_layout.addWidget(self.group_states_widget)

        # Page 5: Save
        save_page = QWidget()
        save_page.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        save_layout = QGridLayout(save_page)
        save_layout.setContentsMargins(3, 3, 3, 3)

        # SRDF file row
        save_srdf_label = QLabel("SRDF File:")
        self.save_srdf_line_edit = QLineEdit()
        self.save_srdf_line_edit.setReadOnly(True)
        self.save_srdf_browse_button = QPushButton("Browse")
        self.save_srdf_browse_button.setMinimumWidth(80)

        save_layout.addWidget(save_srdf_label, 4, 0)
        save_layout.addWidget(self.save_srdf_line_edit, 4, 1)
        save_layout.addWidget(self.save_srdf_browse_button, 4, 2)

        # Save button
        self.save_srdf_save_button = QPushButton("Save")
        self.save_srdf_save_button.setMinimumWidth(80)
        save_layout.addWidget(self.save_srdf_save_button, 5, 2)

        # Spacer
        save_layout.addItem(
            QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding), 6, 2
        )

        # Add pages to toolbox
        self.toolbox.addItem(load_page, "Load URDF/SRDF")
        self.toolbox.addItem(acm_page, "Allowed Collision Matrix")
        self.toolbox.addItem(groups_page, "Kinematic Groups")
        self.toolbox.addItem(states_page, "Kinematic Group Joint States")
        self.toolbox.addItem(save_page, "Save")

        # Set default page (index 4 = Save)
        self.toolbox.setCurrentIndex(4)

        layout.addWidget(self.toolbox)
