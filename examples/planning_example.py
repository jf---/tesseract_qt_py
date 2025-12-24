#!/usr/bin/env python3
"""Example demonstrating motion planning with PlanningHelper."""
from pathlib import Path
import sys
import numpy as np

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tesseract_robotics.tesseract_environment import Environment
from tesseract_robotics.tesseract_common import GeneralResourceLocator, FilesystemPath

from core.planning import PlanningHelper


def main():
    """Run planning example."""
    # Setup environment
    locator = GeneralResourceLocator()
    urdf_url = "package://tesseract_support/urdf/abb_irb2400.urdf"
    srdf_url = "package://tesseract_support/urdf/abb_irb2400.srdf"
    urdf_path = FilesystemPath(locator.locateResource(urdf_url).getFilePath())
    srdf_path = FilesystemPath(locator.locateResource(srdf_url).getFilePath())

    env = Environment()
    if not env.init(urdf_path, srdf_path, locator):
        raise RuntimeError("Failed to initialize environment")

    # Set initial state
    joint_names = [f"joint_{i+1}" for i in range(6)]
    env.setState(joint_names, np.ones(6) * 0.1)

    # Create planner
    config_path = Path("/path/to/task_composer_plugins.yaml")
    planner = PlanningHelper(env, config_path)

    # Define target poses
    targets = [
        planner.make_pose((0.8, -0.3, 1.455), (0.70710678, 0, 0.70710678, 0)),
        planner.make_pose((0.8, 0.3, 1.455), (0.70710678, 0, 0.70710678, 0)),
    ]

    # Plan freespace motion
    result = planner.plan_freespace(targets)

    if result:
        trajectory = planner.extract_joint_trajectory(result)
        print(f"Planned {len(trajectory)} waypoints:")
        for i, (positions, timestamp) in enumerate(trajectory):
            print(f"  {i}: joints={positions}, time={timestamp:.3f}")
    else:
        print("Planning failed")


if __name__ == "__main__":
    main()
