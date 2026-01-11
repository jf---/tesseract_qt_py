#!/usr/bin/env python
"""Demo UI without tesseract - just shows widgets with VTK primitives."""

import os
import sys

# Force native Cocoa on macOS - NO X11
if sys.platform == "darwin":
    os.environ.pop("DISPLAY", None)
    os.environ["QT_QPA_PLATFORM"] = "cocoa"

# CRITICAL: Force QOpenGLWidget base for VTK+Qt on macOS
import vtkmodules.qt

vtkmodules.qt.QVTKRWIBase = "QOpenGLWidget"

import numpy as np
import vtkmodules.vtkRenderingOpenGL2  # noqa: F401
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QDockWidget
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkFiltersSources import (
    vtkConeSource,
    vtkCubeSource,
    vtkCylinderSource,
    vtkSphereSource,
)
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera
from vtkmodules.vtkRenderingAnnotation import vtkAxesActor
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkPolyDataMapper,
    vtkRenderer,
)

from widgets.acm_editor import ACMEditorWidget
from widgets.cartesian_editor import CartesianEditorWidget
from widgets.contact_compute_widget import ContactComputeWidget
from widgets.environment_dialog import LoadEnvironmentDialog
from widgets.manipulation_widget import ManipulationWidget
from widgets.studio_layout import StudioMainWindow


def create_actor(source, color, position=(0, 0, 0)):
    """Create a colored actor from a VTK source."""
    mapper = vtkPolyDataMapper()
    mapper.SetInputConnection(source.GetOutputPort())
    actor = vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(*color)
    actor.SetPosition(*position)
    return actor


def create_ground_grid(size=2.0, spacing=0.2, color=(0.4, 0.4, 0.4)):
    """Create a ground grid on XY plane at z=0."""
    from vtkmodules.vtkCommonCore import vtkPoints
    from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkPolyData

    points = vtkPoints()
    lines = vtkCellArray()

    # Calculate grid extent
    half_size = size / 2
    num_divisions = int(size / spacing) + 1

    # X-direction lines
    for y in np.linspace(-half_size, half_size, num_divisions):
        p1_idx = points.InsertNextPoint(-half_size, y, 0)
        p2_idx = points.InsertNextPoint(half_size, y, 0)
        line = [2, p1_idx, p2_idx]
        lines.InsertNextCell(len(line), line)

    # Y-direction lines
    for x in np.linspace(-half_size, half_size, num_divisions):
        p1_idx = points.InsertNextPoint(x, -half_size, 0)
        p2_idx = points.InsertNextPoint(x, half_size, 0)
        line = [2, p1_idx, p2_idx]
        lines.InsertNextCell(len(line), line)

    # Create polydata
    poly_data = vtkPolyData()
    poly_data.SetPoints(points)
    poly_data.SetLines(lines)

    # Create mapper and actor
    mapper = vtkPolyDataMapper()
    mapper.SetInputData(poly_data)
    actor = vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(*color)

    return actor


def build_scene(renderer):
    """Add primitives to mimic robot links."""
    # Base - large box
    base = vtkCubeSource()
    base.SetXLength(0.4)
    base.SetYLength(0.4)
    base.SetZLength(0.2)
    renderer.AddActor(create_actor(base, (0.7, 0.35, 0.16), (0, 0, 0.1)))

    # Link 1 - cylinder
    link1 = vtkCylinderSource()
    link1.SetRadius(0.1)
    link1.SetHeight(0.5)
    link1.SetResolution(32)
    a1 = create_actor(link1, (0.7, 0.35, 0.16), (0, 0, 0.45))
    a1.RotateX(90)
    renderer.AddActor(a1)

    # Link 2 - longer cylinder
    link2 = vtkCylinderSource()
    link2.SetRadius(0.08)
    link2.SetHeight(0.6)
    link2.SetResolution(32)
    a2 = create_actor(link2, (0.7, 0.35, 0.16), (0, 0.3, 0.7))
    a2.RotateX(90)
    a2.RotateZ(30)
    renderer.AddActor(a2)

    # Joint spheres
    for pos in [(0, 0, 0.2), (0, 0, 0.7), (0, 0.3, 1.0)]:
        sphere = vtkSphereSource()
        sphere.SetRadius(0.06)
        sphere.SetPhiResolution(16)
        sphere.SetThetaResolution(16)
        renderer.AddActor(create_actor(sphere, (0.3, 0.3, 0.3), pos))

    # End effector - cone
    cone = vtkConeSource()
    cone.SetRadius(0.05)
    cone.SetHeight(0.15)
    cone.SetResolution(32)
    a_cone = create_actor(cone, (0.2, 0.2, 0.2), (0.1, 0.5, 1.1))
    a_cone.RotateZ(-60)
    renderer.AddActor(a_cone)

    # Axes
    axes = vtkAxesActor()
    axes.SetTotalLength(0.3, 0.3, 0.3)
    renderer.AddActor(axes)

    # Ground grid
    grid = create_ground_grid(size=2.0, spacing=0.2, color=(0.4, 0.4, 0.4))
    renderer.AddActor(grid)

    renderer.SetBackground(0.2, 0.25, 0.3)
    renderer.ResetCamera()
    renderer.GetActiveCamera().Azimuth(30)
    renderer.GetActiveCamera().Elevation(20)


def main():
    app = QApplication(sys.argv)

    # Main window
    win = StudioMainWindow()
    win.setWindowTitle("tesseract_qt_py - Demo UI")

    # VTK widget as central
    vtk_widget = QVTKRenderWindowInteractor(win)
    renderer = vtkRenderer()
    vtk_widget.GetRenderWindow().AddRenderer(renderer)
    vtk_widget.GetRenderWindow().SetWindowName("VTK")

    style = vtkInteractorStyleTrackballCamera()
    vtk_widget.SetInteractorStyle(style)

    build_scene(renderer)
    win.setCentralWidget(vtk_widget)

    # Add dock widgets
    def add_dock(title, widget, area=Qt.DockWidgetArea.RightDockWidgetArea):
        dock = QDockWidget(title, win)
        dock.setWidget(widget)
        win.addDockWidget(area, dock)
        return dock

    add_dock("Manipulation", ManipulationWidget())
    add_dock("Cartesian", CartesianEditorWidget())
    add_dock("ACM Editor", ACMEditorWidget(), Qt.DockWidgetArea.LeftDockWidgetArea)
    add_dock("Contact", ContactComputeWidget(), Qt.DockWidgetArea.LeftDockWidgetArea)

    win.action_load_config.triggered.connect(lambda: LoadEnvironmentDialog(win).exec())

    win.resize(1400, 900)
    win.show()

    # Initialize VTK AFTER window is shown (macOS requirement)
    vtk_widget.Initialize()
    vtk_widget.Start()

    # Force window to front and render
    win.raise_()
    win.activateWindow()
    vtk_widget.GetRenderWindow().Render()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
