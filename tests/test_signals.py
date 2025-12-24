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
        w.sliders["j1"].spinbox.setValue(0.5)

        # verify signal emitted
        assert len(spy) == 1
        # verify signal payload: (name, value)
        assert spy[0][0] == "j1"
        assert abs(spy[0][1] - 0.5) < 0.001

    def test_joint_values_changed_signal_emission(self, qapp):
        """test jointValuesChanged signal emitted with dict of all joint values."""
        from widgets.joint_slider import JointSliderWidget

        w = JointSliderWidget()
        w.set_joints({"j1": (-1.0, 1.0, 0.0), "j2": (-2.0, 2.0, 0.0)})

        spy = SignalSpy()
        w.jointValuesChanged.connect(spy.slot)
        w.sliders["j1"].spinbox.setValue(0.5)

        # verify signal emitted
        assert len(spy) == 1
        # verify signal payload: dict with all joint values
        values = spy[0][0]
        assert isinstance(values, dict)
        assert "j1" in values
        assert "j2" in values
        assert abs(values["j1"] - 0.5) < 0.001
        assert values["j2"] == 0.0

    def test_joint_value_changed_via_spinbox(self, qapp):
        """test signal emitted when spinbox value changes."""
        from widgets.joint_slider import JointSliderWidget

        w = JointSliderWidget()
        w.set_joints({"j1": (-1.0, 1.0, 0.0)})

        spy = SignalSpy()
        w.jointValueChanged.connect(spy.slot)
        w.sliders["j1"].spinbox.setValue(0.75)

        assert len(spy) == 1
        assert spy[0][0] == "j1"
        assert abs(spy[0][1] - 0.75) < 0.001

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
