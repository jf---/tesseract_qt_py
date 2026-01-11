"""FK visualization demo."""


# Example usage of FK visualization methods


def demo_fk_viz(scene_manager, joint_values):
    """Demo forward kinematics visualization.

    Args:
        scene_manager: SceneManager instance
        joint_values: dict of joint_name -> value
    """
    # 1. Get TCP pose from joint values
    tcp_link = "tool0"  # or your end effector link name
    tcp_pose = scene_manager.get_tcp_pose(joint_values, tcp_link)

    if tcp_pose:
        # 2. Display TCP marker
        scene_manager.show_tcp_marker(
            tcp_pose,
            radius=0.03,
            color=(1.0, 0.0, 1.0),  # magenta
        )

        # 3. Show FK chain from base to TCP
        scene_manager.show_fk_chain(
            joint_values,
            base_link="base_link",
            tip_link=tcp_link,
            line_width=4.0,
            color=(0.0, 1.0, 1.0),  # cyan
        )

    # Clear FK viz when done
    # scene_manager.clear_fk_viz()
