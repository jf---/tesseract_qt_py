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

    widget.add_result("link_a", "link_b", 0.001, [0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [1.0, 0.0, 0.0])

    assert widget.contact_results_widget.rowCount() == 1
    assert widget.contact_results_widget.item(0, 0).text() == "link_a"
    assert widget.contact_results_widget.item(0, 1).text() == "link_b"

    widget.clear_results()
    assert widget.contact_results_widget.rowCount() == 0


def test_ik_widget_signals(qapp):
    """Test IKWidget has required signals."""
    from widgets.ik_widget import IKWidget

    widget = IKWidget()

    assert hasattr(widget, "solutionFound")
    assert hasattr(widget, "targetPoseSet")
    assert hasattr(widget, "planRequested")
    assert hasattr(widget, "set_planning_status")


def test_scene_tree_signals(qapp):
    """Test SceneTreeWidget has required signals."""
    from widgets.scene_tree import SceneTreeWidget

    widget = SceneTreeWidget()

    assert hasattr(widget, "linkSelected")
    assert hasattr(widget, "linkVisibilityChanged")
    assert hasattr(widget, "linkDeleteRequested")


def test_all_docks_in_view_menu():
    """Test all dock widgets are accessible via View menu."""
    from pathlib import Path
    import re

    app_py = Path(__file__).parent.parent / "app.py"
    content = app_py.read_text()

    dock_pattern = r"self\.(\w+_dock)\s*=\s*QDockWidget"
    created_docks = set(re.findall(dock_pattern, content))

    menu_pattern = r"view_menu\.addAction\(self\.(\w+_dock)\.toggleViewAction"
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
    match = re.search(r"self\.resize\((\d+),\s*(\d+)\)", content)
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
        assert hasattr(widget, "x_spin")
        assert hasattr(widget, "x_slider")
        assert hasattr(widget, "roll_spin")

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


class TestFKIKWidget:
    """Tests for FKIKWidget unified FK/IK panel."""

    def test_create_widget(self, qapp):
        """Test widget creates without error."""
        from widgets.fkik_widget import FKIKWidget

        widget = FKIKWidget()
        assert widget is not None
        assert hasattr(widget, "joint_slider")
        assert hasattr(widget, "cartesian_widget")
        assert hasattr(widget, "jointValuesChanged")
        assert hasattr(widget, "ikSolveRequested")

    def test_ik_solve_moves_vtk_actors(self, qapp):
        """Test IK solve updates VTK actor positions."""
        from pathlib import Path
        from widgets.fkik_widget import FKIKWidget
        from core.scene_manager import SceneManager
        import tesseract_robotics
        from tesseract_robotics.tesseract_environment import Environment
        from tesseract_robotics.tesseract_common import GeneralResourceLocator
        import vtk

        # Load robot with SRDF for kinematic group
        support_dir = Path(tesseract_robotics.get_tesseract_support_path())
        urdf = support_dir / "urdf" / "abb_irb2400.urdf"
        srdf = support_dir / "urdf" / "abb_irb2400.srdf"

        if not urdf.exists() or not srdf.exists():
            pytest.skip("tesseract_support not found")

        env = Environment()
        loc = GeneralResourceLocator()
        assert env.init(str(urdf), str(srdf), loc)

        # Create scene manager and load environment
        renderer = vtk.vtkRenderer()
        scene = SceneManager(renderer)
        scene.load_environment(env)

        # Get initial link_6 actor position (tool0 has no geometry)
        link6_actors = scene.link_actors.get("link_6", [])
        assert len(link6_actors) > 0, "link_6 should have actors"
        initial_pos = link6_actors[0].GetCenter()

        # Create FKIKWidget
        widget = FKIKWidget()
        widget.set_environment(env, "manipulator", "tool0")
        widget.set_joints(
            {
                "joint_1": (-3.14, 3.14, 0.0),
                "joint_2": (-1.74, 1.92, 0.0),
                "joint_3": (-3.14, 3.14, 0.0),
                "joint_4": (-3.14, 3.14, 0.0),
                "joint_5": (-2.18, 2.18, 0.0),
                "joint_6": (-6.28, 6.28, 0.0),
            }
        )

        # Connect signal to scene update
        widget.jointValuesChanged.connect(scene.update_joint_values)

        # Set target pose and solve IK
        widget.cartesian_widget.set_pose(0.8, 0.3, 1.0, 0.0, 1.57, 0.0)
        widget._on_ik_solve_requested()

        # Verify IK solved
        assert "solved" in widget.status_label.text().lower(), (
            f"IK should solve, got: {widget.status_label.text()}"
        )

        # Get new link_6 position
        new_pos = link6_actors[0].GetCenter()

        # Position should have changed
        pos_changed = any(abs(new_pos[i] - initial_pos[i]) > 0.01 for i in range(3))
        assert pos_changed, (
            f"VTK actor should move after IK. Initial: {initial_pos}, New: {new_pos}"
        )

    def test_fk_updates_ik_display(self, qapp):
        """Test FK slider changes update IK Cartesian display."""
        from pathlib import Path
        from widgets.fkik_widget import FKIKWidget
        import tesseract_robotics
        from tesseract_robotics.tesseract_environment import Environment
        from tesseract_robotics.tesseract_common import GeneralResourceLocator

        # Load robot with SRDF for kinematic group
        support_dir = Path(tesseract_robotics.get_tesseract_support_path())
        urdf = support_dir / "urdf" / "abb_irb2400.urdf"
        srdf = support_dir / "urdf" / "abb_irb2400.srdf"

        if not urdf.exists() or not srdf.exists():
            pytest.skip("tesseract_support not found")

        env = Environment()
        loc = GeneralResourceLocator()
        assert env.init(str(urdf), str(srdf), loc)

        widget = FKIKWidget()
        widget.set_environment(env, "manipulator", "tool0")
        widget.set_joints(
            {
                "joint_1": (-3.14, 3.14, 0.0),
                "joint_2": (-1.74, 1.92, 0.0),
                "joint_3": (-3.14, 3.14, 0.0),
                "joint_4": (-3.14, 3.14, 0.0),
                "joint_5": (-2.18, 2.18, 0.0),
                "joint_6": (-6.28, 6.28, 0.0),
            }
        )

        # Get initial TCP pose
        initial_pose = widget.cartesian_widget.get_pose()

        # Move joint 1 via spinbox (triggers signal emission)
        # 0.5 rad = ~28.6 degrees
        widget.joint_slider.sliders["joint_1"].spinbox.setValue(28.6)

        # IK display should have updated
        new_pose = widget.cartesian_widget.get_pose()
        # Y position should have changed (joint 1 rotates around Z)
        assert new_pose != initial_pose, "IK display should update when FK changes"

    def test_ik_solve_updates_fk(self, qapp):
        """Test IK solve updates FK sliders."""
        from pathlib import Path
        from widgets.fkik_widget import FKIKWidget
        import tesseract_robotics
        from tesseract_robotics.tesseract_environment import Environment
        from tesseract_robotics.tesseract_common import GeneralResourceLocator

        # Load robot with SRDF for kinematic group
        support_dir = Path(tesseract_robotics.get_tesseract_support_path())
        urdf = support_dir / "urdf" / "abb_irb2400.urdf"
        srdf = support_dir / "urdf" / "abb_irb2400.srdf"

        if not urdf.exists() or not srdf.exists():
            pytest.skip("tesseract_support not found")

        env = Environment()
        loc = GeneralResourceLocator()
        assert env.init(str(urdf), str(srdf), loc)

        widget = FKIKWidget()
        widget.set_environment(env, "manipulator", "tool0")
        widget.set_joints(
            {
                "joint_1": (-3.14, 3.14, 0.0),
                "joint_2": (-1.74, 1.92, 0.0),
                "joint_3": (-3.14, 3.14, 0.0),
                "joint_4": (-3.14, 3.14, 0.0),
                "joint_5": (-2.18, 2.18, 0.0),
                "joint_6": (-6.28, 6.28, 0.0),
            }
        )

        # Get initial joint values
        initial_joints = widget.get_joint_values()

        # Set a different target pose (within reachable workspace)
        widget.cartesian_widget.set_pose(0.8, 0.2, 1.2, 0.0, 1.57, 0.0)

        # Trigger IK solve
        widget._on_ik_solve_requested()

        # Check if joints changed
        new_joints = widget.get_joint_values()

        # At least one joint should have changed
        changed = any(
            abs(new_joints.get(j, 0) - initial_joints.get(j, 0)) > 0.01 for j in initial_joints
        )
        assert changed, f"IK should update FK sliders. Status: {widget.status_label.text()}"
