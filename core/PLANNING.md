# Motion Planning Module

`core/planning.py` provides high-level motion planning helpers using Tesseract's task composer framework.

## PlanningHelper

Main class wrapping Tesseract planning functionality.

### Initialization

```python
from core.planning import PlanningHelper
from pathlib import Path

planner = PlanningHelper(env, config_path=Path("/path/to/task_composer_plugins.yaml"))
```

Config file location: typically from `tesseract_planning/tesseract_task_composer/config/task_composer_plugins*.yaml`

### Methods

#### plan_freespace()

Plans collision-free freespace motion to target Cartesian poses.

```python
targets = [
    planner.make_pose((0.8, -0.3, 1.4), (0.707, 0, 0.707, 0)),
    planner.make_pose((0.8, 0.3, 1.4), (0.707, 0, 0.707, 0)),
]

result = planner.plan_freespace(
    targets,
    manipulator="manipulator",  # from SRDF
    tcp_frame="tool0",
    working_frame="base_link"
)
```

Uses FreespacePipeline: OMPL for collision-free path, TrajOpt for refinement, time parameterization.

#### plan_linear()

Plans Cartesian linear motion between poses.

```python
result = planner.plan_linear(
    targets,
    manipulator="manipulator",
    tcp_frame="tool0",
    working_frame="base_link"
)
```

First waypoint uses freespace, subsequent use linear interpolation. Uses CartesianPipeline.

#### extract_joint_trajectory()

Extracts joint positions and timestamps from planned trajectory.

```python
trajectory = planner.extract_joint_trajectory(result)
for positions, timestamp in trajectory:
    print(f"Joints: {positions}, Time: {timestamp}")
```

Returns: `list[tuple[np.ndarray, float]]`

#### make_pose()

Helper to create Isometry3d transforms.

```python
pose = planner.make_pose(
    xyz=(0.8, 0.3, 1.4),
    quat=(w, x, y, z)  # quaternion in w,x,y,z order
)
```

## Environment Setup

Required environment variables (if using package URLs):

```bash
export TESSERACT_RESOURCE_PATH="/path/to/tesseract/"
export TESSERACT_TASK_COMPOSER_CONFIG_FILE="/path/to/task_composer_plugins.yaml"
```

Or distribute config file with application and pass absolute path to PlanningHelper.

## Dependencies

- tesseract_robotics.tesseract_common
- tesseract_robotics.tesseract_command_language
- tesseract_robotics.tesseract_task_composer

## Example

See `examples/planning_example.py` for complete usage example.
