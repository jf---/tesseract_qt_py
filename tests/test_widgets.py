"""widget tests - verify widgets create and basic ops work."""
import pytest
from pathlib import Path
import sys

# add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# ACMEditorWidget tests
def test_acm_create_widget(qtbot):
    from widgets.acm_editor import ACMEditorWidget
    w = ACMEditorWidget()
    qtbot.addWidget(w)
    assert w.table.rowCount() == 0


def test_acm_add_entry(qtbot):
    from widgets.acm_editor import ACMEditorWidget
    w = ACMEditorWidget()
    qtbot.addWidget(w)
    w.add_entry("link_a", "link_b", "test reason")
    assert w.table.rowCount() == 1
    assert w.table.item(0, 0).text() == "link_a"
    assert w.table.item(0, 1).text() == "link_b"
    assert w.table.item(0, 2).text() == "test reason"


def test_acm_remove_entry(qtbot):
    from widgets.acm_editor import ACMEditorWidget
    w = ACMEditorWidget()
    qtbot.addWidget(w)
    w.add_entry("link_a", "link_b", "reason")
    w.add_entry("link_c", "link_d", "reason2")
    assert w.table.rowCount() == 2

    # select first row and remove
    w.table.selectRow(0)
    w._on_remove()
    assert w.table.rowCount() == 1
    assert w.table.item(0, 0).text() == "link_c"


def test_acm_signals_exist(qtbot):
    from widgets.acm_editor import ACMEditorWidget
    w = ACMEditorWidget()
    qtbot.addWidget(w)
    # verify signals defined
    assert hasattr(w, 'entry_added')
    assert hasattr(w, 'entry_removed')
    assert hasattr(w, 'matrix_applied')
    assert hasattr(w, 'generate_requested')


def test_acm_get_entries(qtbot):
    from widgets.acm_editor import ACMEditorWidget
    w = ACMEditorWidget()
    qtbot.addWidget(w)
    w.add_entry("l1", "l2", "r1")
    w.add_entry("l3", "l4", "r2")
    entries = w.get_entries()
    assert len(entries) == 2
    assert entries[0] == ("l1", "l2", "r1")
    assert entries[1] == ("l3", "l4", "r2")


def test_acm_clear(qtbot):
    from widgets.acm_editor import ACMEditorWidget
    w = ACMEditorWidget()
    qtbot.addWidget(w)
    w.add_entry("l1", "l2", "r1")
    w.clear()
    assert w.table.rowCount() == 0


# SRDFEditorWidget tests
def test_srdf_create_widget(qtbot):
    from widgets.srdf_editor import SRDFEditorWidget
    w = SRDFEditorWidget()
    qtbot.addWidget(w)
    assert w.toolbox is not None


def test_srdf_page_count(qtbot):
    from widgets.srdf_editor import SRDFEditorWidget
    w = SRDFEditorWidget()
    qtbot.addWidget(w)
    assert w.toolbox.count() == 5


def test_srdf_page_navigation(qtbot):
    from widgets.srdf_editor import SRDFEditorWidget
    w = SRDFEditorWidget()
    qtbot.addWidget(w)
    # default is page 4 (save)
    assert w.toolbox.currentIndex() == 4

    # switch to ACM page (index 1)
    w.toolbox.setCurrentIndex(1)
    assert w.toolbox.currentIndex() == 1

    # switch to kinematic groups (index 2)
    w.toolbox.setCurrentIndex(2)
    assert w.toolbox.currentIndex() == 2


def test_srdf_ui_elements_exist(qtbot):
    from widgets.srdf_editor import SRDFEditorWidget
    w = SRDFEditorWidget()
    qtbot.addWidget(w)
    assert w.urdf_line_edit is not None
    assert w.srdf_line_edit is not None
    assert w.urdf_browse_button is not None
    assert w.load_push_button is not None
    assert w.save_srdf_save_button is not None


# CartesianEditorWidget tests
def test_cartesian_create_widget(qtbot):
    from widgets.cartesian_editor import CartesianEditorWidget
    w = CartesianEditorWidget()
    qtbot.addWidget(w)
    assert w.x_spin is not None
    assert w.y_spin is not None
    assert w.z_spin is not None


