"""widget tests - verify widgets create and basic ops work."""
import pytest
from pathlib import Path
import sys

# add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestACMEditorWidget:
    """test ACM editor widget."""

    @pytest.fixture
    def qapp(self):
        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance() or QApplication([])
            yield app
        except ImportError:
            pytest.skip("PySide6 not installed")

    def test_create_widget(self, qapp):
        from widgets.acm_editor import ACMEditorWidget
        w = ACMEditorWidget()
        assert w.table.rowCount() == 0

    def test_add_entry(self, qapp):
        from widgets.acm_editor import ACMEditorWidget
        w = ACMEditorWidget()
        w.add_entry("link_a", "link_b", "test reason")
        assert w.table.rowCount() == 1
        assert w.table.item(0, 0).text() == "link_a"
        assert w.table.item(0, 1).text() == "link_b"
        assert w.table.item(0, 2).text() == "test reason"

    def test_remove_entry(self, qapp):
        from widgets.acm_editor import ACMEditorWidget
        w = ACMEditorWidget()
        w.add_entry("link_a", "link_b", "reason")
        w.add_entry("link_c", "link_d", "reason2")
        assert w.table.rowCount() == 2

        # select first row and remove
        w.table.selectRow(0)
        w._on_remove()
        assert w.table.rowCount() == 1
        assert w.table.item(0, 0).text() == "link_c"

    def test_signals_exist(self, qapp):
        from widgets.acm_editor import ACMEditorWidget
        w = ACMEditorWidget()
        # verify signals defined
        assert hasattr(w, 'entry_added')
        assert hasattr(w, 'entry_removed')
        assert hasattr(w, 'matrix_applied')
        assert hasattr(w, 'generate_requested')

    def test_get_entries(self, qapp):
        from widgets.acm_editor import ACMEditorWidget
        w = ACMEditorWidget()
        w.add_entry("l1", "l2", "r1")
        w.add_entry("l3", "l4", "r2")
        entries = w.get_entries()
        assert len(entries) == 2
        assert entries[0] == ("l1", "l2", "r1")
        assert entries[1] == ("l3", "l4", "r2")

    def test_clear(self, qapp):
        from widgets.acm_editor import ACMEditorWidget
        w = ACMEditorWidget()
        w.add_entry("l1", "l2", "r1")
        w.clear()
        assert w.table.rowCount() == 0


class TestSRDFEditorWidget:
    """test SRDF editor widget."""

    @pytest.fixture
    def qapp(self):
        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance() or QApplication([])
            yield app
        except ImportError:
            pytest.skip("PySide6 not installed")

    def test_create_widget(self, qapp):
        from widgets.srdf_editor import SRDFEditorWidget
        w = SRDFEditorWidget()
        assert w.toolbox is not None

    def test_page_count(self, qapp):
        from widgets.srdf_editor import SRDFEditorWidget
        w = SRDFEditorWidget()
        assert w.toolbox.count() == 5

    def test_page_navigation(self, qapp):
        from widgets.srdf_editor import SRDFEditorWidget
        w = SRDFEditorWidget()
        # default is page 4 (save)
        assert w.toolbox.currentIndex() == 4

        # switch to ACM page (index 1)
        w.toolbox.setCurrentIndex(1)
        assert w.toolbox.currentIndex() == 1

        # switch to kinematic groups (index 2)
        w.toolbox.setCurrentIndex(2)
        assert w.toolbox.currentIndex() == 2

    def test_ui_elements_exist(self, qapp):
        from widgets.srdf_editor import SRDFEditorWidget
        w = SRDFEditorWidget()
        assert w.urdf_line_edit is not None
        assert w.srdf_line_edit is not None
        assert w.urdf_browse_button is not None
        assert w.load_push_button is not None
        assert w.save_srdf_save_button is not None


