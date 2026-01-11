#!/usr/bin/env python
"""Test imports."""

import sys

sys.path.insert(0, ".")

print("Testing core imports...")
from core.scene_manager import SceneManager
from core.camera_control import CameraController

print("  Core OK")

print("Testing widget imports...")
from widgets.joint_slider import JointSliderWidget
from widgets.scene_tree import SceneTreeWidget

print("  Widgets OK")

print("Testing render widget...")
from widgets.render_widget import RenderWidget

print("  Render OK")

print("Testing app...")
from app import TesseractViewer

print("  App OK")

print("\nAll imports successful!")
