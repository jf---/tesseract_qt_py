"""Demo tool path visualization."""
import numpy as np


def create_sample_paths():
    """Generate sample tool paths for testing."""
    # Spiral path
    t = np.linspace(0, 4 * np.pi, 100)
    spiral = np.column_stack([
        0.3 * np.cos(t),
        0.3 * np.sin(t),
        0.1 * t / (4 * np.pi)
    ])

    # Linear segments with different colors
    segment1 = np.array([[0, 0, 0], [0.5, 0, 0]])
    segment2 = np.array([[0.5, 0, 0], [0.5, 0.5, 0]])
    segment3 = np.array([[0.5, 0.5, 0], [0.5, 0.5, 0.5]])

    return {
        'spiral': spiral,
        'segments': [segment1, segment2, segment3]
    }


def add_demo_paths(scene_manager):
    """Add demonstration paths to scene manager.

    Args:
        scene_manager: SceneManager instance

    Example:
        scene_manager.add_tool_path(
            'spiral',
            paths['spiral'],
            color=(1.0, 0.0, 0.0),
            line_width=3.0,
            show_waypoints=True
        )
    """
    paths = create_sample_paths()

    # Add spiral path with waypoints
    scene_manager.add_tool_path(
        'spiral',
        paths['spiral'],
        color=(1.0, 0.0, 0.0),
        line_width=3.0,
        show_waypoints=True,
        waypoint_radius=0.005
    )

    # Add segmented path with different colors
    colors = [(1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)]
    for i, (seg, col) in enumerate(zip(paths['segments'], colors)):
        scene_manager.add_path_segment(
            'multi',
            f'seg_{i}',
            seg,
            color=col,
            line_width=4.0
        )