def test_cartesian_position_defaults(qtbot):
    from widgets.cartesian_editor import CartesianEditorWidget
    w = CartesianEditorWidget()
    qtbot.addWidget(w)
    assert w.x_spin.value() == 0.0
    assert w.y_spin.value() == 0.0
    assert w.z_spin.value() == 0.0


def test_cartesian_position_value_changes(qtbot):
    from widgets.cartesian_editor import CartesianEditorWidget
    w = CartesianEditorWidget()
    qtbot.addWidget(w)
    w.x_spin.setValue(1.5)
    w.y_spin.setValue(-2.3)
    w.z_spin.setValue(0.75)
    assert w.x_spin.value() == 1.5
    assert w.y_spin.value() == -2.3
    assert w.z_spin.value() == 0.75


def test_cartesian_orientation_defaults(qtbot):
    from widgets.cartesian_editor import CartesianEditorWidget
    w = CartesianEditorWidget()
    qtbot.addWidget(w)
    assert w.roll_spin.value() == 0.0
    assert w.pitch_spin.value() == 0.0
    assert w.yaw_spin.value() == 0.0
    assert w.quat_w_spin.value() == 1.0
    assert w.quat_x_spin.value() == 0.0


def test_cartesian_orientation_value_changes(qtbot):
    from widgets.cartesian_editor import CartesianEditorWidget
    w = CartesianEditorWidget()
    qtbot.addWidget(w)
    w.roll_spin.setValue(0.5)
    w.pitch_spin.setValue(-0.3)
    w.yaw_spin.setValue(1.2)
    assert w.roll_spin.value() == 0.5
    assert w.pitch_spin.value() == -0.3
    assert w.yaw_spin.value() == 1.2


# ContactComputeWidget tests
def test_contact_create_widget(qtbot):
    from widgets.contact_compute_widget import ContactComputeWidget
    w = ContactComputeWidget()
    qtbot.addWidget(w)
    assert w.contact_threshold is not None


def test_contact_threshold_default(qtbot):
    from widgets.contact_compute_widget import ContactComputeWidget
    w = ContactComputeWidget()
    qtbot.addWidget(w)
    assert w.contact_threshold.value() == 0.0


def test_contact_threshold_value_change(qtbot):
    from widgets.contact_compute_widget import ContactComputeWidget
    w = ContactComputeWidget()
    qtbot.addWidget(w)
    w.contact_threshold.setValue(0.05)
    assert w.contact_threshold.value() == 0.05


def test_contact_test_type(qtbot):
    from widgets.contact_compute_widget import ContactComputeWidget
    w = ContactComputeWidget()
    qtbot.addWidget(w)
    assert w.contact_test_type.count() == 3
    assert w.contact_test_type.currentText() == "First"
    w.contact_test_type.setCurrentIndex(2)
    assert w.contact_test_type.currentText() == "All"


def test_contact_checkboxes_default(qtbot):
    from widgets.contact_compute_widget import ContactComputeWidget
    w = ContactComputeWidget()
    qtbot.addWidget(w)
    assert w.calc_penetration.isChecked()
    assert w.calc_distance.isChecked()


def test_contact_buttons_exist(qtbot):
    from widgets.contact_compute_widget import ContactComputeWidget
    w = ContactComputeWidget()
    qtbot.addWidget(w)
    assert w.btn_check_state is not None
    assert w.btn_compute is not None


# StudioMainWindow tests
def test_studio_create_window(qtbot):
    from widgets.studio_layout import StudioMainWindow
    w = StudioMainWindow()
    qtbot.addWidget(w)
    assert w.windowTitle() == "MainWindow"


def test_studio_menu_actions_exist(qtbot):
    from widgets.studio_layout import StudioMainWindow
    w = StudioMainWindow()
    qtbot.addWidget(w)
    assert w.action_load_config is not None
    assert w.action_save_config is not None
    assert w.action_save_config_as is not None
    assert w.action_restore_state is not None
    assert w.action_save_state is not None
    assert w.action_create_perspective is not None
    assert w.action_load_plugins is not None


