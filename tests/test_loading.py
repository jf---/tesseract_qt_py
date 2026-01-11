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


def test_mesh_geometry_loading():
    """Test all mesh geometries are loaded with valid VTK polydata.

    Verifies:
    - All mesh links have VTK actors created
    - Actors have valid geometry (non-zero points)
    - Actors have distinct positions (not all at origin)
    """
    import vtk
    from core.scene_manager import SceneManager
    from tesseract_robotics.tesseract_environment import Environment
    from tesseract_robotics.tesseract_common import GeneralResourceLocator
    from tesseract_robotics.tesseract_geometry import GeometryType as GT

    urdf = FIXTURES / "abb_irb2400.urdf"
    env = Environment()
    loc = GeneralResourceLocator()
    env.init(str(urdf), loc)

    # Count mesh visuals in scene graph
    sg = env.getSceneGraph()
    mesh_links = []
    for link in sg.getLinks():
        for v in link.visual:
            if v.geometry.getType() in (GT.MESH, GT.CONVEX_MESH, GT.POLYGON_MESH):
                mesh_links.append(link.getName())
                break

    assert len(mesh_links) >= 7, f"Expected 7+ mesh links, got {len(mesh_links)}"

    # Load into SceneManager
    renderer = vtk.vtkRenderer()
    scene = SceneManager(renderer)
    scene.load_environment(env)

    # Verify all mesh links have actors
    for link in mesh_links:
        assert link in scene.link_actors, f"Missing actor for mesh link: {link}"
        actors = scene.link_actors[link]
        assert len(actors) > 0, f"No actors for mesh link: {link}"

        # Check actor has valid geometry
        for actor in actors:
            mapper = actor.GetMapper()
            assert mapper is not None, f"No mapper for {link}"
            polydata = mapper.GetInput()
            assert polydata is not None, f"No polydata for {link}"
            assert polydata.GetNumberOfPoints() > 0, f"No points in {link}"

    # Verify actors have distinct bounds (not all overlapping)
    centers = []
    for link in mesh_links:
        for actor in scene.link_actors[link]:
            centers.append(actor.GetCenter())

    # At least 5 unique positions (some tolerance for nearby links)
    unique_positions = set()
    for c in centers:
        rounded = (round(c[0], 1), round(c[1], 1), round(c[2], 1))
        unique_positions.add(rounded)
    assert len(unique_positions) >= 5, (
        f"Expected 5+ distinct positions, got {len(unique_positions)}"
    )


def test_compound_mesh_geometry():
    """Test COMPOUND_MESH geometry (used by Kuka iiwa).

    Verifies:
    - COMPOUND_MESH geometries are properly loaded
    - Multiple sub-meshes are combined
    - No crashes on complex mesh structures
    """
    import vtk
    import tesseract_robotics
    from core.scene_manager import SceneManager
    from tesseract_robotics.tesseract_environment import Environment
    from tesseract_robotics.tesseract_common import GeneralResourceLocator
    from tesseract_robotics.tesseract_geometry import GeometryType as GT

    support_dir = Path(tesseract_robotics.get_tesseract_support_path())
    urdf = support_dir / "urdf" / "lbr_iiwa_14_r820.urdf"

    if not urdf.exists():
        pytest.skip("iiwa URDF not found in tesseract_support")

    env = Environment()
    loc = GeneralResourceLocator()
    assert env.init(str(urdf), loc), f"Failed to load {urdf}"

    # Verify iiwa uses COMPOUND_MESH
    sg = env.getSceneGraph()
    compound_links = []
    for link in sg.getLinks():
        for v in link.visual:
            if v.geometry.getType() == GT.COMPOUND_MESH:
                compound_links.append(link.getName())
                break

    assert len(compound_links) >= 5, f"Expected 5+ COMPOUND_MESH links, got {len(compound_links)}"

    # Load into SceneManager - should not crash
    renderer = vtk.vtkRenderer()
    scene = SceneManager(renderer)
    scene.load_environment(env)

    # Verify actors were created for compound mesh links
    for link in compound_links:
        assert link in scene.link_actors, f"Missing actor for compound mesh: {link}"
        actors = scene.link_actors[link]
        assert len(actors) > 0, f"No actors for compound mesh: {link}"

        # Check actor has valid geometry
        for actor in actors:
            mapper = actor.GetMapper()
            assert mapper is not None, f"No mapper for {link}"
            polydata = mapper.GetInput()
            assert polydata is not None, f"No polydata for {link}"
            assert polydata.GetNumberOfPoints() > 0, f"Empty geometry for {link}"


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


