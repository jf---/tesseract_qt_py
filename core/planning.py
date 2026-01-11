"""Motion planning helpers for Tesseract.

Uses the high-level tesseract_robotics.planning API.
"""

from __future__ import annotations

from tesseract_robotics.planning import (
    CartesianTarget,
    MotionProgram,
    Pose,
    Robot,
    TaskComposer,
)


class PlanningHelper:
    """Simplifies motion planning with Tesseract task composer."""

    def __init__(self, robot: Robot, composer: TaskComposer | None = None):
        self.robot = robot
        self.composer = composer or TaskComposer.from_config()

    @classmethod
    def from_env(cls, env, manipulator: str = "manipulator") -> PlanningHelper:
        """Create from existing environment."""
        robot = Robot(env, manipulator)
        return cls(robot)

    def plan_freespace(
        self,
        target_poses: list[Pose],
        manipulator: str = "manipulator",
        tcp_frame: str = "tool0",
        profile: str = "DEFAULT",
        pipeline: str = "FreespacePipeline",
    ):
        """Plan freespace motion to target poses.

        Args:
            target_poses: List of Pose targets
            manipulator: Manipulator name from SRDF
            tcp_frame: Tool center point frame
            profile: Planning profile name
            pipeline: Task composer pipeline

        Returns:
            PlanResult or None on failure
        """
        if not target_poses:
            return None

        program = MotionProgram(manipulator, tcp_frame=tcp_frame, profile=profile)

        for pose in target_poses:
            program.move_to(CartesianTarget(pose, profile=profile))

        return self.composer.plan(self.robot, program, pipeline=pipeline)

    def plan_linear(
        self,
        target_poses: list[Pose],
        manipulator: str = "manipulator",
        tcp_frame: str = "tool0",
        profile: str = "DEFAULT",
        pipeline: str = "CartesianPipeline",
    ):
        """Plan linear Cartesian motion to target poses.

        Args:
            target_poses: List of Pose targets
            manipulator: Manipulator name from SRDF
            tcp_frame: Tool center point frame
            profile: Planning profile name
            pipeline: Task composer pipeline

        Returns:
            PlanResult or None on failure
        """
        if not target_poses:
            return None

        program = MotionProgram(manipulator, tcp_frame=tcp_frame, profile=profile)

        for i, pose in enumerate(target_poses):
            if i == 0:
                program.move_to(CartesianTarget(pose, profile=profile))
            else:
                program.linear_to(CartesianTarget(pose, profile=profile))

        return self.composer.plan(self.robot, program, pipeline=pipeline)

    @staticmethod
    def make_pose(xyz: tuple[float, float, float], quat: tuple[float, float, float, float]) -> Pose:
        """Create Pose from position and quaternion (w,x,y,z)."""
        return Pose.from_xyz_quat(*xyz, *quat)