def test_studio_menu_shortcuts(qtbot):
    from widgets.studio_layout import StudioMainWindow
    from PySide6.QtGui import QKeySequence
    w = StudioMainWindow()
    qtbot.addWidget(w)
    assert w.action_load_config.shortcut() == QKeySequence("Ctrl+O")
    assert w.action_save_config.shortcut() == QKeySequence("Ctrl+S")
    assert w.action_save_config_as.shortcut() == QKeySequence("Ctrl+Shift+S")


def test_studio_save_config_disabled_by_default(qtbot):
    from widgets.studio_layout import StudioMainWindow
    w = StudioMainWindow()
    qtbot.addWidget(w)
    assert not w.action_save_config.isEnabled()


def test_studio_menus_exist(qtbot):
    from widgets.studio_layout import StudioMainWindow
    w = StudioMainWindow()
    qtbot.addWidget(w)
    menubar = w.menuBar()
    actions = menubar.actions()
    menu_titles = [action.text() for action in actions]
    assert "File" in menu_titles
    assert "View" in menu_titles
    assert "Tools" in menu_titles


# InfoPanel tests
def test_info_create_widget(qtbot):
    from widgets.info_panel import RobotInfoPanel
    w = RobotInfoPanel()
    qtbot.addWidget(w)
    assert w.name_label is not None
    assert w.dof_label is not None
    assert w.joint_table is not None
    assert w.tcp_xyz_label is not None
    assert w.tcp_rpy_label is not None


def test_info_initial_state(qtbot):
    from widgets.info_panel import RobotInfoPanel
    w = RobotInfoPanel()
    qtbot.addWidget(w)
    assert w.name_label.text() == "Name: -"
    assert w.dof_label.text() == "DOF: 0"
    assert w.tcp_xyz_label.text() == "XYZ: -"
    assert w.tcp_rpy_label.text() == "RPY: -"


def test_info_joint_table_columns(qtbot):
    from widgets.info_panel import RobotInfoPanel
    w = RobotInfoPanel()
    qtbot.addWidget(w)
    assert w.joint_table.columnCount() == 4
    headers = [w.joint_table.horizontalHeaderItem(i).text() for i in range(4)]
    assert headers == ["Joint", "Value", "Min", "Max"]


def test_info_set_tcp_link(qtbot):
    from widgets.info_panel import RobotInfoPanel
    w = RobotInfoPanel()
    qtbot.addWidget(w)
    w.set_tcp_link("tool_link")
    assert w._tcp_link == "tool_link"


# JointSlider tests
def test_joint_slider_create(qtbot):
    from widgets.joint_slider import JointSlider
    s = JointSlider("joint_1", -1.57, 1.57, 0.0)
    qtbot.addWidget(s)
    assert s.name == "joint_1"
    assert s.lower == -1.57
    assert s.upper == 1.57
    assert s.value() == 0.0


def test_joint_slider_value_clamping(qtbot):
    from widgets.joint_slider import JointSlider
    s = JointSlider("j", -1.0, 1.0, 0.0)
    qtbot.addWidget(s)
    s.set_value(2.0)
    assert s.value() == 1.0
    s.set_value(-2.0)
    assert s.value() == -1.0


def test_joint_slider_components(qtbot):
    from widgets.joint_slider import JointSlider
    s = JointSlider("j", 0.0, 10.0)
    qtbot.addWidget(s)
    assert s.label is not None
    assert s.slider is not None
    assert s.spinbox is not None


def test_joint_slider_widget_create(qtbot):
    from widgets.joint_slider import JointSliderWidget
    w = JointSliderWidget()
    qtbot.addWidget(w)
    assert w.btn_zero is not None
    assert w.btn_random is not None
    assert len(w.sliders) == 0


def test_joint_slider_widget_set_joints(qtbot):
    from widgets.joint_slider import JointSliderWidget
    w = JointSliderWidget()
    qtbot.addWidget(w)
    joints = {"j1": (-1.0, 1.0, 0.0), "j2": (-2.0, 2.0, 0.5)}
    w.set_joints(joints)
    assert len(w.sliders) == 2
    assert "j1" in w.sliders
    assert "j2" in w.sliders


