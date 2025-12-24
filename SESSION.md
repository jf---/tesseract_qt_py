# Session State - 2024-12-24

## Repository
- GitHub: https://github.com/jf---/tesseract_qt_py
- Branch: main
- 109 tests passing

## CRITICAL: Plugin Setup

### Import Order
```python
import tesseract_robotics  # FIRST - sets up plugin paths
```
The root `tesseract_robotics.__init__` sets:
- `TESSERACT_CONTACT_MANAGERS_PLUGIN_DIRECTORIES`
- `TESSERACT_KINEMATICS_PLUGIN_DIRECTORIES`
- `TESSERACT_TASK_COMPOSER_PLUGIN_DIRECTORIES`

### SRDF Required for Collision Detection
Contact manager only works with SRDF:
```python
env.init(urdf_path, srdf_path, locator)  # Works
env.init(urdf_path, locator)  # getDiscreteContactManager() returns None!
```
SRDF contains `<contact_managers_plugin_config>` that loads plugins.

## Completed Features

### P1 - Core
- Real-time collision detection (links turn red on collision)
- Contact Results Table with detailed info
- Joint Trajectory Plot (pyqtgraph)
- Environment Commands

### P2 - Enhanced
- Task Composer (wired with high-level planning API)
- ACM Editor (loads from SRDF)
- Kinematic Groups Editor
- Group States Editor
- TCP Editor
- Manipulation Widget
- Cartesian Editor (XYZ + RPY sliders with IK)

### UI
- Tabified docks
- VTK resize fix (resizeEvent)
- Initial camera focus on robot bounds (not grid)
- TCP pose in status bar (XYZ + RPY degrees) - right side, updates real-time
- Uncaught exception logging via `sys.excepthook` -> loguru

## How to Run
```bash
conda activate tesseract_nb
cd ~/Code/CADCAM/tesseract_qt_py
python app.py /path/to/robot.urdf /path/to/robot.srdf
```

## Remaining (P3 - Nice to Have)
- Undo/Redo
- Multiple Environments
- Dockable log panel
- **Interactive IK gimbal at tool frame** (drag to move robot via IK)

## Key API Notes
- `env.setState(joint_dict)` - use dict, not `(list, list)`
- `state.joints` - not `state.joint_positions`
- `SceneState` attributes: `joints`, `link_transforms`, `joint_transforms`
- Isometry3d: `tf.translation()` and `tf.rotation()` are methods, not properties
- PySide6 status bar: add permanent widgets BEFORE `setStatusBar()` to avoid Qt ownership deletion

## Notes
- QPainter warnings are cosmetic (macOS VTK/Qt)
- Kinematics plugins (KDL/OPW) fail on macOS due to `@rpath` not resolving in dlopen
  - Symbols exist (`nm -gU`), but runtime loading fails
  - Bug filed: see `tesseract_nanobind/tests/test_kinematics_plugin_loading.py`
  - Numerical IK fallback works
