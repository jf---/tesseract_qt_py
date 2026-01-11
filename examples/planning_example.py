#!/usr/bin/env python3
"""Example demonstrating motion planning with high-level API."""

from pathlib import Path
import sys
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from tesseract_robotics.planning import Robot, Pose, TaskComposer
from core.planning import PlanningHelper


def main():
    """Run planning example."""
    # Load robot from tesseract_support
    robot = Robot.from_tesseract_support("abb_irb2400")

    # Set initial state
    joint_names = robot.get_joint_names("manipulator")
    robot.set_joints(np.ones(6) * 0.1, joint_names=joint_names)

    # Create planner
    composer = TaskComposer.from_config()
    planner = PlanningHelper(robot, composer)

    # Define target poses
    targets = [
        planner.make_pose((0.8, -0.3, 1.455), (0.70710678, 0, 0.70710678, 0)),
        planner.make_pose((0.8, 0.3, 1.455), (0.70710678, 0, 0.70710678, 0)),
    ]

    # Plan freespace motion
    print("Planning freespace motion...")
    result = planner.plan_freespace(targets, pipeline="FreespacePipeline")

    if result and result.successful:
        print(f"Planning successful! {len(result)} waypoints")
    else:
        msg = result.message if result else "No result"
        print(f"Planning failed: {msg}")


if __name__ == "__main__":
    main()
