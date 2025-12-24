# tesseract_qt_py

## CRITICAL: macOS VTK+Qt Setup

```python
# MUST be at top of any VTK+Qt file on macOS
import os
os.environ.pop('DISPLAY', None)  # NO X11 EVER
os.environ['QT_QPA_PLATFORM'] = 'cocoa'

import vtkmodules.qt
vtkmodules.qt.QVTKRWIBase = "QOpenGLWidget"  # Required for rendering to work

# THEN import Qt and VTK widgets
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
```

Without `QVTKRWIBase = "QOpenGLWidget"`, VTK renders to invisible buffer (glass sheet window).

---

Python/Qt6/VTK replacement for tesseract_qt. ~1500 LOC vs 59k C++ LOC.

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
conda activate tesseract_nb
cd ~/Code/CADCAM/tesseract_qt_py
python app.py /path/to/robot.urdf [/path/to/robot.srdf]
```

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
