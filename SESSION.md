# Session State - 2024-12-24

## Repository
- GitHub: https://github.com/jf---/tesseract_qt_py
- Branch: main
- Latest commit: 68149ba - "fix contact compute + add all P2 docks"

## Completed

### P1 Features (All Done)
- Contact Results Table - QTableWidget with results
- Joint Trajectory Plot - matplotlib, tabbed with trajectory player
- Environment Commands - context menu signals
- Motion Planning UI - Plan Motion button in IK widget

### P2 Features (All Done)
- ACM Editor - wired to app, loads from env
- Kinematic Groups Editor - signals + button handlers
- ManipulationWidget - CartesianEditor embedded, mode switching
- Group States Editor - new widget (190 LOC)
- TCP Editor - new widget (117 LOC)

### UI Polish
- Tabified right panel (9 docks)
- Tabified bottom panel (trajectory + plot)
- Fixed window sizing
- Joint sorting alphabetical
- matplotlib margins

## Current State
- 12 commits ahead of upstream tesseract_qt
- All widget tests pass (except 1 needing tesseract_robotics)
- App runs with TESSERACT_RESOURCE_PATH set

## How to Run
```bash
export TESSERACT_RESOURCE_PATH="/Users/jelle/Code/CADCAM/tesseract_python_nanobind/ws/install/share"
cd /Users/jelle/Code/CADCAM/tesseract_qt_py
/opt/miniconda3/envs/tesseract_nb/bin/python app.py /path/to/robot.urdf
```

## Remaining (P3)
- Undo/Redo
- Multiple Environments
- Logging Panel
- Task Composer execution wiring

## Key Files Modified
- app.py - main application (~850 LOC)
- widgets/plot_widget.py - matplotlib plotting
- widgets/manipulation_widget.py - 4-tab control
- widgets/kinematic_groups_editor.py - signals added
- widgets/group_states_editor.py - NEW
- widgets/tcp_editor.py - NEW
- widgets/acm_editor.py - wired to app
- core/scene_manager.py - Box API fix

## Notes
- Contact compute uses BulletDiscreteBVHManager via plugin factory
- Plugin config path hardcoded: /Users/jelle/Code/CADCAM/tesseract_python_nanobind/ws/install/share/tesseract_support/urdf/contact_manager_plugins.yaml
- QPainter warnings are cosmetic (macOS VTK/Qt)
