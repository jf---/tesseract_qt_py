# tesseract_qt_py

## CRITICAL: Import Order & Plugin Setup

```python
# 1. Import tesseract_robotics FIRST - sets up plugin paths
import tesseract_robotics

# 2. macOS VTK+Qt setup
import os
os.environ.pop('DISPLAY', None)  # NO X11 EVER
os.environ['QT_QPA_PLATFORM'] = 'cocoa'

import vtkmodules.qt
vtkmodules.qt.QVTKRWIBase = "QOpenGLWidget"  # Required for rendering

# 3. THEN import Qt and VTK widgets
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
```

- Without `import tesseract_robotics` first, plugin env vars not set
- Without `QVTKRWIBase = "QOpenGLWidget"`, VTK renders to invisible buffer

## CRITICAL: Collision Detection Requires SRDF

Contact manager only works when loading with SRDF:
```python
# Works - SRDF loads contact_manager_plugins.yaml
env.init(urdf_path, srdf_path, locator)
manager = env.getDiscreteContactManager()  # Returns valid manager

# Fails - no plugin config loaded
env.init(urdf_path, locator)
manager = env.getDiscreteContactManager()  # Returns None!
```

The SRDF contains `<contact_managers_plugin_config filename="..."/>` which triggers plugin loading.

---

Python/Qt6/VTK replacement for tesseract_qt. ~7.3k LOC + 2.2k tests vs 59k C++ LOC.

## Why

Original C++ tesseract_qt has Qt5/Qt6 conflicts + Gazebo/OGRE dependencies that don't build cleanly on macOS. This port uses PySide6 (Qt6) + VTK - no OGRE drama.

## Architecture

```
tesseract_qt_py/
├── core/
│   ├── scene_manager.py   # VTK scene from tesseract Environment
│   ├── camera_control.py  # Orbit/pan/zoom camera
│   ├── state_manager.py   # Joint pose save/restore
│   ├── planning.py        # Motion planning helpers
│   └── contact_viz.py     # Contact visualization
├── widgets/
│   ├── render_widget.py   # VTK viewport + toolbar
│   ├── joint_slider.py    # Joint controls
│   ├── scene_tree.py      # Scene graph tree
│   ├── plot_widget.py     # Pyqtgraph joint plots
│   ├── trajectory_player.py # Trajectory playback
│   ├── ik_widget.py       # IK solver UI
│   ├── info_panel.py      # Robot info display
│   ├── studio_layout.py   # Main window with menus/toolbar
│   ├── manipulation_widget.py # 4-tab robot control
│   ├── acm_editor.py      # Allowed collision matrix editor
│   ├── srdf_editor.py     # SRDF toolbox editor
│   ├── cartesian_editor.py # XYZ + RPY editor
│   ├── contact_compute_widget.py # Contact params
│   ├── kinematic_groups_editor.py # Chain/joints/links
│   ├── task_composer_widget.py # Task config/logs
│   ├── log_widget.py      # Real-time loguru log viewer
│   ├── tool_path_dialog.py # Tool path file picker
│   └── environment_dialog.py # URDF/SRDF loader
├── examples/
│   ├── planning_example.py
│   ├── tool_path_demo.py
│   ├── workspace_demo.py
│   ├── fk_viz_demo.py
│   ├── contact_viz_example.py
│   └── info_panel_demo.py
├── app.py                 # Main application
└── pyproject.toml
```

## Dependencies

- PySide6
- VTK (vtkmodules)
- tesseract-robotics-nanobind (tesseract_robotics)
- pyqtgraph (optional, for plotting)

## Run

```bash
# Preferred: use pixi (overlays tesseract_nb conda env)
pixi run app /path/to/robot.urdf [/path/to/robot.srdf]

# Or directly
./run_app.sh /path/to/robot.urdf
```

## Testing

```bash
pixi run test  # parallel with xdist
```

## Pixi Tasks

- `pixi run test` - parallel tests
- `pixi run app` - launch viewer
- `pixi run check` - verify deps
- `pixi run lint` / `pixi run fmt` - ruff

## CRITICAL: tesseract 0.33+ URDF Requirements

URDFs must have `tesseract:make_convex` attribute on `<robot>` element:
```xml
<robot name="my_robot"
       xmlns:tesseract="http://www.tesseract.com"
       tesseract:make_convex="true">
```
- `true` = auto-convert collision meshes to convex hulls (old default)
- `false` = use original mesh geometry (slower but more accurate)

## Editable Install Path Gotcha

When `tesseract_robotics` is installed in editable mode, `get_tesseract_support_path()` returns the source directory which may lack data files. The app searches `sys.path` for the installed package location as fallback.

## Keyboard Shortcuts

- **1-7**: Standard views (Front/Back/Left/Right/Top/Bottom/Iso)
- **Home**: Reset view
- **F**: Fit view
- **G**: Toggle grid
- **A**: Toggle axes
- **Ctrl+S**: Save config
- **Ctrl+O**: Open URDF

## API Notes