class TestCartesianEditorWidget:
    """test cartesian editor widget."""

    @pytest.fixture
    def qapp(self):
        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance() or QApplication([])
            yield app
        except ImportError:
            pytest.skip("PySide6 not installed")

    def test_create_widget(self, qapp):
        from widgets.cartesian_editor import CartesianEditorWidget
        w = CartesianEditorWidget()
        assert w.x_spin is not None
        assert w.y_spin is not None
        assert w.z_spin is not None

    def test_position_defaults(self, qapp):
        from widgets.cartesian_editor import CartesianEditorWidget
        w = CartesianEditorWidget()
        assert w.x_spin.value() == 0.0
        assert w.y_spin.value() == 0.0
        assert w.z_spin.value() == 0.0

    def test_position_value_changes(self, qapp):
        from widgets.cartesian_editor import CartesianEditorWidget
        w = CartesianEditorWidget()
        w.x_spin.setValue(1.5)
        w.y_spin.setValue(-2.3)
        w.z_spin.setValue(0.75)
        assert w.x_spin.value() == 1.5
        assert w.y_spin.value() == -2.3
        assert w.z_spin.value() == 0.75

    def test_orientation_defaults(self, qapp):
        from widgets.cartesian_editor import CartesianEditorWidget
        w = CartesianEditorWidget()
        assert w.roll_spin.value() == 0.0
        assert w.pitch_spin.value() == 0.0
        assert w.yaw_spin.value() == 0.0
        assert w.quat_w_spin.value() == 1.0
        assert w.quat_x_spin.value() == 0.0

    def test_orientation_value_changes(self, qapp):
        from widgets.cartesian_editor import CartesianEditorWidget
        w = CartesianEditorWidget()
        w.roll_spin.setValue(0.5)
        w.pitch_spin.setValue(-0.3)
        w.yaw_spin.setValue(1.2)
        assert w.roll_spin.value() == 0.5
        assert w.pitch_spin.value() == -0.3
        assert w.yaw_spin.value() == 1.2


class TestContactComputeWidget:
    """test contact compute widget."""

    @pytest.fixture
    def qapp(self):
        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance() or QApplication([])
            yield app
        except ImportError:
            pytest.skip("PySide6 not installed")

    def test_create_widget(self, qapp):
        from widgets.contact_compute_widget import ContactComputeWidget
        w = ContactComputeWidget()
        assert w.contact_threshold is not None

    def test_threshold_default(self, qapp):
        from widgets.contact_compute_widget import ContactComputeWidget
        w = ContactComputeWidget()
        assert w.contact_threshold.value() == 0.0

    def test_threshold_value_change(self, qapp):
        from widgets.contact_compute_widget import ContactComputeWidget
        w = ContactComputeWidget()
        w.contact_threshold.setValue(0.05)
        assert w.contact_threshold.value() == 0.05

    def test_contact_test_type(self, qapp):
        from widgets.contact_compute_widget import ContactComputeWidget
        w = ContactComputeWidget()
        assert w.contact_test_type.count() == 3
        assert w.contact_test_type.currentText() == "First"
        w.contact_test_type.setCurrentIndex(2)
        assert w.contact_test_type.currentText() == "All"

    def test_checkboxes_default(self, qapp):
        from widgets.contact_compute_widget import ContactComputeWidget
        w = ContactComputeWidget()
        assert w.calc_penetration.isChecked()
        assert w.calc_distance.isChecked()

    def test_buttons_exist(self, qapp):
        from widgets.contact_compute_widget import ContactComputeWidget
        w = ContactComputeWidget()
        assert w.btn_check_state is not None
        assert w.btn_compute is not None


class TestStudioMainWindow:
    """test studio main window."""

    @pytest.fixture
    def qapp(self):
        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance() or QApplication([])
            yield app
        except ImportError:
            pytest.skip("PySide6 not installed")

    def test_create_window(self, qapp):
        from widgets.studio_layout import StudioMainWindow
        w = StudioMainWindow()
        assert w.windowTitle() == "MainWindow"

    def test_menu_actions_exist(self, qapp):
        from widgets.studio_layout import StudioMainWindow
        w = StudioMainWindow()
        assert w.action_load_config is not None
        assert w.action_save_config is not None
        assert w.action_save_config_as is not None
        assert w.action_restore_state is not None
        assert w.action_save_state is not None
        assert w.action_create_perspective is not None
        assert w.action_load_plugins is not None

    def test_menu_shortcuts(self, qapp):
        from widgets.studio_layout import StudioMainWindow
        from PySide6.QtGui import QKeySequence
        w = StudioMainWindow()
        assert w.action_load_config.shortcut() == QKeySequence("Ctrl+O")
        assert w.action_save_config.shortcut() == QKeySequence("Ctrl+S")
        assert w.action_save_config_as.shortcut() == QKeySequence("Ctrl+Shift+S")

    def test_save_config_disabled_by_default(self, qapp):
        from widgets.studio_layout import StudioMainWindow
        w = StudioMainWindow()
        assert not w.action_save_config.isEnabled()

    def test_menus_exist(self, qapp):
        from widgets.studio_layout import StudioMainWindow
        w = StudioMainWindow()
        menubar = w.menuBar()
        actions = menubar.actions()
        menu_titles = [action.text() for action in actions]
        assert "File" in menu_titles
        assert "View" in menu_titles
        assert "Tools" in menu_titles


