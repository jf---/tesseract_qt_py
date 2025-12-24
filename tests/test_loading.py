"""Test URDF loading and core functionality."""
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


def test_urdf_loads():
    """Test basic URDF loading."""
    from tesseract_robotics.tesseract_environment import Environment
    from tesseract_robotics.tesseract_common import GeneralResourceLocator

    urdf = FIXTURES / "abb_irb2400.urdf"
    env = Environment()
    loc = GeneralResourceLocator()

    assert env.init(str(urdf), loc), f"Failed to load {urdf}"

    sg = env.getSceneGraph()
    links = [l.getName() for l in sg.getLinks()]
    joints = [j.getName() for j in sg.getJoints()]

    assert "base_link" in links
    assert "tool0" in links
    assert len(links) == 9
    assert len(joints) == 8


def test_joint_limits():
    """Test joint limits are parsed correctly."""
    from tesseract_robotics.tesseract_environment import Environment
    from tesseract_robotics.tesseract_common import GeneralResourceLocator
    from tesseract_robotics.tesseract_scene_graph import JointType

    urdf = FIXTURES / "abb_irb2400.urdf"
    env = Environment()
    loc = GeneralResourceLocator()
    env.init(str(urdf), loc)

    sg = env.getSceneGraph()
    movable = (JointType.REVOLUTE, JointType.CONTINUOUS, JointType.PRISMATIC)

    joints = {}
    for j in sg.getJoints():
        if j.type in movable:
            lim = j.limits
            joints[j.getName()] = (lim.lower, lim.upper)

    assert len(joints) == 6
    assert joints["joint_1"] == pytest.approx((-3.1416, 3.1416), rel=1e-3)
    assert joints["joint_2"] == pytest.approx((-1.7453, 1.9199), rel=1e-3)


def test_state_transforms():
    """Test state and link transforms."""
    from tesseract_robotics.tesseract_environment import Environment
    from tesseract_robotics.tesseract_common import GeneralResourceLocator

    urdf = FIXTURES / "abb_irb2400.urdf"
    env = Environment()
    loc = GeneralResourceLocator()
    env.init(str(urdf), loc)

    state = env.getState()
    assert "base_link" in state.link_transforms
    assert "tool0" in state.link_transforms

    # Set joint and verify state updates
    env.setState({"joint_1": 1.0})
    state = env.getState()
    assert state.joints["joint_1"] == pytest.approx(1.0)


def test_scene_manager_load():
    """Test SceneManager loads environment."""
    import vtk
    from core.scene_manager import SceneManager
    from tesseract_robotics.tesseract_environment import Environment
    from tesseract_robotics.tesseract_common import GeneralResourceLocator

    urdf = FIXTURES / "abb_irb2400.urdf"
    env = Environment()
    loc = GeneralResourceLocator()
    env.init(str(urdf), loc)

    renderer = vtk.vtkRenderer()
    scene = SceneManager(renderer)
    scene.load_environment(env)

    assert len(scene.link_actors) == 9
    assert "base_link" in scene.link_actors
    assert "tool0" in scene.link_actors


def test_scene_manager_update_joints():
    """Test SceneManager updates joint values."""
    import vtk
    from core.scene_manager import SceneManager
    from tesseract_robotics.tesseract_environment import Environment
    from tesseract_robotics.tesseract_common import GeneralResourceLocator

    urdf = FIXTURES / "abb_irb2400.urdf"
    env = Environment()
    loc = GeneralResourceLocator()
    env.init(str(urdf), loc)

    renderer = vtk.vtkRenderer()
    scene = SceneManager(renderer)
    scene.load_environment(env)

    # Should not raise
    scene.update_joint_values({"joint_1": 0.5, "joint_2": -0.3})


def test_scene_manager_remove_link():
    """Test SceneManager remove_link."""
    import vtk
    from core.scene_manager import SceneManager
    from tesseract_robotics.tesseract_environment import Environment
    from tesseract_robotics.tesseract_common import GeneralResourceLocator

    urdf = FIXTURES / "abb_irb2400.urdf"
    env = Environment()
    loc = GeneralResourceLocator()
    env.init(str(urdf), loc)

    renderer = vtk.vtkRenderer()
    scene = SceneManager(renderer)
    scene.load_environment(env)

    assert "link_1" in scene.link_actors
    scene.remove_link("link_1")
    assert "link_1" not in scene.link_actors
