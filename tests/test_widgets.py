"""Test widget functionality."""
import pytest


def test_plot_widget_load_trajectory(qapp):
    """Test PlotWidget loads trajectory data."""
    from widgets.plot_widget import PlotWidget

    plot = PlotWidget()

    trajectory = [
        {"time": 0.0, "joints": {"j1": 0.0, "j2": 0.0}},
        {"time": 1.0, "joints": {"j1": 1.0, "j2": -0.5}},
        {"time": 2.0, "joints": {"j1": 0.5, "j2": 0.5}},
    ]

    plot.load_trajectory(trajectory, ["j1", "j2"])

    assert "j1" in plot.data
    assert "j2" in plot.data
    assert len(plot.data["j1"][0]) == 3  # 3 time points
    assert plot.data["j1"][1] == [0.0, 1.0, 0.5]  # j1 values


def test_plot_widget_frame_marker(qapp):
    """Test PlotWidget frame marker."""
    from widgets.plot_widget import PlotWidget

    plot = PlotWidget()

    trajectory = [
        {"time": 0.0, "joints": {"j1": 0.0}},
        {"time": 1.0, "joints": {"j1": 1.0}},
        {"time": 2.0, "joints": {"j1": 2.0}},
    ]

    plot.load_trajectory(trajectory, ["j1"])
    plot.set_frame_marker(1)

    assert plot.frame_line is not None