class TestInfoPanel:
    """test robot info panel widget."""

    @pytest.fixture
    def qapp(self):
        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance() or QApplication([])
            yield app
        except ImportError:
            pytest.skip("PySide6 not installed")

    def test_create_widget(self, qapp):
        from widgets.info_panel import RobotInfoPanel
        w = RobotInfoPanel()
        assert w.name_label is not None
        assert w.dof_label is not None
        assert w.joint_table is not None
        assert w.tcp_xyz_label is not None
        assert w.tcp_rpy_label is not None

    def test_initial_state(self, qapp):
        from widgets.info_panel import RobotInfoPanel
        w = RobotInfoPanel()
        assert w.name_label.text() == "Name: -"
        assert w.dof_label.text() == "DOF: 0"
        assert w.tcp_xyz_label.text() == "XYZ: -"
        assert w.tcp_rpy_label.text() == "RPY: -"

    def test_joint_table_columns(self, qapp):
        from widgets.info_panel import RobotInfoPanel
        w = RobotInfoPanel()
        assert w.joint_table.columnCount() == 4
        headers = [w.joint_table.horizontalHeaderItem(i).text() for i in range(4)]
        assert headers == ["Joint", "Value", "Min", "Max"]

    def test_set_tcp_link(self, qapp):
        from widgets.info_panel import RobotInfoPanel
        w = RobotInfoPanel()
        w.set_tcp_link("tool_link")
        assert w._tcp_link == "tool_link"


class TestJointSlider:
    """test joint slider widget."""

    @pytest.fixture
    def qapp(self):
        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance() or QApplication([])
            yield app
        except ImportError:
            pytest.skip("PySide6 not installed")

    def test_create_slider(self, qapp):
        from widgets.joint_slider import JointSlider
        s = JointSlider("joint_1", -1.57, 1.57, 0.0)
        assert s.name == "joint_1"
        assert s.lower == -1.57
        assert s.upper == 1.57
        assert s.value() == 0.0

    def test_slider_value_clamping(self, qapp):
        from widgets.joint_slider import JointSlider
        s = JointSlider("j", -1.0, 1.0, 0.0)
        s.set_value(2.0)
        assert s.value() == 1.0
        s.set_value(-2.0)
        assert s.value() == -1.0

    def test_slider_components(self, qapp):
        from widgets.joint_slider import JointSlider
        s = JointSlider("j", 0.0, 10.0)
        assert s.label is not None
        assert s.slider is not None
        assert s.spinbox is not None

    def test_joint_slider_widget_create(self, qapp):
        from widgets.joint_slider import JointSliderWidget
        w = JointSliderWidget()
        assert w.btn_zero is not None
        assert w.btn_random is not None
        assert len(w.sliders) == 0

    def test_joint_slider_widget_set_joints(self, qapp):
        from widgets.joint_slider import JointSliderWidget
        w = JointSliderWidget()
        joints = {"j1": (-1.0, 1.0, 0.0), "j2": (-2.0, 2.0, 0.5)}
        w.set_joints(joints)
        assert len(w.sliders) == 2
        assert "j1" in w.sliders
        assert "j2" in w.sliders

    def test_joint_slider_widget_get_values(self, qapp):
        from widgets.joint_slider import JointSliderWidget
        w = JointSliderWidget()
        w.set_joints({"j1": (-1.0, 1.0, 0.0), "j2": (-2.0, 2.0, 0.5)})
        values = w.get_values()
        assert values["j1"] == 0.0
        assert values["j2"] == 0.5

    def test_joint_slider_widget_set_values(self, qapp):
        from widgets.joint_slider import JointSliderWidget
        w = JointSliderWidget()
        w.set_joints({"j1": (-1.0, 1.0, 0.0), "j2": (-2.0, 2.0, 0.0)})
        w.set_values({"j1": 0.5, "j2": -0.75})
        assert w.sliders["j1"].value() == 0.5
        assert w.sliders["j2"].value() == -0.75