Enum access patterns:
```python
from tesseract_robotics.tesseract_geometry import GeometryType
GT = GeometryType
if geom_type == GT.SPHERE:  # not GeometryType_SPHERE

from tesseract_robotics.tesseract_scene_graph import JointType
movable = (JointType.REVOLUTE, JointType.CONTINUOUS, JointType.PRISMATIC)
```

Use absolute imports (not relative):
```python
from core.scene_manager import SceneManager  # not ..core
```

## Features

### Visualization
- All geometry types (box, sphere, cylinder, capsule, mesh)
- Camera orbit/pan/zoom
- Ground grid + axes widget
- Link coordinate frames
- TCP frame display
- Tool path visualization
- Contact results visualization
- FK chain visualization
- Workspace point cloud

### Widgets
- Joint sliders with limits
- Scene tree with visibility toggles
- Link picking/highlighting
- Trajectory player (play/pause/scrub)
- Joint plot widget (pyqtgraph)
- IK solver widget
- Robot info panel (DOF, TCP pose)
- Main window (menus/toolbar)
- 4-tab manipulation control
- ACM editor
- SRDF toolbox editor
- Cartesian XYZ+RPY editor
- Contact compute params
- Kinematic groups (chain/joints/links)
- Task composer (config/logs)
- Log viewer (color-coded, level filter)
- Tool path/environment dialogs

### File Operations
- URDF/SRDF loading with dialogs
- Recent files menu (persisted)
- Screenshot export (PNG)
- Scene export (STL/OBJ)
- State save/load (JSON)
- Named pose save/restore

### Motion Planning
```python
from core.planning import PlanningHelper

planner = PlanningHelper(env, config_path)
result = planner.plan_freespace(targets)
trajectory = planner.extract_joint_trajectory(result)
```

### Workspace Visualization
```python
points = scene.sample_workspace(joint_names, joint_limits, n_samples=1000, tcp_link="tool0")
scalars = scene.compute_manipulability(points)
scene.show_workspace(points, scalars, point_size=3.0)
```

## SceneManager Key Methods

```python
# Loading
load_environment(env)
update_joint_values(joint_values)

# Visualization
set_link_visibility(link, visible)
highlight_link(link)
show_frame(link, visible)
set_tcp_link(link)

# Tool paths
add_tool_path(path_id, points, color, line_width)
add_path_segment(path_id, p1, p2, color, line_width)
clear_path(path_id)

# Contacts
visualize_contacts(contact_results)
clear_contacts()

# FK/Workspace
get_tcp_pose(joint_values, tcp_link)
show_tcp_marker(pose, radius, color)
show_fk_chain(joint_values, base_link, tip_link)
sample_workspace(joint_names, joint_limits, n_samples)
show_workspace(points, scalars)
```

## Development Status (branch jf/update_tesseract_033)

### tesseract 0.33 Update
- Added `tesseract:make_convex` to test fixture URDF
- Pixi environment overlaying tesseract_nb conda env
- Robust default URDF path resolution for editable installs

### Recent Additions
- `widgets/log_widget.py` - loguru log viewer with color-coding, level filter, auto-scroll, `loguru_sink()` method
- Window state persistence (geometry, dock positions via QSettings)
- closeEvent cleanup (stops timers, saves state)
- Tooltips on cartesian_editor, manipulation_widget

### Logging

**Python (loguru)** - all modules use loguru:

- `core/scene_manager.py`
- `widgets/ik_widget.py`
- `widgets/info_panel.py`

**Tesseract C++ logging** - ALWAYS enable when debugging crashes:

```python
import tesseract_robotics.tesseract_common as tc

# Levels: TRACE, DEBUG, INFO, WARN, ERROR, FATAL
tc.setLogLevel(tc.LogLevel.DEBUG)

# Call BEFORE loading environment to catch init errors
```

C++ warnings appear as `Warning:` or `Error:` in stderr. Enable TRACE/DEBUG to see what tesseract is doing before a segfault. This is non-negotiable for crash debugging.

### Known Issues

- Qt dock objectName warnings (cosmetic, affects state restore)
  - Fix: `dock.setObjectName("dock_name")` for each QDockWidget in app.py
- ~~URDF reload crash when switching between different robots~~ **FIXED**
  - Was: `fkik_widget.set_environment()` called `setState()` with stale joint names
  - Fix: Removed premature `_update_ik_from_fk()` call

## CRITICAL: URDF/SRDF Are Always Paired

**NEVER delete or separate URDF from its SRDF.** They are a matched pair:

- URDF defines geometry and kinematics
- SRDF defines semantic info (groups, ACM, states, plugin configs)

When copying robot files to fixtures, copy ALL related files:

- `robot.urdf`
- `robot.srdf`
- Any referenced config YAMLs (check SRDF for `<kinematics_plugin_config>`)
- Mesh files if using `package://` paths

### Test Coverage
108 tests passing, 5 skipped. Gaps: CameraController, PlanningHelper, ContactVisualizer