def test_contact_widget_results(qapp):
    """Test ContactComputeWidget results table."""
    from widgets.contact_compute_widget import ContactComputeWidget

    widget = ContactComputeWidget()

    widget.add_result(
        "link_a", "link_b", 0.001,
        [0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [1.0, 0.0, 0.0]
    )

    assert widget.contact_results_widget.rowCount() == 1
    assert widget.contact_results_widget.item(0, 0).text() == "link_a"
    assert widget.contact_results_widget.item(0, 1).text() == "link_b"

    widget.clear_results()
    assert widget.contact_results_widget.rowCount() == 0


def test_ik_widget_signals(qapp):
    """Test IKWidget has required signals."""
    from widgets.ik_widget import IKWidget

    widget = IKWidget()

    assert hasattr(widget, 'solutionFound')
    assert hasattr(widget, 'targetPoseSet')
    assert hasattr(widget, 'planRequested')
    assert hasattr(widget, 'set_planning_status')


def test_scene_tree_signals(qapp):
    """Test SceneTreeWidget has required signals."""
    from widgets.scene_tree import SceneTreeWidget

    widget = SceneTreeWidget()

    assert hasattr(widget, 'linkSelected')
    assert hasattr(widget, 'linkVisibilityChanged')
    assert hasattr(widget, 'linkDeleteRequested')


def test_all_docks_in_view_menu():
    """Test all dock widgets are accessible via View menu."""
    from pathlib import Path
    import re

    app_py = Path(__file__).parent.parent / "app.py"
    content = app_py.read_text()

    dock_pattern = r'self\.(\w+_dock)\s*=\s*QDockWidget'
    created_docks = set(re.findall(dock_pattern, content))

    menu_pattern = r'view_menu\.addAction\(self\.(\w+_dock)\.toggleViewAction'
    menu_docks = set(re.findall(menu_pattern, content))

    missing = created_docks - menu_docks
    assert not missing, f"Docks missing from View menu: {missing}"


def test_window_size_reasonable():
    """Test app.py configures reasonable window size."""
    from pathlib import Path
    import re

    app_py = Path(__file__).parent.parent / "app.py"
    content = app_py.read_text()

    # Check resize() call
    match = re.search(r'self\.resize\((\d+),\s*(\d+)\)', content)
    assert match, "No resize() call found"

    width, height = int(match.group(1)), int(match.group(2))
    assert width <= 1600, f"Default width too large: {width}"
    assert height <= 1000, f"Default height too large: {height}"


class TestCartesianEditor:
    """Tests for CartesianEditorWidget."""

    def test_create_widget(self, qapp):
        """Test widget creates without error."""
        from widgets.cartesian_editor import CartesianEditorWidget

        widget = CartesianEditorWidget()
        assert widget is not None
        assert hasattr(widget, 'x_spin')
        assert hasattr(widget, 'x_slider')
        assert hasattr(widget, 'roll_spin')

    def test_default_values(self, qapp):
        """Test default pose values."""
        from widgets.cartesian_editor import CartesianEditorWidget

        widget = CartesianEditorWidget()
        x, y, z, r, p, yaw = widget.get_pose()

        assert x == 0.0
        assert y == 0.0
        assert z == 0.5  # Default Z
        assert r == 0.0
        assert p == 0.0
        assert yaw == 0.0

    def test_set_pose(self, qapp):
        """Test setting pose values."""
        from widgets.cartesian_editor import CartesianEditorWidget
        from math import radians

        widget = CartesianEditorWidget()
        widget.set_pose(1.0, 0.5, 0.8, radians(45), radians(30), radians(-90))

        x, y, z, r, p, yaw = widget.get_pose()
        assert abs(x - 1.0) < 0.01
        assert abs(y - 0.5) < 0.01
        assert abs(z - 0.8) < 0.01
        assert abs(r - radians(45)) < 0.01
        assert abs(p - radians(30)) < 0.01
        assert abs(yaw - radians(-90)) < 0.01

    def test_slider_spinbox_sync(self, qapp):
        """Test slider and spinbox stay synchronized."""
        from widgets.cartesian_editor import CartesianEditorWidget

        widget = CartesianEditorWidget()

        # Set via spinbox
        widget.x_spin.setValue(0.5)
        assert widget.x_slider.value() == 500  # Scaled by 1000

        # Set via slider
        widget.y_slider.setValue(250)
        assert abs(widget.y_spin.value() - 0.25) < 0.001

    def test_pose_changed_signal(self, qapp):
        """Test poseChanged signal emits on value change."""
        from widgets.cartesian_editor import CartesianEditorWidget

        widget = CartesianEditorWidget()
        received = []

        widget.poseChanged.connect(lambda *args: received.append(args))

        # Trigger change
        widget.x_spin.setValue(0.3)

        assert len(received) > 0
        assert abs(received[-1][0] - 0.3) < 0.01  # X value

    def test_apply_ik_signal(self, qapp):
        """Test applyIKRequested signal emits on button click."""
        from widgets.cartesian_editor import CartesianEditorWidget

        widget = CartesianEditorWidget()
        clicked = []

        widget.applyIKRequested.connect(lambda: clicked.append(True))
        widget.apply_btn.click()

        assert len(clicked) == 1

    def test_get_xyz(self, qapp):
        """Test get_xyz returns position only."""
        from widgets.cartesian_editor import CartesianEditorWidget

        widget = CartesianEditorWidget()
        widget.set_pose(1.0, 2.0, 3.0, 0.1, 0.2, 0.3)

        xyz = widget.get_xyz()
        assert len(xyz) == 3
        assert abs(xyz[0] - 1.0) < 0.01
        assert abs(xyz[1] - 2.0) < 0.01
        assert abs(xyz[2] - 2.0) < 0.01  # Clamped to range max 2.0

    def test_get_rpy_radians(self, qapp):
        """Test get_rpy_radians returns orientation in radians."""
        from widgets.cartesian_editor import CartesianEditorWidget
        from math import radians, pi

        widget = CartesianEditorWidget()
        widget.set_pose(0, 0, 0, radians(90), radians(45), radians(-45))

        rpy = widget.get_rpy_radians()
        assert len(rpy) == 3
        assert abs(rpy[0] - radians(90)) < 0.01
        assert abs(rpy[1] - radians(45)) < 0.01
        assert abs(rpy[2] - radians(-45)) < 0.01