def test_reload_multiple_robots(qapp):
    """Test reloading multiple URDF/SRDF pairs doesn't break signal wiring.

    Loads several different robots sequentially and verifies:
    - No crashes on reload
    - Widgets update correctly
    - Signals remain connected
    - Joint sliders match new robot
    """
    import tesseract_robotics
    from widgets.manipulation_widget import ManipulationWidget
    from core.scene_manager import SceneManager
    from tesseract_robotics.tesseract_environment import Environment
    from tesseract_robotics.tesseract_common import GeneralResourceLocator
    from tesseract_robotics.tesseract_scene_graph import JointType
    import vtk

    support_dir = Path(tesseract_robotics.get_tesseract_support_path())
    urdf_dir = support_dir / "urdf"

    # Robot configs to test (urdf, srdf)
    robots = [
        ("abb_irb2400.urdf", "abb_irb2400.srdf"),
        ("lbr_iiwa_14_r820.urdf", "lbr_iiwa_14_r820.srdf"),
        ("boxbot.urdf", "boxbot.srdf"),
        ("abb_irb2400.urdf", "abb_irb2400.srdf"),  # Reload first robot
    ]

    # Filter to existing files
    valid_robots = []
    for urdf, srdf in robots:
        urdf_path = urdf_dir / urdf
        srdf_path = urdf_dir / srdf
        if urdf_path.exists() and srdf_path.exists():
            valid_robots.append((urdf_path, srdf_path))

    if len(valid_robots) < 2:
        pytest.skip("Need at least 2 robots in tesseract_support")

    # Create widgets
    renderer = vtk.vtkRenderer()
    scene = SceneManager(renderer)
    manip = ManipulationWidget()

    # Track signal emissions
    joint_signals = []
    manip.jointValuesChanged.connect(lambda v: joint_signals.append(v))

    loc = GeneralResourceLocator()
    prev_joint_count = 0
    loaded_count = 0

    for urdf_path, srdf_path in valid_robots:
        # Load environment (some SRDFs have missing deps, skip those)
        env = Environment()
        if not env.init(str(urdf_path), str(srdf_path), loc):
            continue  # Skip robots that fail to load

        loaded_count += 1

        # Load into scene
        scene.load_environment(env)

        # Get joints
        sg = env.getSceneGraph()
        movable = (JointType.REVOLUTE, JointType.CONTINUOUS, JointType.PRISMATIC)
        joints = {}
        for j in sg.getJoints():
            if j.type in movable:
                lim = j.limits
                lo, hi = (lim.lower, lim.upper) if lim else (-3.14, 3.14)
                joints[j.getName()] = (lo, hi, 0.0)

        # Update manipulation widget
        manip.set_environment(env)
        manip.set_joint_limits(joints)

        # Verify joints changed (different robots have different joints)
        current_count = len(joints)
        if prev_joint_count > 0 and current_count != prev_joint_count:
            # Joint count changed - widget should reflect this
            widget_joints = manip.get_joint_values()
            assert len(widget_joints) == current_count, (
                f"Widget joints {len(widget_joints)} != env joints {current_count}"
            )

        prev_joint_count = current_count

        # Verify scene has actors
        assert len(scene.link_actors) > 0, f"No actors after loading {urdf_path.name}"

    # Verify we loaded at least 2 different robots
    assert loaded_count >= 2, f"Need 2+ robots to test reload, only loaded {loaded_count}"


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
        ContactTestType,
        ContactRequest,
        ContactResultMap,
        ContactResultVector,
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
