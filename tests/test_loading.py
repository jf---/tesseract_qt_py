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


def test_contact_detection_with_joint_values():
    """Test contact detection uses current joint state.

    When joints are moved to collision pose, contact checker must detect it.
    Requires SRDF for contact manager to be available.
    Uses tesseract_support paths because SRDF needs package:// resolution.
    """
    import math
    import tesseract_robotics  # Set up plugin paths
    from tesseract_robotics.tesseract_environment import Environment
    from tesseract_robotics.tesseract_common import GeneralResourceLocator, CollisionMarginData
    from tesseract_robotics.tesseract_collision import (
        ContactTestType, ContactRequest, ContactResultMap, ContactResultVector
    )

    # Use installed tesseract_support (has proper package:// resolution)
    support_dir = Path(tesseract_robotics.get_tesseract_support_path())
    if not support_dir.exists():
        # Fallback to ws/install for dev mode
        import os
        support_dir = Path(os.environ.get("TESSERACT_SUPPORT_DIR", ""))
    urdf = support_dir / "urdf" / "abb_irb2400.urdf"
    srdf = support_dir / "urdf" / "abb_irb2400.srdf"

    if not urdf.exists() or not srdf.exists():
        pytest.skip("tesseract_support not found")

    env = Environment()
    loc = GeneralResourceLocator()
    assert env.init(str(urdf), str(srdf), loc), "Failed to init with SRDF"

    manager = env.getDiscreteContactManager()
    assert manager is not None, "Contact manager not available (needs SRDF)"

    manager.setActiveCollisionObjects(env.getActiveLinkNames())
    manager.setCollisionMarginData(CollisionMarginData(0.01))

    # Home position - no collision
    home_joints = {f"joint_{i}": 0.0 for i in range(1, 7)}
    env.setState(home_joints)
    state = env.getState()
    manager.setCollisionObjectsTransform(state.link_transforms)

    request = ContactRequest(ContactTestType.ALL)
    result_map = ContactResultMap()
    manager.contactTest(result_map, request)
    results = ContactResultVector()
    result_map.flattenMoveResults(results)
    assert len(results) == 0, f"Home pose should have no collisions, found {len(results)}"

    # Collision pose: joint_2=110deg, joint_3=61deg
    collision_joints = {
        "joint_1": 0.0,
        "joint_2": math.radians(110),
        "joint_3": math.radians(61),
        "joint_4": 0.0,
        "joint_5": 0.0,
        "joint_6": 0.0,
    }
    env.setState(collision_joints)
    state = env.getState()
    manager.setCollisionObjectsTransform(state.link_transforms)

    result_map2 = ContactResultMap()
    manager.contactTest(result_map2, request)
    results2 = ContactResultVector()
    result_map2.flattenMoveResults(results2)
    assert len(results2) > 0, "Collision pose should detect contacts"

    # Verify joint state was actually updated
    assert state.joints["joint_2"] == pytest.approx(math.radians(110), rel=1e-6)
    assert state.joints["joint_3"] == pytest.approx(math.radians(61), rel=1e-6)