class TestTrajectoryPlayer:
    """test trajectory player widget."""

    @pytest.fixture
    def qapp(self):
        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance() or QApplication([])
            yield app
        except ImportError:
            pytest.skip("PySide6 not installed")

    def test_create_widget(self, qapp):
        from widgets.trajectory_player import TrajectoryPlayerWidget
        w = TrajectoryPlayerWidget()
        assert w.btn_play is not None
        assert w.btn_stop is not None
        assert w.slider is not None
        assert w.speed_spinbox is not None

    def test_initial_state(self, qapp):
        from widgets.trajectory_player import TrajectoryPlayerWidget
        w = TrajectoryPlayerWidget()
        assert w.is_playing() is False
        assert w.get_frame() == 0
        assert w.speed_spinbox.value() == 1.0

    def test_load_trajectory_empty(self, qapp):
        from widgets.trajectory_player import TrajectoryPlayerWidget
        w = TrajectoryPlayerWidget()
        w.load_trajectory([])
        assert w.get_frame() == 0
        assert w.slider.maximum() == 0

    def test_load_trajectory_with_frames(self, qapp):
        from widgets.trajectory_player import TrajectoryPlayerWidget

        class MockWaypoint:
            def __init__(self, time):
                self.time = time

        w = TrajectoryPlayerWidget()
        trajectory = [MockWaypoint(i * 0.033) for i in range(10)]
        w.load_trajectory(trajectory)
        assert w.slider.maximum() == 9

    def test_set_frame(self, qapp):
        from widgets.trajectory_player import TrajectoryPlayerWidget

        class MockWaypoint:
            def __init__(self, time):
                self.time = time

        w = TrajectoryPlayerWidget()
        trajectory = [MockWaypoint(i * 0.033) for i in range(10)]
        w.load_trajectory(trajectory)
        w.set_frame(5)
        assert w.get_frame() == 5

    def test_speed_control(self, qapp):
        from widgets.trajectory_player import TrajectoryPlayerWidget
        w = TrajectoryPlayerWidget()
        w.speed_spinbox.setValue(2.0)
        assert w._speed == 2.0


class TestLoadEnvironment:
    """test load environment dialog and widget."""

    @pytest.fixture
    def qapp(self):
        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance() or QApplication([])
            yield app
        except ImportError:
            pytest.skip("PySide6 not installed")

    def test_create_widget(self, qapp):
        from widgets.environment_dialog import LoadEnvironmentWidget
        w = LoadEnvironmentWidget()
        assert w.urdf_line_edit is not None
        assert w.srdf_line_edit is not None
        assert w.urdf_filepath == ""
        assert w.srdf_filepath == ""

    def test_create_dialog(self, qapp):
        from widgets.environment_dialog import LoadEnvironmentDialog
        d = LoadEnvironmentDialog()
        assert d.load_widget is not None
        assert d.windowTitle() == "Load Environment"

    def test_dialog_properties(self, qapp):
        from widgets.environment_dialog import LoadEnvironmentDialog
        d = LoadEnvironmentDialog()
        assert d.urdf_filepath == ""
        assert d.srdf_filepath == ""


class TestManipulationWidget:
    """test manipulation widget."""

    @pytest.fixture
    def qapp(self):
        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance() or QApplication([])
            yield app
        except ImportError:
            pytest.skip("PySide6 not installed")

    def test_create_widget(self, qapp):
        from widgets.manipulation_widget import ManipulationWidget
        w = ManipulationWidget()
        assert w.tab_widget is not None
        assert w.tab_widget.count() == 4

    def test_tab_titles(self, qapp):
        from widgets.manipulation_widget import ManipulationWidget
        w = ManipulationWidget()
        titles = [w.tab_widget.tabText(i) for i in range(w.tab_widget.count())]
        assert "Config" in titles
        assert "Joint" in titles
        assert "Cartesian" in titles
        assert "State" in titles


