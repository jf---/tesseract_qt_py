# Tool Path Visualization

Tool path visualization added to `SceneManager` class.

## Basic Usage

```python
import numpy as np
from core.scene_manager import SceneManager

# Create path points (Nx3 array)
points = np.array([
    [0, 0, 0],
    [0.5, 0, 0],
    [0.5, 0.5, 0.2],
    [1.0, 0.5, 0.4]
])

# Add path with waypoints
scene_manager.add_tool_path(
    path_id='my_path',
    points=points,
    color=(1.0, 0.0, 0.0),  # Red
    line_width=3.0,
    show_waypoints=True,
    waypoint_radius=0.01
)
```

## Multi-Segment Paths

```python
# Different colors per segment
scene_manager.add_path_segment(
    path_id='multi_path',
    segment_id='approach',
    points=approach_points,
    color=(0.0, 1.0, 0.0),  # Green
    line_width=2.0
)

scene_manager.add_path_segment(
    path_id='multi_path',
    segment_id='cut',
    points=cut_points,
    color=(1.0, 0.0, 0.0),  # Red
    line_width=4.0
)
```

## Clear/Update

```python
# Clear specific path
scene_manager.clear_path('my_path')

# Update (auto-clears existing)
scene_manager.add_tool_path('my_path', new_points)
```

## API

### `add_tool_path(path_id, points, color, line_width, show_waypoints, waypoint_radius)`
- `path_id`: Unique identifier
- `points`: Nx3 numpy array
- `color`: RGB tuple (0-1)
- `line_width`: Line thickness
- `show_waypoints`: Display sphere markers
- `waypoint_radius`: Sphere size

### `add_path_segment(path_id, segment_id, points, color, line_width)`
- Creates sub-path under parent `path_id`
- No waypoints shown

### `clear_path(path_id)`
- Removes path from scene
