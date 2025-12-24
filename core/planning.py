"""Motion planning helpers for Tesseract."""
from __future__ import annotations

import numpy as np
from pathlib import Path

from tesseract_robotics.tesseract_common import (
    ManipulatorInfo,
    Isometry3d,
    Translation3d,
    Quaterniond,
    FilesystemPath,
    AnyPoly_wrap_CompositeInstruction,
    AnyPoly_as_CompositeInstruction,
)
from tesseract_robotics.tesseract_command_language import (
    CartesianWaypoint,
    CartesianWaypointPoly_wrap_CartesianWaypoint,
    MoveInstruction,
    MoveInstructionPoly_wrap_MoveInstruction,
    MoveInstructionType_FREESPACE,
    MoveInstructionType_LINEAR,
    CompositeInstruction,
    ProfileDictionary,
    InstructionPoly_as_MoveInstructionPoly,
    WaypointPoly_as_StateWaypointPoly,
)
from tesseract_robotics.tesseract_task_composer import (
    TaskComposerPluginFactory,
    PlanningTaskComposerProblemUPtr,
    PlanningTaskComposerProblemUPtr_as_TaskComposerProblemUPtr,
    TaskComposerDataStorage,
    TaskComposerInput,
)


class PlanningHelper:
    """Simplifies motion planning with Tesseract task composer."""

    def __init__(self, env, config_path: Path | str):
        self.env = env
        self.factory = TaskComposerPluginFactory(FilesystemPath(str(config_path)))
        self.executor = self.factory.createTaskComposerExecutor("TaskflowExecutor")

    def plan_freespace(
        self,
        target_poses: list[Isometry3d],
        manipulator: str = "manipulator",
        tcp_frame: str = "tool0",
        working_frame: str = "base_link",
        profile: str = "DEFAULT",
    ) -> CompositeInstruction | None:
        """Plan freespace motion to target poses.

        Args:
            target_poses: List of target Isometry3d transforms
            manipulator: Manipulator name from SRDF
            tcp_frame: Tool center point frame
            working_frame: Base frame for planning
            profile: Planning profile name

        Returns:
            Planned trajectory as CompositeInstruction or None on failure
        """
        if not target_poses:
            return None

        manip_info = ManipulatorInfo()
        manip_info.tcp_frame = tcp_frame
        manip_info.manipulator = manipulator
        manip_info.working_frame = working_frame

        # Build program with waypoints
        program = CompositeInstruction(profile)
        program.setManipulatorInfo(manip_info)

        for i, pose in enumerate(target_poses):
            wp = CartesianWaypoint(pose)
            wp_poly = CartesianWaypointPoly_wrap_CartesianWaypoint(wp)
            instr = MoveInstruction(wp_poly, MoveInstructionType_FREESPACE, profile)
            program.appendMoveInstruction(MoveInstructionPoly_wrap_MoveInstruction(instr))

        return self._execute_pipeline("FreespacePipeline", program)

    def plan_linear(
        self,
        target_poses: list[Isometry3d],
        manipulator: str = "manipulator",
        tcp_frame: str = "tool0",
        working_frame: str = "base_link",
        profile: str = "DEFAULT",
    ) -> CompositeInstruction | None:
        """Plan linear Cartesian motion to target poses.

        Args:
            target_poses: List of target Isometry3d transforms
            manipulator: Manipulator name from SRDF
            tcp_frame: Tool center point frame
            working_frame: Base frame for planning
            profile: Planning profile name

        Returns:
            Planned trajectory as CompositeInstruction or None on failure
        """
        if not target_poses:
            return None

        manip_info = ManipulatorInfo()
        manip_info.tcp_frame = tcp_frame
        manip_info.manipulator = manipulator
        manip_info.working_frame = working_frame

        program = CompositeInstruction(profile)
        program.setManipulatorInfo(manip_info)

        for i, pose in enumerate(target_poses):
            wp = CartesianWaypoint(pose)
            wp_poly = CartesianWaypointPoly_wrap_CartesianWaypoint(wp)
            move_type = MoveInstructionType_FREESPACE if i == 0 else MoveInstructionType_LINEAR
            instr = MoveInstruction(wp_poly, move_type, profile)
            program.appendMoveInstruction(MoveInstructionPoly_wrap_MoveInstruction(instr))

        return self._execute_pipeline("CartesianPipeline", program)

    def _execute_pipeline(
        self, pipeline_name: str, program: CompositeInstruction
    ) -> CompositeInstruction | None:
        """Execute task composer pipeline.

        Args:
            pipeline_name: Name of pipeline (FreespacePipeline, CartesianPipeline, etc)
            program: Input CompositeInstruction program

        Returns:
            Planned trajectory or None on failure
        """
        try:
            task = self.factory.createTaskComposerNode(pipeline_name)
            input_key = task.getInputKeys()[0]
            output_key = task.getOutputKeys()[0]

            profiles = ProfileDictionary()
            task_data = TaskComposerDataStorage()
            task_data.setData(input_key, AnyPoly_wrap_CompositeInstruction(program))

            task_problem_unique = PlanningTaskComposerProblemUPtr.make_unique(
                self.env, task_data, profiles
            )
            task_problem = PlanningTaskComposerProblemUPtr_as_TaskComposerProblemUPtr(
                task_problem_unique
            )
            task_input = TaskComposerInput(task_problem)

            future = self.executor.run(task.get(), task_input)
            future.wait()

            return AnyPoly_as_CompositeInstruction(task_input.data_storage.getData(output_key))

        except Exception as e:
            print(f"Planning failed: {e}")
            return None

    @staticmethod
    def extract_joint_trajectory(result: CompositeInstruction) -> list[tuple[np.ndarray, float]]:
        """Extract joint positions and timestamps from planned trajectory.

        Args:
            result: Planned CompositeInstruction trajectory

        Returns:
            List of (joint_positions, timestamp) tuples
        """
        trajectory = []
        for instr in result:
            if not instr.isMoveInstruction():
                continue
            move_instr = InstructionPoly_as_MoveInstructionPoly(instr)
            wp = move_instr.getWaypoint()
            if not wp.isStateWaypoint():
                continue
            state_wp = WaypointPoly_as_StateWaypointPoly(wp)
            positions = state_wp.getPosition().flatten()
            timestamp = state_wp.getTime()
            trajectory.append((positions, timestamp))
        return trajectory

    @staticmethod
    def make_pose(xyz: tuple[float, float, float], quat: tuple[float, float, float, float]) -> Isometry3d:
        """Create Isometry3d from position and quaternion (w,x,y,z)."""
        return Isometry3d.Identity() * Translation3d(*xyz) * Quaterniond(*quat)