def test_joint_slider_widget_get_values(qtbot):
    from widgets.joint_slider import JointSliderWidget
    w = JointSliderWidget()
    qtbot.addWidget(w)
    w.set_joints({"j1": (-1.0, 1.0, 0.0), "j2": (-2.0, 2.0, 0.5)})
    values = w.get_values()
    assert values["j1"] == 0.0
    assert values["j2"] == 0.5


def test_joint_slider_widget_set_values(qtbot):
    from widgets.joint_slider import JointSliderWidget
    w = JointSliderWidget()
    qtbot.addWidget(w)
    w.set_joints({"j1": (-1.0, 1.0, 0.0), "j2": (-2.0, 2.0, 0.0)})
    w.set_values({"j1": 0.5, "j2": -0.75})
    assert w.sliders["j1"].value() == 0.5
    assert w.sliders["j2"].value() == -0.75


# TrajectoryPlayer tests
def test_trajectory_create_widget(qtbot):
    from widgets.trajectory_player import TrajectoryPlayerWidget
    w = TrajectoryPlayerWidget()
    qtbot.addWidget(w)
    assert w.btn_play is not None
    assert w.btn_stop is not None
    assert w.slider is not None
    assert w.speed_spinbox is not None


def test_trajectory_initial_state(qtbot):
    from widgets.trajectory_player import TrajectoryPlayerWidget
    w = TrajectoryPlayerWidget()
    qtbot.addWidget(w)
    assert w.is_playing() is False
    assert w.get_frame() == 0
    assert w.speed_spinbox.value() == 1.0


def test_trajectory_load_empty(qtbot):
    from widgets.trajectory_player import TrajectoryPlayerWidget
    w = TrajectoryPlayerWidget()
    qtbot.addWidget(w)
    w.load_trajectory([])
    assert w.get_frame() == 0
    assert w.slider.maximum() == 0


def test_trajectory_load_with_frames(qtbot):
    from widgets.trajectory_player import TrajectoryPlayerWidget

    class MockWaypoint:
        def __init__(self, time):
            self.time = time

    w = TrajectoryPlayerWidget()
    qtbot.addWidget(w)
    trajectory = [MockWaypoint(i * 0.033) for i in range(10)]
    w.load_trajectory(trajectory)
    assert w.slider.maximum() == 9


def test_trajectory_set_frame(qtbot):
    from widgets.trajectory_player import TrajectoryPlayerWidget

    class MockWaypoint:
        def __init__(self, time):
            self.time = time

    w = TrajectoryPlayerWidget()
    qtbot.addWidget(w)
    trajectory = [MockWaypoint(i * 0.033) for i in range(10)]
    w.load_trajectory(trajectory)
    w.set_frame(5)
    assert w.get_frame() == 5


def test_trajectory_speed_control(qtbot):
    from widgets.trajectory_player import TrajectoryPlayerWidget
    w = TrajectoryPlayerWidget()
    qtbot.addWidget(w)
    w.speed_spinbox.setValue(2.0)
    assert w._speed == 2.0


# LoadEnvironment tests
def test_load_env_create_widget(qtbot):
    from widgets.environment_dialog import LoadEnvironmentWidget
    w = LoadEnvironmentWidget()
    qtbot.addWidget(w)
    assert w.urdf_line_edit is not None
    assert w.srdf_line_edit is not None
    assert w.urdf_filepath == ""
    assert w.srdf_filepath == ""


def test_load_env_create_dialog(qtbot):
    from widgets.environment_dialog import LoadEnvironmentDialog
    d = LoadEnvironmentDialog()
    qtbot.addWidget(d)
    assert d.load_widget is not None
    assert d.windowTitle() == "Load Environment"


def test_load_env_dialog_properties(qtbot):
    from widgets.environment_dialog import LoadEnvironmentDialog
    d = LoadEnvironmentDialog()
    qtbot.addWidget(d)
    assert d.urdf_filepath == ""
    assert d.srdf_filepath == ""


# ManipulationWidget tests
def test_manipulation_create_widget(qtbot):
    from widgets.manipulation_widget import ManipulationWidget
    w = ManipulationWidget()
    qtbot.addWidget(w)
    assert w.tab_widget is not None
    assert w.tab_widget.count() == 4


