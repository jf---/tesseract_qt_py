"""Demo workspace visualization."""



def visualize_workspace(scene_manager, joint_names, joint_limits, tcp_link, n_samples=1000):
    """Visualize robot workspace with distance-based coloring.

    Args:
        scene_manager: SceneManager instance
        joint_names: List of joint names to sample
        joint_limits: Dict of joint name -> (min, max)
        tcp_link: TCP link name
        n_samples: Number of samples

    Example:
        joint_names = ['joint_1', 'joint_2', 'joint_3']
        joint_limits = {
            'joint_1': (-3.14, 3.14),
            'joint_2': (-1.57, 1.57),
            'joint_3': (-2.0, 2.0),
        }
        visualize_workspace(scene, joint_names, joint_limits, 'tool0', 2000)
    """
    # Set TCP link
    scene_manager.set_tcp_link(tcp_link)

    # Sample workspace
    print(f"Sampling {n_samples} configurations...")
    points = scene_manager.sample_workspace(joint_names, joint_limits, n_samples, tcp_link)
    print(f"Generated {len(points)} reachable points")

    # Compute distance metric
    scalars = scene_manager.compute_manipulability(points)

    # Display
    scene_manager.show_workspace(points, scalars, point_size=4.0, opacity=0.7)
    print("Workspace visualization complete (blue=near center, red=far)")


def visualize_workspace_simple(scene_manager, joint_names, joint_limits, tcp_link, n_samples=500):
    """Simple workspace visualization without coloring.

    Args:
        scene_manager: SceneManager instance
        joint_names: List of joint names
        joint_limits: Joint limit dict
        tcp_link: TCP link name
        n_samples: Number of samples
    """
    scene_manager.set_tcp_link(tcp_link)
    points = scene_manager.sample_workspace(joint_names, joint_limits, n_samples, tcp_link)
    scene_manager.show_workspace(points, point_size=3.0, opacity=0.5)
    print(f"Workspace: {len(points)} points")
