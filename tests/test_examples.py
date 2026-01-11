"""Smoke tests - examples must complete without error."""

import pytest
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# Skip markers for optional deps
vtk_available = pytest.importorskip("vtk", reason="vtk not installed")
tesseract_available = pytest.mark.skipif(
    not pytest.importorskip("tesseract_robotics", reason="tesseract not installed"),
    reason="tesseract_robotics not installed",
)


class TestImports:
    """Test all modules import cleanly."""

    def test_import_core(self):
        try:
            from core.scene_manager import SceneManager
            from core.camera_control import CameraController, ViewMode
        except ImportError as e:
            if "vtk" in str(e) or "tesseract" in str(e) or "dylib" in str(e):
                pytest.skip(f"dependency not available: {e}")
            raise

    def test_import_state_manager(self):
        from core.state_manager import StateManager

    def test_import_contact_viz(self):
        try:
            from core.contact_viz import ContactVisualizer
        except ImportError as e:
            if "vtk" in str(e):
                pytest.skip("vtk not installed")
            raise


class TestExamples:
    """Test example scripts parse and define expected functions."""

    def test_tool_path_demo(self):
        from examples.tool_path_demo import create_sample_paths, add_demo_paths

        assert callable(create_sample_paths)
        assert callable(add_demo_paths)

        # Actually run it
        paths = create_sample_paths()
        assert "spiral" in paths
        assert "segments" in paths

    def test_workspace_demo(self):
        from examples.workspace_demo import visualize_workspace, visualize_workspace_simple

        assert callable(visualize_workspace)
        assert callable(visualize_workspace_simple)

    def test_fk_viz_demo(self):
        from examples.fk_viz_demo import demo_fk_viz

        assert callable(demo_fk_viz)


class TestStateManager:
    """Test state manager functionality."""

    def test_save_load_pose(self, tmp_path):
        from core.state_manager import StateManager

        mgr = StateManager()
        mgr.save_pose("test", {"joint_1": 0.5, "joint_2": -0.3})

        loaded = mgr.load_pose("test")
        assert loaded == {"joint_1": 0.5, "joint_2": -0.3}

    def test_list_poses(self):
        from core.state_manager import StateManager

        mgr = StateManager()
        mgr.save_pose("pose_a", {"j1": 0.1})
        mgr.save_pose("pose_b", {"j1": 0.2})

        poses = mgr.list_poses()
        assert "pose_a" in poses
        assert "pose_b" in poses

    def test_save_load_file(self, tmp_path):
        from core.state_manager import StateManager

        mgr = StateManager()
        mgr.save_pose("home", {"j1": 0.0, "j2": 0.0})

        filepath = tmp_path / "state.json"
        mgr.save_to_file(filepath)
        assert filepath.exists()

        mgr2 = StateManager()
        mgr2.load_from_file(filepath)
        assert mgr2.load_pose("home") == {"j1": 0.0, "j2": 0.0}


class TestTrajectoryPlayer:
    """Test trajectory player widget."""

    @pytest.fixture
    def qapp(self):
        from PySide6.QtWidgets import QApplication

        app = QApplication.instance() or QApplication([])
        yield app

    def test_create_player(self, qapp):
        from widgets.trajectory_player import TrajectoryPlayerWidget

        w = TrajectoryPlayerWidget()
        assert w._frame_count == 0
        assert w.get_frame() == 0

    def test_load_trajectory(self, qapp):
        import numpy as np
        from widgets.trajectory_player import TrajectoryPlayerWidget

        w = TrajectoryPlayerWidget()
        # Fake trajectory: list of (positions, timestamp) tuples
        traj = [
            (np.array([0.0, 0.0, 0.0]), 0.0),
            (np.array([0.1, 0.2, 0.3]), 0.5),
            (np.array([0.2, 0.4, 0.6]), 1.0),
        ]
        w.load_trajectory(traj)
        assert w._frame_count == 3
        assert w.get_frame() == 0


class TestInfoPanel:
    """Test robot info panel."""

    @pytest.fixture
    def qapp(self):
        from PySide6.QtWidgets import QApplication

        app = QApplication.instance() or QApplication([])
        yield app

    def test_create_panel(self, qapp):
        from widgets.info_panel import RobotInfoPanel

        p = RobotInfoPanel()
        assert p.name_label.text() == "Name: -"

    def test_update_joint_values(self, qapp):
        from widgets.info_panel import RobotInfoPanel
        from PySide6.QtWidgets import QTableWidgetItem

        p = RobotInfoPanel()
        p._joint_names = ["j1", "j2"]
        p.joint_table.setRowCount(2)
        for i in range(2):
            p.joint_table.setItem(i, 1, QTableWidgetItem("0.0"))
        p.update_joint_values({"j1": 1.5, "j2": -0.5})


class TestRotationConversion:
    """Test rotation matrix to RPY conversion."""

    def test_identity(self):
        import numpy as np
        from widgets.info_panel import rotation_matrix_to_rpy

        R = np.eye(3)
        roll, pitch, yaw = rotation_matrix_to_rpy(R)
        assert abs(roll) < 1e-6
        assert abs(pitch) < 1e-6
        assert abs(yaw) < 1e-6

    def test_90_deg_yaw(self):
        import numpy as np
        from widgets.info_panel import rotation_matrix_to_rpy

        # 90 deg rotation about Z
        R = np.array(
            [
                [0, -1, 0],
                [1, 0, 0],
                [0, 0, 1],
            ],
            dtype=float,
        )
        roll, pitch, yaw = rotation_matrix_to_rpy(R)
        assert abs(yaw - np.pi / 2) < 1e-6


class TestPlotWidget:
    """Test plot widget without display."""

    @pytest.fixture
    def qapp(self):
        from PySide6.QtWidgets import QApplication

        app = QApplication.instance() or QApplication([])
        yield app

    def test_create_plot_widget(self, qapp):
        pytest.importorskip("pyqtgraph", reason="pyqtgraph not installed")
        from widgets.plot_widget import PlotWidget

        w = PlotWidget()
        w.add_joint("joint_1")
        w.add_joint("joint_2")
        w.update_points({"joint_1": 0.5, "joint_2": -0.3}, 0.0)
        w.clear()
