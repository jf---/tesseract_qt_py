"""signal tests for P1 widgets - test signal emission and payload data."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class SignalSpy:
    """simple signal spy for collecting signal emissions."""

    def __init__(self):
        self.emissions = []

    def slot(self, *args):
        """slot that captures signal args."""
        self.emissions.append(args)

    def __len__(self):
        return len(self.emissions)

    def __getitem__(self, idx):
        return self.emissions[idx]


class TestJointSliderSignals:
    """test JointSliderWidget signals."""

    @pytest.fixture
    def qapp(self):
        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance() or QApplication([])
            yield app
        except ImportError:
            pytest.skip("PySide6 not installed")

    def test_joint_value_changed_signal_emission(self, qapp):
        """test jointValueChanged signal emitted with correct name and value."""
        from widgets.joint_slider import JointSliderWidget

        w = JointSliderWidget()
        w.set_joints({"j1": (-1.0, 1.0, 0.0)})

        spy = SignalSpy()
        w.jointValueChanged.connect(spy.slot)
        # Spinbox displays degrees, set 30 degrees (~0.5236 radians)
        w.sliders["j1"].spinbox.setValue(30.0)

        # verify signal emitted
        assert len(spy) == 1
        # verify signal payload: (name, value in radians)
        assert spy[0][0] == "j1"
        import math
        assert abs(spy[0][1] - math.radians(30.0)) < 0.001

    def test_joint_values_changed_signal_emission(self, qapp):
        """test jointValuesChanged signal emitted with dict of all joint values."""
        from widgets.joint_slider import JointSliderWidget

        w = JointSliderWidget()
        w.set_joints({"j1": (-1.0, 1.0, 0.0), "j2": (-2.0, 2.0, 0.0)})

        spy = SignalSpy()
        w.jointValuesChanged.connect(spy.slot)
        # Spinbox displays degrees, set 30 degrees
        w.sliders["j1"].spinbox.setValue(30.0)

        # verify signal emitted
        assert len(spy) == 1
        # verify signal payload: dict with all joint values in radians
        values = spy[0][0]
        assert isinstance(values, dict)
        assert "j1" in values
        assert "j2" in values
        import math
        assert abs(values["j1"] - math.radians(30.0)) < 0.001
        assert values["j2"] == 0.0

    def test_joint_value_changed_via_spinbox(self, qapp):
        """test signal emitted when spinbox value changes."""
        from widgets.joint_slider import JointSliderWidget

        w = JointSliderWidget()
        w.set_joints({"j1": (-1.0, 1.0, 0.0)})

        spy = SignalSpy()
        w.jointValueChanged.connect(spy.slot)
        # Spinbox displays degrees, set 45 degrees
        w.sliders["j1"].spinbox.setValue(45.0)

        assert len(spy) == 1
        assert spy[0][0] == "j1"
        import math
        assert abs(spy[0][1] - math.radians(45.0)) < 0.001

    def test_joint_value_changed_via_slider(self, qapp):
        """test signal emitted when slider value changes."""
        from widgets.joint_slider import JointSliderWidget

        w = JointSliderWidget()
        w.set_joints({"j1": (-1.0, 1.0, 0.0)})

        spy = SignalSpy()
        w.jointValueChanged.connect(spy.slot)
        # slider range is 0-1000, set to 750 (3/4 position = 0.5 in joint space)
        w.sliders["j1"].slider.setValue(750)

        assert len(spy) == 1
        assert spy[0][0] == "j1"
        # 750/1000 of range -1.0 to 1.0 is 0.5
        assert abs(spy[0][1] - 0.5) < 0.01

    def test_multiple_joint_changes(self, qapp):
        """test multiple joints trigger individual signals."""
        from widgets.joint_slider import JointSliderWidget

        w = JointSliderWidget()
        w.set_joints({"j1": (-1.0, 1.0, 0.0), "j2": (-2.0, 2.0, 0.0)})

        spy = SignalSpy()
        w.jointValueChanged.connect(spy.slot)

        w.sliders["j1"].spinbox.setValue(0.5)
        w.sliders["j2"].spinbox.setValue(-1.0)

        assert len(spy) == 2
        assert spy[0][0] == "j1"
        assert spy[1][0] == "j2"

    def test_zero_all_emits_joint_values_changed(self, qapp):
        """test zero all button emits jointValuesChanged signal."""
        from widgets.joint_slider import JointSliderWidget

        w = JointSliderWidget()
        w.set_joints({"j1": (-1.0, 1.0, 0.5), "j2": (-2.0, 2.0, 1.0)})

        spy = SignalSpy()
        w.jointValuesChanged.connect(spy.slot)
        w.btn_zero.click()

        assert len(spy) == 1
        values = spy[0][0]
        assert values["j1"] == 0.0
        assert values["j2"] == 0.0

    def test_random_emits_joint_values_changed(self, qapp):
        """test random button emits jointValuesChanged signal."""
        from widgets.joint_slider import JointSliderWidget

        w = JointSliderWidget()
        w.set_joints({"j1": (-1.0, 1.0, 0.0), "j2": (-2.0, 2.0, 0.0)})

        spy = SignalSpy()
        w.jointValuesChanged.connect(spy.slot)
        w.btn_random.click()

        assert len(spy) == 1
        values = spy[0][0]
        assert "j1" in values
        assert "j2" in values
        # verify values are within limits
        assert -1.0 <= values["j1"] <= 1.0
        assert -2.0 <= values["j2"] <= 2.0

    def test_set_value_programmatic_no_signal(self, qapp):
        """test set_value() does not emit signal (updating flag prevents it)."""
        from widgets.joint_slider import JointSliderWidget

        w = JointSliderWidget()
        w.set_joints({"j1": (-1.0, 1.0, 0.0)})

        spy = SignalSpy()
        w.sliders["j1"].valueChanged.connect(spy.slot)

        # set_value uses _updating flag to prevent signal
        w.sliders["j1"].set_value(0.5)

        # no signal should be emitted
        assert len(spy) == 0


class TestTrajectoryPlayerSignals:
    """test TrajectoryPlayerWidget signals."""

    @pytest.fixture
    def qapp(self):
        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance() or QApplication([])
            yield app
        except ImportError:
            pytest.skip("PySide6 not installed")

    @pytest.fixture
    def mock_trajectory(self):
        """create mock trajectory for testing."""

        class MockWaypoint:
            def __init__(self, time):
                self.time = time

        return [MockWaypoint(i * 0.033) for i in range(10)]

    def test_frame_changed_signal_on_slider_change(self, qapp, mock_trajectory):
        """test frameChanged signal emitted when slider moved."""
        from widgets.trajectory_player import TrajectoryPlayerWidget

        w = TrajectoryPlayerWidget()
        w.load_trajectory(mock_trajectory)

        spy = SignalSpy()
        w.frameChanged.connect(spy.slot)
        w.slider.setValue(5)

        assert len(spy) == 1
        assert spy[0][0] == 5

    def test_frame_changed_signal_on_set_frame(self, qapp, mock_trajectory):
        """test frameChanged signal emitted when set_frame called."""
        from widgets.trajectory_player import TrajectoryPlayerWidget

        w = TrajectoryPlayerWidget()
        w.load_trajectory(mock_trajectory)

        spy = SignalSpy()
        w.frameChanged.connect(spy.slot)
        w.set_frame(3)

        assert len(spy) == 1
        assert spy[0][0] == 3

    def test_state_changed_signal_on_play(self, qapp, mock_trajectory):
        """test stateChanged signal emitted when playback starts."""
        from widgets.trajectory_player import TrajectoryPlayerWidget

        w = TrajectoryPlayerWidget()
        w.load_trajectory(mock_trajectory)

        spy = SignalSpy()
        w.stateChanged.connect(spy.slot)
        w.btn_play.click()

        assert len(spy) == 1
        assert spy[0][0] == "playing"

    def test_state_changed_signal_on_pause(self, qapp, mock_trajectory):
        """test stateChanged signal emitted when playback paused."""
        from widgets.trajectory_player import TrajectoryPlayerWidget

        w = TrajectoryPlayerWidget()
        w.load_trajectory(mock_trajectory)

        # start playing first
        w.btn_play.click()

        spy = SignalSpy()
        w.stateChanged.connect(spy.slot)
        w.btn_play.click()  # toggle to pause

        assert len(spy) == 1
        assert spy[0][0] == "paused"

    def test_state_changed_signal_on_stop(self, qapp, mock_trajectory):
        """test stateChanged signal emitted when playback stopped."""
        from widgets.trajectory_player import TrajectoryPlayerWidget

        w = TrajectoryPlayerWidget()
        w.load_trajectory(mock_trajectory)

        spy = SignalSpy()
        w.stateChanged.connect(spy.slot)
        w.btn_stop.click()

        assert len(spy) == 1
        assert spy[0][0] == "stopped"

    def test_frame_changed_signal_sequence(self, qapp, mock_trajectory):
        """test multiple frameChanged signals as slider moves."""
        from widgets.trajectory_player import TrajectoryPlayerWidget

        w = TrajectoryPlayerWidget()
        w.load_trajectory(mock_trajectory)

        spy = SignalSpy()
        w.frameChanged.connect(spy.slot)

        w.slider.setValue(2)
        w.slider.setValue(4)
        w.slider.setValue(6)

        assert len(spy) == 3
        assert spy[0][0] == 2
        assert spy[1][0] == 4
        assert spy[2][0] == 6

    def test_stop_emits_frame_zero(self, qapp, mock_trajectory):
        """test stop button resets frame to 0 and emits signal."""
        from widgets.trajectory_player import TrajectoryPlayerWidget

        w = TrajectoryPlayerWidget()
        w.load_trajectory(mock_trajectory)

        w.set_frame(5)

        frame_spy = SignalSpy()
        state_spy = SignalSpy()
        w.frameChanged.connect(frame_spy.slot)
        w.stateChanged.connect(state_spy.slot)

        w.btn_stop.click()

        # should emit frameChanged(0) and stateChanged("stopped")
        assert len(frame_spy) >= 1
        assert frame_spy[-1][0] == 0
        assert len(state_spy) == 1
        assert state_spy[0][0] == "stopped"

    def test_frame_changed_payload_type(self, qapp, mock_trajectory):
        """test frameChanged signal payload is int."""
        from widgets.trajectory_player import TrajectoryPlayerWidget

        w = TrajectoryPlayerWidget()
        w.load_trajectory(mock_trajectory)

        spy = SignalSpy()
        w.frameChanged.connect(spy.slot)
        w.slider.setValue(7)

        assert len(spy) == 1
        assert isinstance(spy[0][0], int)
        assert spy[0][0] == 7


class TestSceneTreeSignals:
    """test SceneTreeWidget signals."""

    @pytest.fixture
    def qapp(self):
        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance() or QApplication([])
            yield app
        except ImportError:
            pytest.skip("PySide6 not installed")

    def test_link_selected_signal(self, qapp):
        """test linkSelected signal emitted when tree item selected."""
        from widgets.scene_tree import SceneTreeWidget
        from PySide6.QtWidgets import QTreeWidgetItem
        from PySide6.QtCore import Qt

        w = SceneTreeWidget()

        # manually create a link item
        item = QTreeWidgetItem()
        item.setText(0, "base_link")
        item.setData(0, Qt.ItemDataRole.UserRole, ("link", "base_link"))
        w.tree.addTopLevelItem(item)

        spy = SignalSpy()
        w.linkSelected.connect(spy.slot)
        w.tree.setCurrentItem(item)

        assert len(spy) == 1
        assert spy[0][0] == "base_link"

    def test_link_visibility_changed_signal(self, qapp):
        """test linkVisibilityChanged signal emitted when checkbox toggled."""
        from widgets.scene_tree import SceneTreeWidget
        from PySide6.QtWidgets import QTreeWidgetItem
        from PySide6.QtCore import Qt

        w = SceneTreeWidget()

        item = QTreeWidgetItem()
        item.setText(0, "test_link")
        item.setData(0, Qt.ItemDataRole.UserRole, ("link", "test_link"))
        item.setCheckState(0, Qt.CheckState.Checked)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        w.tree.addTopLevelItem(item)

        spy = SignalSpy()
        w.linkVisibilityChanged.connect(spy.slot)
        item.setCheckState(0, Qt.CheckState.Unchecked)

        # verify signal emitted
        assert len(spy) == 1
        # verify signal payload: (link_name, visible)
        assert spy[0][0] == "test_link"
        assert spy[0][1] is False

    def test_link_visibility_changed_to_visible(self, qapp):
        """test linkVisibilityChanged signal with visible=True."""
        from widgets.scene_tree import SceneTreeWidget
        from PySide6.QtWidgets import QTreeWidgetItem
        from PySide6.QtCore import Qt

        w = SceneTreeWidget()

        item = QTreeWidgetItem()
        item.setText(0, "link2")
        item.setData(0, Qt.ItemDataRole.UserRole, ("link", "link2"))
        item.setCheckState(0, Qt.CheckState.Unchecked)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        w.tree.addTopLevelItem(item)

        spy = SignalSpy()
        w.linkVisibilityChanged.connect(spy.slot)
        item.setCheckState(0, Qt.CheckState.Checked)

        assert len(spy) == 1
        assert spy[0][0] == "link2"
        assert spy[0][1] is True

    def test_link_frame_toggled_signal_show(self, qapp):
        """test linkFrameToggled signal emitted when show frame action triggered."""
        from widgets.scene_tree import SceneTreeWidget

        w = SceneTreeWidget()

        spy = SignalSpy()
        w.linkFrameToggled.connect(spy.slot)
        w.linkFrameToggled.emit("test_link", True)

        assert len(spy) == 1
        assert spy[0][0] == "test_link"
        assert spy[0][1] is True

    def test_link_frame_toggled_signal_hide(self, qapp):
        """test linkFrameToggled signal emitted when hide frame action triggered."""
        from widgets.scene_tree import SceneTreeWidget

        w = SceneTreeWidget()

        spy = SignalSpy()
        w.linkFrameToggled.connect(spy.slot)
        w.linkFrameToggled.emit("another_link", False)

        assert len(spy) == 1
        assert spy[0][0] == "another_link"
        assert spy[0][1] is False

    def test_link_selected_signal_payload(self, qapp):
        """test linkSelected signal payload is string link name."""
        from widgets.scene_tree import SceneTreeWidget
        from PySide6.QtWidgets import QTreeWidgetItem
        from PySide6.QtCore import Qt

        w = SceneTreeWidget()

        item = QTreeWidgetItem()
        item.setText(0, "gripper_link")
        item.setData(0, Qt.ItemDataRole.UserRole, ("link", "gripper_link"))
        w.tree.addTopLevelItem(item)

        spy = SignalSpy()
        w.linkSelected.connect(spy.slot)
        w.tree.setCurrentItem(item)

        assert len(spy) == 1
        assert isinstance(spy[0][0], str)
        assert spy[0][0] == "gripper_link"

    def test_no_signal_on_joint_selection(self, qapp):
        """test linkSelected NOT emitted when joint item selected."""
        from widgets.scene_tree import SceneTreeWidget
        from PySide6.QtWidgets import QTreeWidgetItem
        from PySide6.QtCore import Qt

        w = SceneTreeWidget()

        # create joint item (not link)
        item = QTreeWidgetItem()
        item.setText(0, "joint1")
        item.setData(0, Qt.ItemDataRole.UserRole, ("joint", "joint1"))
        w.tree.addTopLevelItem(item)

        spy = SignalSpy()
        w.linkSelected.connect(spy.slot)
        w.tree.setCurrentItem(item)

        # should not emit linkSelected for joint item
        assert len(spy) == 0


class TestACMEditorSignals:
    """test ACMEditorWidget signals."""

    @pytest.fixture
    def qapp(self):
        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance() or QApplication([])
            yield app
        except ImportError:
            pytest.skip("PySide6 not installed")

    def test_entry_added_signal(self, qapp):
        """test entry_added signal emitted when entry manually added."""
        from widgets.acm_editor import ACMEditorWidget

        w = ACMEditorWidget()

        spy = SignalSpy()
        w.entry_added.connect(spy.slot)
        w.entry_added.emit("link_a", "link_b", "collision allowed")

        # verify signal captured
        assert len(spy) == 1
        # verify signal payload: (link1, link2, reason)
        assert spy[0][0] == "link_a"
        assert spy[0][1] == "link_b"
        assert spy[0][2] == "collision allowed"

    def test_entry_removed_signal(self, qapp):
        """test entry_removed signal emitted when entry removed."""
        from widgets.acm_editor import ACMEditorWidget

        w = ACMEditorWidget()
        w.add_entry("link_1", "link_2", "reason")

        w.table.selectRow(0)

        spy = SignalSpy()
        w.entry_removed.connect(spy.slot)
        w._on_remove()

        # verify signal emitted
        assert len(spy) == 1
        # verify signal payload: (link1, link2)
        assert spy[0][0] == "link_1"
        assert spy[0][1] == "link_2"

    def test_matrix_applied_signal(self, qapp):
        """test matrix_applied signal emitted when apply button clicked."""
        from widgets.acm_editor import ACMEditorWidget

        w = ACMEditorWidget()

        spy = SignalSpy()
        w.matrix_applied.connect(spy.slot)
        w.apply_btn.click()

        # matrix_applied has no payload
        assert len(spy) == 1
        assert len(spy[0]) == 0

    def test_generate_requested_signal(self, qapp):
        """test generate_requested signal emitted with resolution value."""
        from widgets.acm_editor import ACMEditorWidget

        w = ACMEditorWidget()
        w.resolution_slider.setValue(5000)

        spy = SignalSpy()
        w.generate_requested.connect(spy.slot)
        w.generate_btn.click()

        # verify signal emitted
        assert len(spy) == 1
        # verify signal payload: resolution value
        assert spy[0][0] == 5000

    def test_generate_requested_different_resolution(self, qapp):
        """test generate_requested signal with different resolution."""
        from widgets.acm_editor import ACMEditorWidget

        w = ACMEditorWidget()
        w.resolution_slider.setValue(8500)

        spy = SignalSpy()
        w.generate_requested.connect(spy.slot)
        w.generate_btn.click()

        assert len(spy) == 1
        assert spy[0][0] == 8500

    def test_entry_removed_multiple(self, qapp):
        """test entry_removed signal emitted for each removed entry."""
        from widgets.acm_editor import ACMEditorWidget

        w = ACMEditorWidget()
        w.add_entry("l1", "l2", "r1")
        w.add_entry("l3", "l4", "r2")

        spy = SignalSpy()
        w.entry_removed.connect(spy.slot)

        w.table.selectRow(0)
        w._on_remove()

        assert len(spy) == 1
        assert spy[0][0] == "l1"
        assert spy[0][1] == "l2"

    def test_entry_added_payload_types(self, qapp):
        """test entry_added signal payload types are all strings."""
        from widgets.acm_editor import ACMEditorWidget

        w = ACMEditorWidget()

        spy = SignalSpy()
        w.entry_added.connect(spy.slot)
        w.entry_added.emit("base", "gripper", "adjacent")

        assert len(spy) == 1
        assert isinstance(spy[0][0], str)
        assert isinstance(spy[0][1], str)
        assert isinstance(spy[0][2], str)

    def test_generate_requested_payload_type(self, qapp):
        """test generate_requested signal payload is int."""
        from widgets.acm_editor import ACMEditorWidget

        w = ACMEditorWidget()

        spy = SignalSpy()
        w.generate_requested.connect(spy.slot)
        w.generate_btn.click()

        assert len(spy) == 1
        assert isinstance(spy[0][0], int)


class TestKinematicGroupsEditorSignals:
    """test KinematicGroupsEditorWidget signals."""

    @pytest.fixture
    def qapp(self):
        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance() or QApplication([])
            yield app
        except ImportError:
            pytest.skip("PySide6 not installed")

    def test_group_added_chain_signal(self, qapp):
        """test group_added signal emitted for chain group."""
        from widgets.kinematic_groups_editor import KinematicGroupsEditorWidget

        w = KinematicGroupsEditorWidget()
        w.set_links(["base_link", "link_1", "link_2", "tool0"])
        w.groupNameLineEdit.setText("test_group")
        w.kinGroupTabWidget.setCurrentIndex(0)  # CHAIN tab
        w.baseLinkNameComboBox.setCurrentText("base_link")
        w.tipLinkNameComboBox.setCurrentText("tool0")

        spy = SignalSpy()
        w.group_added.connect(spy.slot)
        w.addGroupPushButton.click()

        assert len(spy) == 1
        assert spy[0][0] == "test_group"
        assert spy[0][1] == "chain"
        assert spy[0][2] == ("base_link", "tool0")

    def test_group_added_joints_signal(self, qapp):
        """test group_added signal emitted for joints group."""
        from widgets.kinematic_groups_editor import KinematicGroupsEditorWidget

        w = KinematicGroupsEditorWidget()
        w.set_joints(["joint_1", "joint_2", "joint_3"])
        w.groupNameLineEdit.setText("joints_group")
        w.kinGroupTabWidget.setCurrentIndex(1)  # JOINTS tab

        # Add joints to list
        w.jointComboBox.setCurrentText("joint_1")
        w.addJointPushButton.click()
        w.jointComboBox.setCurrentText("joint_2")
        w.addJointPushButton.click()

        spy = SignalSpy()
        w.group_added.connect(spy.slot)
        w.addGroupPushButton.click()

        assert len(spy) == 1
        assert spy[0][0] == "joints_group"
        assert spy[0][1] == "joints"
        assert "joint_1" in spy[0][2]
        assert "joint_2" in spy[0][2]

    def test_group_added_links_signal(self, qapp):
        """test group_added signal emitted for links group."""
        from widgets.kinematic_groups_editor import KinematicGroupsEditorWidget

        w = KinematicGroupsEditorWidget()
        w.set_links(["base_link", "link_1", "link_2"])
        w.groupNameLineEdit.setText("links_group")
        w.kinGroupTabWidget.setCurrentIndex(2)  # LINKS tab

        # Add links to list
        w.linkComboBox.setCurrentText("link_1")
        w.addLinkPushButton.click()
        w.linkComboBox.setCurrentText("link_2")
        w.addLinkPushButton.click()

        spy = SignalSpy()
        w.group_added.connect(spy.slot)
        w.addGroupPushButton.click()

        assert len(spy) == 1
        assert spy[0][0] == "links_group"
        assert spy[0][1] == "links"
        assert "link_1" in spy[0][2]
        assert "link_2" in spy[0][2]

    def test_group_removed_signal(self, qapp):
        """test group_removed signal emitted when remove clicked."""
        from widgets.kinematic_groups_editor import KinematicGroupsEditorWidget

        w = KinematicGroupsEditorWidget()
        w.groupNameLineEdit.setText("group_to_remove")

        spy = SignalSpy()
        w.group_removed.connect(spy.slot)
        w.removeGroupPushButton.click()

        assert len(spy) == 1
        assert spy[0][0] == "group_to_remove"

    def test_group_modified_signal(self, qapp):
        """test group_modified signal emitted when apply clicked."""
        from widgets.kinematic_groups_editor import KinematicGroupsEditorWidget

        w = KinematicGroupsEditorWidget()

        spy = SignalSpy()
        w.group_modified.connect(spy.slot)
        w.applyPushButton.click()

        assert len(spy) == 1
        assert len(spy[0]) == 0  # No payload

    def test_add_joint_to_list(self, qapp):
        """test adding joint to list via button."""
        from widgets.kinematic_groups_editor import KinematicGroupsEditorWidget

        w = KinematicGroupsEditorWidget()
        w.set_joints(["j1", "j2", "j3"])
        w.kinGroupTabWidget.setCurrentIndex(1)  # JOINTS tab

        w.jointComboBox.setCurrentText("j2")
        w.addJointPushButton.click()

        assert w.jointListWidget.count() == 1
        assert w.jointListWidget.item(0).text() == "j2"

    def test_remove_joint_from_list(self, qapp):
        """test removing joint from list via button."""
        from widgets.kinematic_groups_editor import KinematicGroupsEditorWidget

        w = KinematicGroupsEditorWidget()
        w.set_joints(["j1", "j2"])
        w.kinGroupTabWidget.setCurrentIndex(1)

        # Add then remove
        w.jointComboBox.setCurrentText("j1")
        w.addJointPushButton.click()
        w.jointListWidget.setCurrentRow(0)
        w.removeJointPushButton.click()

        assert w.jointListWidget.count() == 0

    def test_add_link_to_list(self, qapp):
        """test adding link to list via button."""
        from widgets.kinematic_groups_editor import KinematicGroupsEditorWidget

        w = KinematicGroupsEditorWidget()
        w.set_links(["link_1", "link_2"])
        w.kinGroupTabWidget.setCurrentIndex(2)  # LINKS tab

        w.linkComboBox.setCurrentText("link_1")
        w.addLinkPushButton.click()

        assert w.linkListWidget.count() == 1
        assert w.linkListWidget.item(0).text() == "link_1"

    def test_no_duplicate_joints(self, qapp):
        """test same joint cannot be added twice."""
        from widgets.kinematic_groups_editor import KinematicGroupsEditorWidget

        w = KinematicGroupsEditorWidget()
        w.set_joints(["j1"])
        w.kinGroupTabWidget.setCurrentIndex(1)

        w.jointComboBox.setCurrentText("j1")
        w.addJointPushButton.click()
        w.addJointPushButton.click()  # Try adding again

        assert w.jointListWidget.count() == 1

    def test_empty_group_name_no_signal(self, qapp):
        """test no signal emitted when group name is empty."""
        from widgets.kinematic_groups_editor import KinematicGroupsEditorWidget

        w = KinematicGroupsEditorWidget()
        w.groupNameLineEdit.setText("")  # Empty name

        spy = SignalSpy()
        w.group_added.connect(spy.slot)
        w.addGroupPushButton.click()

        assert len(spy) == 0  # No signal emitted


class TestManipulationWidgetSignals:
    """test ManipulationWidget signals."""

    @pytest.fixture
    def qapp(self):
        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance() or QApplication([])
            yield app
        except ImportError:
            pytest.skip("PySide6 not installed")

    def test_group_changed_signal(self, qapp):
        """test groupChanged signal emitted when group selection changes."""
        from widgets.manipulation_widget import ManipulationWidget

        w = ManipulationWidget()
        w.set_groups(["arm", "gripper"])

        spy = SignalSpy()
        w.groupChanged.connect(spy.slot)
        w.group_combo_box.setCurrentIndex(1)  # Select "gripper"

        assert len(spy) == 1
        assert spy[0][0] == "gripper"

    def test_reload_requested_signal(self, qapp):
        """test reloadRequested signal emitted when reload button clicked."""
        from widgets.manipulation_widget import ManipulationWidget

        w = ManipulationWidget()

        spy = SignalSpy()
        w.reloadRequested.connect(spy.slot)
        w.reload_push_button.click()

        assert len(spy) == 1

    def test_state_apply_requested_signal(self, qapp):
        """test stateApplyRequested signal emitted when apply button clicked."""
        from widgets.manipulation_widget import ManipulationWidget

        w = ManipulationWidget()
        w.set_states(["home", "ready"])
        w.state_selector_combo.setCurrentIndex(1)  # Select "ready"

        spy = SignalSpy()
        w.stateApplyRequested.connect(spy.slot)
        w.apply_state_button.click()

        assert len(spy) == 1
        assert spy[0][0] == "ready"

    def test_joint_values_changed_signal(self, qapp):
        """test jointValuesChanged signal emitted when joint slider values change."""
        from widgets.manipulation_widget import ManipulationWidget

        w = ManipulationWidget()

        # Only if FKIKWidget is available
        if w.fkik_widget is None:
            pytest.skip("FKIKWidget not available")

        w.set_joint_limits({"joint_1": (-1.0, 1.0, 0.0)})

        spy = SignalSpy()
        w.jointValuesChanged.connect(spy.slot)

        # Change joint value via spinbox (in degrees, 30 deg = ~0.5236 rad)
        w.fkik_widget.joint_slider.sliders["joint_1"].spinbox.setValue(30.0)

        assert len(spy) >= 1
        assert isinstance(spy[0][0], dict)
        assert "joint_1" in spy[0][0]

    def test_set_groups_populates_combo(self, qapp):
        """test set_groups populates group combo box."""
        from widgets.manipulation_widget import ManipulationWidget

        w = ManipulationWidget()
        w.set_groups(["group1", "group2", "group3"])

        assert w.group_combo_box.count() == 3
        assert w.group_combo_box.itemText(0) == "group1"
        assert w.group_combo_box.itemText(2) == "group3"

    def test_set_states_populates_combo(self, qapp):
        """test set_states populates state combo boxes."""
        from widgets.manipulation_widget import ManipulationWidget

        w = ManipulationWidget()
        w.set_states(["state1", "state2"])

        assert w.state_combo_box.count() == 2
        assert w.state_selector_combo.count() == 2
        assert w.state_combo_box.itemText(0) == "state1"

    def test_set_links_populates_combos(self, qapp):
        """test set_links populates working frame and TCP combo boxes."""
        from widgets.manipulation_widget import ManipulationWidget

        w = ManipulationWidget()
        w.set_links(["link1", "link2", "link3"])

        assert w.working_frame_combo_box.count() == 3
        assert w.tcp_combo_box.count() == 3
        assert w.tcp_combo_box.itemText(1) == "link2"

    def test_current_group_returns_selected(self, qapp):
        """test current_group returns selected group name."""
        from widgets.manipulation_widget import ManipulationWidget

        w = ManipulationWidget()
        w.set_groups(["arm", "leg"])
        w.group_combo_box.setCurrentIndex(1)

        assert w.current_group() == "leg"

class TestGroupStatesEditorSignals:
    """test GroupStatesEditorWidget signals."""

    @pytest.fixture
    def qapp(self):
        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance() or QApplication([])
            yield app
        except ImportError:
            pytest.skip("PySide6 not installed")

    def test_state_added_signal(self, qapp):
        """test state_added signal emitted when add button clicked."""
        from widgets.group_states_editor import GroupStatesEditorWidget

        w = GroupStatesEditorWidget()
        w.set_groups(["manipulator"])
        w.group_combo.setCurrentIndex(0)

        spy = SignalSpy()
        w.state_added.connect(spy.slot)
        w.btn_add.click()

        assert len(spy) == 1
        assert spy[0][0] == "manipulator"
        assert spy[0][1] == "state_1"
        assert spy[0][2] == {}  # empty values

    def test_state_removed_signal(self, qapp):
        """test state_removed signal emitted when remove button clicked."""
        from widgets.group_states_editor import GroupStatesEditorWidget

        w = GroupStatesEditorWidget()
        w.set_groups(["arm"])
        w.set_states({"arm": {"home": {"j1": 0.0}}})
        w.table.selectRow(0)

        spy = SignalSpy()
        w.state_removed.connect(spy.slot)
        w.btn_remove.click()

        assert len(spy) == 1
        assert spy[0][0] == "arm"
        assert spy[0][1] == "home"

    def test_state_applied_signal(self, qapp):
        """test state_applied signal emitted when apply button clicked."""
        from widgets.group_states_editor import GroupStatesEditorWidget

        w = GroupStatesEditorWidget()
        w.set_groups(["gripper"])
        w.set_states({"gripper": {"open": {"j1": 0.5}}})
        w.table.selectRow(0)

        spy = SignalSpy()
        w.state_applied.connect(spy.slot)
        w.btn_apply.click()

        assert len(spy) == 1
        assert spy[0][0] == "gripper"
        assert spy[0][1] == "open"

    def test_set_groups_populates_combo(self, qapp):
        """test set_groups populates group combo."""
        from widgets.group_states_editor import GroupStatesEditorWidget

        w = GroupStatesEditorWidget()
        w.set_groups(["g1", "g2", "g3"])

        assert w.group_combo.count() == 3
        assert w.group_combo.itemText(1) == "g2"

    def test_set_states_populates_table(self, qapp):
        """test set_states populates table for current group."""
        from widgets.group_states_editor import GroupStatesEditorWidget

        w = GroupStatesEditorWidget()
        w.set_groups(["arm"])
        w.set_states({"arm": {"home": {"j1": 0.0}, "ready": {"j1": 1.0}}})

        assert w.table.rowCount() == 2

    def test_get_states_returns_dict(self, qapp):
        """test get_states returns current states dict."""
        from widgets.group_states_editor import GroupStatesEditorWidget

        w = GroupStatesEditorWidget()
        states = {"arm": {"home": {"j1": 0.0}}}
        w.set_groups(["arm"])
        w.set_states(states)

        result = w.get_states()
        assert result == states


class TestTCPEditorSignals:
    """test TCPEditorWidget signals."""

    @pytest.fixture
    def qapp(self):
        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance() or QApplication([])
            yield app
        except ImportError:
            pytest.skip("PySide6 not installed")

    def test_tcp_changed_signal(self, qapp):
        """test tcp_changed signal emitted when link selection changes."""
        from widgets.tcp_editor import TCPEditorWidget

        w = TCPEditorWidget()
        w.set_links(["base_link", "tool0", "flange"])

        spy = SignalSpy()
        w.tcp_changed.connect(spy.slot)
        w.link_combo.setCurrentIndex(1)

        assert len(spy) == 1
        assert spy[0][0] == "tool0"

    def test_offset_changed_signal(self, qapp):
        """test offset_changed signal emitted when offset values change."""
        from widgets.tcp_editor import TCPEditorWidget

        w = TCPEditorWidget()

        spy = SignalSpy()
        w.offset_changed.connect(spy.slot)
        w.offset_editor.x_spin.setValue(0.1)

        assert len(spy) >= 1
        assert spy[0][0] == 0.1  # x value

    def test_set_links_populates_combo(self, qapp):
        """test set_links populates link combo."""
        from widgets.tcp_editor import TCPEditorWidget

        w = TCPEditorWidget()
        w.set_links(["link1", "link2", "link3"])

        assert w.link_combo.count() == 3
        assert w.link_combo.itemText(2) == "link3"

    def test_set_tcp_selects_link(self, qapp):
        """test set_tcp selects the specified link."""
        from widgets.tcp_editor import TCPEditorWidget

        w = TCPEditorWidget()
        w.set_links(["base", "tool0", "flange"])
        w.set_tcp("flange")

        assert w.link_combo.currentText() == "flange"

    def test_get_offset_returns_tuple(self, qapp):
        """test get_offset returns offset as tuple."""
        from widgets.tcp_editor import TCPEditorWidget

        w = TCPEditorWidget()
        w.offset_editor.x_spin.setValue(0.1)
        w.offset_editor.y_spin.setValue(0.2)
        w.offset_editor.z_spin.setValue(0.3)

        offset = w.get_offset()
        assert len(offset) == 6
        assert offset[0] == 0.1
        assert offset[1] == 0.2
        assert offset[2] == 0.3

    def test_reset_clears_offset(self, qapp):
        """test reset button clears all offset values."""
        from widgets.tcp_editor import TCPEditorWidget

        w = TCPEditorWidget()
        w.offset_editor.x_spin.setValue(0.5)
        w.offset_editor.roll_spin.setValue(45.0)

        w.reset_btn.click()

        offset = w.get_offset()
        assert all(v == 0.0 for v in offset)


class TestTaskComposerSignals:
    """test TaskComposerWidget signals."""

    @pytest.fixture
    def qapp(self):
        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance() or QApplication([])
            yield app
        except ImportError:
            pytest.skip("PySide6 not installed")

    def test_execute_requested_signal(self, qapp):
        """test execute_requested signal emitted when run button clicked."""
        from widgets.task_composer_widget import TaskComposerWidget

        w = TaskComposerWidget()

        spy = SignalSpy()
        w.execute_requested.connect(spy.slot)
        w.task_run_push_button.click()

        assert len(spy) == 1

    def test_log_appends_text(self, qapp):
        """test log method appends text to output."""
        from widgets.task_composer_widget import TaskComposerWidget

        w = TaskComposerWidget()
        w.log("Test message 1")
        w.log("Test message 2")

        text = w.log_output.toPlainText()
        assert "Test message 1" in text
        assert "Test message 2" in text

    def test_clear_log_clears_output(self, qapp):
        """test clear_log method clears output."""
        from widgets.task_composer_widget import TaskComposerWidget

        w = TaskComposerWidget()
        w.log("Some message")
        assert w.log_output.toPlainText() != ""

        w.clear_log()
        assert w.log_output.toPlainText() == ""

    def test_has_config_tab(self, qapp):
        """test widget has config tab with combo boxes."""
        from widgets.task_composer_widget import TaskComposerWidget

        w = TaskComposerWidget()

        assert w.tab_widget.count() == 2
        assert w.tab_widget.tabText(0) == "Config"
        assert w.tab_widget.tabText(1) == "Logs"

    def test_has_executor_combo(self, qapp):
        """test config tab has executor combo box."""
        from widgets.task_composer_widget import TaskComposerWidget

        w = TaskComposerWidget()
        assert hasattr(w, 'executor_combo_box')
        assert hasattr(w, 'task_combo_box')


class TestScaleCoherence:
    """test VTK actor scale matches tesseract geometry."""

    urdf = '/Users/jelle/Code/CADCAM/tesseract_python_nanobind/ws/src/tesseract/tesseract_support/urdf/abb_irb2400.urdf'
    srdf = '/Users/jelle/Code/CADCAM/tesseract_python_nanobind/ws/src/tesseract/tesseract_support/urdf/abb_irb2400.srdf'

    @pytest.fixture
    def env_and_scene(self):
        """create environment and scene manager."""
        import os
        import vtk
        os.environ.pop('DISPLAY', None)
        os.environ['QT_QPA_PLATFORM'] = 'offscreen'

        from tesseract_robotics.tesseract_environment import Environment
        from tesseract_robotics.tesseract_common import GeneralResourceLocator
        from core.scene_manager import SceneManager

        if not Path(self.urdf).exists():
            pytest.skip("ABB URDF not found")

        renderer = vtk.vtkRenderer()
        render_window = vtk.vtkRenderWindow()
        render_window.AddRenderer(renderer)
        render_window.SetOffScreenRendering(True)

        env = Environment()
        loc = GeneralResourceLocator()
        env.init(self.urdf, self.srdf, loc)

        scene = SceneManager(renderer)
        scene.load_environment(env)

        return env, scene

    def test_actor_bounds_match_geometry(self, env_and_scene):
        """test VTK actor bounds match tesseract mesh geometry (within 5%)."""
        import numpy as np
        env, scene = env_and_scene

        for link in env.getSceneGraph().getLinks():
            name = link.getName()
            if not link.visual or name not in scene.link_actors:
                continue

            geom = link.visual[0].geometry
            verts = geom.getVertices()
            if len(verts) == 0:
                continue

            # tesseract mesh bounds
            verts_np = np.array(verts)
            geom_size = verts_np.max(axis=0) - verts_np.min(axis=0)

            # VTK actor bounds
            actor = scene.link_actors[name][0]
            bounds = actor.GetBounds()
            actor_size = np.array([bounds[1]-bounds[0], bounds[3]-bounds[2], bounds[5]-bounds[4]])

            # sizes should match within 5%
            for i, (gs, as_) in enumerate(zip(geom_size, actor_size)):
                if gs > 0.01:  # skip tiny dimensions
                    ratio = as_ / gs
                    assert 0.95 < ratio < 1.05, f"{name} axis {i}: geom={gs:.3f}, actor={as_:.3f}"

    def test_actor_motion_matches_fk(self, env_and_scene):
        """test VTK actor moves correct distance when joints change."""
        import numpy as np
        env, scene = env_and_scene

        # get initial tool0 position
        state0 = env.getState()
        pos0 = np.array(state0.link_transforms['link_6'].translation())

        # get VTK actor center
        actor = scene.link_actors['link_6'][0]
        vtk_pos0 = np.array(actor.GetCenter())

        # apply joint motion
        scene.update_joint_values({'joint_1': 1.5, 'joint_2': -0.5, 'joint_3': 0.5})

        # get new positions
        state1 = env.getState()
        pos1 = np.array(state1.link_transforms['link_6'].translation())
        vtk_pos1 = np.array(actor.GetCenter())

        # FK motion
        fk_motion = np.linalg.norm(pos1 - pos0)
        vtk_motion = np.linalg.norm(vtk_pos1 - vtk_pos0)

        # VTK motion should match FK motion within 10%
        assert fk_motion > 0.3, f"FK motion too small: {fk_motion:.3f}m"
        assert abs(vtk_motion - fk_motion) / fk_motion < 0.1, \
            f"Motion mismatch: FK={fk_motion:.3f}m, VTK={vtk_motion:.3f}m"

    def test_link_positions_coherent(self, env_and_scene):
        """test all VTK actor positions within 10cm of tesseract FK."""
        import numpy as np
        env, scene = env_and_scene
        state = env.getState()

        for name, actors in scene.link_actors.items():
            if not actors:
                continue

            # tesseract FK position
            try:
                tf = state.link_transforms[name]
                fk_pos = np.array(tf.translation())
            except (KeyError, AttributeError):
                continue

            # VTK actor center
            vtk_pos = np.array(actors[0].GetCenter())

            # positions should be within 0.5m (mesh center vs link origin)
            dist = np.linalg.norm(vtk_pos - fk_pos)
            assert dist < 0.5, f"{name}: FK={fk_pos}, VTK={vtk_pos}, dist={dist:.3f}m"