def test_manipulation_tab_titles(qtbot):
    from widgets.manipulation_widget import ManipulationWidget
    w = ManipulationWidget()
    qtbot.addWidget(w)
    titles = [w.tab_widget.tabText(i) for i in range(w.tab_widget.count())]
    assert "Config" in titles
    assert "Joint" in titles
    assert "Cartesian" in titles
    assert "State" in titles


# KinematicGroupsEditor tests
def test_kinematic_groups_create_widget(qtbot):
    from widgets.kinematic_groups_editor import KinematicGroupsEditorWidget
    w = KinematicGroupsEditorWidget()
    qtbot.addWidget(w)
    assert w.groupNameLabel is not None


def test_kinematic_groups_ui_elements_exist(qtbot):
    from widgets.kinematic_groups_editor import KinematicGroupsEditorWidget
    w = KinematicGroupsEditorWidget()
    qtbot.addWidget(w)
    # Check basic UI elements are created
    assert w.groupNameLabel is not None


# PlotWidget tests
def test_plot_create_widget(qtbot):
    try:
        from widgets.plot_widget import PlotWidget
    except ImportError:
        pytest.skip("pyqtgraph not installed")
    w = PlotWidget()
    qtbot.addWidget(w)
    assert w.toolbar is not None
    assert len(w.traces) == 0
    assert len(w.data) == 0


def test_plot_colors_defined(qtbot):
    try:
        from widgets.plot_widget import PlotWidget
    except ImportError:
        pytest.skip("pyqtgraph not installed")
    w = PlotWidget()
    qtbot.addWidget(w)
    assert len(w.colors) == 8
    assert w.colors[0] == (255, 0, 0)  # red


# SceneTree tests
def test_scene_tree_create_widget(qtbot):
    from widgets.scene_tree import SceneTreeWidget
    w = SceneTreeWidget()
    qtbot.addWidget(w)
    assert w.search is not None
    assert w.tree is not None


def test_scene_tree_signals_exist(qtbot):
    from widgets.scene_tree import SceneTreeWidget
    w = SceneTreeWidget()
    qtbot.addWidget(w)
    assert hasattr(w, 'linkSelected')
    assert hasattr(w, 'linkVisibilityChanged')
    assert hasattr(w, 'linkFrameToggled')


def test_scene_tree_search_placeholder(qtbot):
    from widgets.scene_tree import SceneTreeWidget
    w = SceneTreeWidget()
    qtbot.addWidget(w)
    assert w.search.placeholderText() == "Filter..."


# ToolPathDialog tests
def test_tool_path_create_dialog(qtbot):
    from widgets.tool_path_dialog import ToolPathFileDialog
    d = ToolPathFileDialog()
    qtbot.addWidget(d)
    assert d.frame_combo_box is not None
    assert d.file_path_line_edit is not None
    assert d.file_path_push_button is not None


def test_tool_path_initial_state(qtbot):
    from widgets.tool_path_dialog import ToolPathFileDialog
    d = ToolPathFileDialog()
    qtbot.addWidget(d)
    assert d.file_path_line_edit.isReadOnly()
    assert d.file_path_line_edit.text() == ""


def test_tool_path_window_title(qtbot):
    from widgets.tool_path_dialog import ToolPathFileDialog
    d = ToolPathFileDialog()
    qtbot.addWidget(d)
    assert d.windowTitle() == "Dialog"


# TaskComposerWidget tests
def test_task_composer_create_widget(qtbot):
    from widgets.task_composer_widget import TaskComposerWidget
    w = TaskComposerWidget()
    qtbot.addWidget(w)
    assert w.tab_widget is not None


def test_task_composer_tab_widget_exists(qtbot):
    from widgets.task_composer_widget import TaskComposerWidget
    w = TaskComposerWidget()
    qtbot.addWidget(w)
    assert w.tab_widget.count() > 0


def test_task_composer_size_policy(qtbot):
    from widgets.task_composer_widget import TaskComposerWidget
    from PySide6.QtWidgets import QSizePolicy
    w = TaskComposerWidget()
    qtbot.addWidget(w)
    assert w.sizePolicy().horizontalPolicy() == QSizePolicy.Policy.Expanding
    assert w.sizePolicy().verticalPolicy() == QSizePolicy.Policy.Expanding