class TestKinematicGroupsEditor:
    """test kinematic groups editor widget."""

    @pytest.fixture
    def qapp(self):
        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance() or QApplication([])
            yield app
        except ImportError:
            pytest.skip("PySide6 not installed")

    def test_create_widget(self, qapp):
        from widgets.kinematic_groups_editor import KinematicGroupsEditorWidget
        w = KinematicGroupsEditorWidget()
        assert w.groupNameLabel is not None

    def test_ui_elements_exist(self, qapp):
        from widgets.kinematic_groups_editor import KinematicGroupsEditorWidget
        w = KinematicGroupsEditorWidget()
        # Check basic UI elements are created
        assert w.groupNameLabel is not None


class TestPlotWidget:
    """test plot widget."""

    @pytest.fixture
    def qapp(self):
        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance() or QApplication([])
            yield app
        except ImportError:
            pytest.skip("PySide6 not installed")

    def test_create_widget(self, qapp):
        try:
            from widgets.plot_widget import PlotWidget
        except ImportError:
            pytest.skip("pyqtgraph not installed")
        w = PlotWidget()
        assert w.toolbar is not None
        assert len(w.traces) == 0
        assert len(w.data) == 0

    def test_colors_defined(self, qapp):
        try:
            from widgets.plot_widget import PlotWidget
        except ImportError:
            pytest.skip("pyqtgraph not installed")
        w = PlotWidget()
        assert len(w.colors) == 8
        assert w.colors[0] == (255, 0, 0)  # red


class TestSceneTree:
    """test scene tree widget."""

    @pytest.fixture
    def qapp(self):
        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance() or QApplication([])
            yield app
        except ImportError:
            pytest.skip("PySide6 not installed")

    def test_create_widget(self, qapp):
        from widgets.scene_tree import SceneTreeWidget
        w = SceneTreeWidget()
        assert w.search is not None
        assert w.tree is not None

    def test_signals_exist(self, qapp):
        from widgets.scene_tree import SceneTreeWidget
        w = SceneTreeWidget()
        assert hasattr(w, 'linkSelected')
        assert hasattr(w, 'linkVisibilityChanged')
        assert hasattr(w, 'linkFrameToggled')

    def test_search_placeholder(self, qapp):
        from widgets.scene_tree import SceneTreeWidget
        w = SceneTreeWidget()
        assert w.search.placeholderText() == "Filter..."


class TestToolPathDialog:
    """test tool path file dialog."""

    @pytest.fixture
    def qapp(self):
        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance() or QApplication([])
            yield app
        except ImportError:
            pytest.skip("PySide6 not installed")

    def test_create_dialog(self, qapp):
        from widgets.tool_path_dialog import ToolPathFileDialog
        d = ToolPathFileDialog()
        assert d.frame_combo_box is not None
        assert d.file_path_line_edit is not None
        assert d.file_path_push_button is not None

    def test_initial_state(self, qapp):
        from widgets.tool_path_dialog import ToolPathFileDialog
        d = ToolPathFileDialog()
        assert d.file_path_line_edit.isReadOnly()
        assert d.file_path_line_edit.text() == ""

    def test_window_title(self, qapp):
        from widgets.tool_path_dialog import ToolPathFileDialog
        d = ToolPathFileDialog()
        assert d.windowTitle() == "Dialog"


class TestTaskComposerWidget:
    """test task composer widget."""

    @pytest.fixture
    def qapp(self):
        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance() or QApplication([])
            yield app
        except ImportError:
            pytest.skip("PySide6 not installed")

    def test_create_widget(self, qapp):
        from widgets.task_composer_widget import TaskComposerWidget
        w = TaskComposerWidget()
        assert w.tab_widget is not None

    def test_tab_widget_exists(self, qapp):
        from widgets.task_composer_widget import TaskComposerWidget
        w = TaskComposerWidget()
        assert w.tab_widget.count() > 0

    def test_size_policy(self, qapp):
        from widgets.task_composer_widget import TaskComposerWidget
        from PySide6.QtWidgets import QSizePolicy
        w = TaskComposerWidget()
        assert w.sizePolicy().horizontalPolicy() == QSizePolicy.Policy.Expanding
        assert w.sizePolicy().verticalPolicy() == QSizePolicy.Policy.Expanding
