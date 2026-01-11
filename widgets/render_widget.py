"""VTK render widget with Qt6 integration."""

from __future__ import annotations

import vtk
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QToolBar, QVBoxLayout, QWidget
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from core.camera_control import CameraController, ViewMode
from core.scene_manager import SceneManager


class RenderWidget(QWidget):
    """3D viewport widget using VTK."""

    linkClicked = Signal(str)  # Emitted when a link is clicked
    linkHovered = Signal(str)  # Emitted when mouse hovers over link

    def __init__(self, parent=None):
        super().__init__(parent)

        self._setup_ui()
        self._setup_vtk()
        self._setup_scene_helpers()

    def _setup_ui(self):
        """Setup widget layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        self.toolbar = QToolBar()
        self.toolbar.setMovable(False)

        # View menu
        view_menu = QMenu("View", self)

        self.action_reset = QAction("Reset View", self)
        self.action_reset.triggered.connect(self._on_reset_view)
        view_menu.addAction(self.action_reset)

        self.action_fit = QAction("Fit View", self)
        self.action_fit.triggered.connect(self._on_reset_view)
        view_menu.addAction(self.action_fit)

        view_menu.addSeparator()

        self.action_front = QAction("Front", self)
        self.action_front.triggered.connect(lambda: self.camera_ctrl.set_view_front())
        view_menu.addAction(self.action_front)

        self.action_back = QAction("Back", self)
        self.action_back.triggered.connect(lambda: self.camera_ctrl.set_view_back())
        view_menu.addAction(self.action_back)

        self.action_left = QAction("Left", self)
        self.action_left.triggered.connect(lambda: self.camera_ctrl.set_view_left())
        view_menu.addAction(self.action_left)

        self.action_right = QAction("Right", self)
        self.action_right.triggered.connect(lambda: self.camera_ctrl.set_view_right())
        view_menu.addAction(self.action_right)

        self.action_top = QAction("Top", self)
        self.action_top.triggered.connect(lambda: self.camera_ctrl.set_view_top())
        view_menu.addAction(self.action_top)

        self.action_bottom = QAction("Bottom", self)
        self.action_bottom.triggered.connect(lambda: self.camera_ctrl.set_view_bottom())
        view_menu.addAction(self.action_bottom)

        self.action_iso = QAction("Isometric", self)
        self.action_iso.triggered.connect(lambda: self.camera_ctrl.set_view_isometric())
        view_menu.addAction(self.action_iso)

        view_menu.addSeparator()

        self.action_ortho = QAction("Orthographic", self)
        self.action_ortho.setCheckable(True)
        self.action_ortho.triggered.connect(self._on_toggle_ortho)
        view_menu.addAction(self.action_ortho)

        # Add menu to toolbar
        view_button = self.toolbar.addAction("View")
        view_button.setMenu(view_menu)

        # Toggle buttons
        self.action_grid = QAction("Grid", self)
        self.action_grid.setCheckable(True)
        self.action_grid.setChecked(True)
        self.action_grid.triggered.connect(self._on_toggle_grid)
        self.toolbar.addAction(self.action_grid)

        self.action_axes = QAction("Axes", self)
        self.action_axes.setCheckable(True)
        self.action_axes.setChecked(True)
        self.action_axes.triggered.connect(self._on_toggle_axes)
        self.toolbar.addAction(self.action_axes)

        self.toolbar.addSeparator()

        # Frame visualization
        self.action_frames = QAction("Frames", self)
        self.action_frames.setCheckable(True)
        self.action_frames.triggered.connect(self._on_toggle_frames)
        self.toolbar.addAction(self.action_frames)

        self.action_tcp = QAction("TCP", self)
        self.action_tcp.setCheckable(True)
        self.action_tcp.triggered.connect(self._on_toggle_tcp)
        self.toolbar.addAction(self.action_tcp)

        layout.addWidget(self.toolbar)

        # VTK widget
        self.vtk_widget = QVTKRenderWindowInteractor(self)
        layout.addWidget(self.vtk_widget)

    def _setup_vtk(self):
        """Setup VTK renderer and scene."""
        # Create renderer
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(0.15, 0.15, 0.18)
        self.renderer.SetBackground2(0.3, 0.3, 0.35)
        self.renderer.GradientBackgroundOn()

        # Add to render window
        self.vtk_widget.GetRenderWindow().AddRenderer(self.renderer)

        # Create scene manager
        self.scene = SceneManager(self.renderer)

        # Create camera controller
        self.camera_ctrl = CameraController(self.renderer)

        # Setup interactor style (we handle camera ourselves)
        style = vtk.vtkInteractorStyleTrackballCamera()
        self.vtk_widget.SetInteractorStyle(style)

        # Override mouse events for our camera controller
        self.vtk_widget.mousePressEvent = self._on_mouse_press
        self.vtk_widget.mouseMoveEvent = self._on_mouse_move
        self.vtk_widget.wheelEvent = self._on_wheel

        # Picker for link selection
        self.picker = vtk.vtkCellPicker()
        self.picker.SetTolerance(0.005)

        # Initialize
        self.vtk_widget.Initialize()
        self.vtk_widget.Start()

    def _setup_scene_helpers(self):
        """Add grid and axes helpers."""
        # Ground grid
        self.grid_actor = self._create_grid()
        self.renderer.AddActor(self.grid_actor)

        # Axes widget
        self.axes_widget = vtk.vtkOrientationMarkerWidget()
        axes = vtk.vtkAxesActor()
        axes.SetShaftTypeToCylinder()
        axes.SetXAxisLabelText("X")
        axes.SetYAxisLabelText("Y")
        axes.SetZAxisLabelText("Z")
        self.axes_widget.SetOrientationMarker(axes)
        self.axes_widget.SetInteractor(self.vtk_widget)
        self.axes_widget.SetViewport(0.0, 0.0, 0.15, 0.15)
        self.axes_widget.EnabledOn()
        self.axes_widget.InteractiveOff()

    def _create_grid(self, size: float = 10.0, divisions: int = 20) -> vtk.vtkActor:
        """Create ground plane grid."""
        points = vtk.vtkPoints()
        lines = vtk.vtkCellArray()

        half = size / 2
        step = size / divisions

        # Create grid lines
        for i in range(divisions + 1):
            pos = -half + i * step

            # Line along X
            p1 = points.InsertNextPoint(-half, pos, 0)
            p2 = points.InsertNextPoint(half, pos, 0)
            line = vtk.vtkLine()
            line.GetPointIds().SetId(0, p1)
            line.GetPointIds().SetId(1, p2)
            lines.InsertNextCell(line)

            # Line along Y
            p1 = points.InsertNextPoint(pos, -half, 0)
            p2 = points.InsertNextPoint(pos, half, 0)
            line = vtk.vtkLine()
            line.GetPointIds().SetId(0, p1)
            line.GetPointIds().SetId(1, p2)
            lines.InsertNextCell(line)

        polydata = vtk.vtkPolyData()
        polydata.SetPoints(points)
        polydata.SetLines(lines)

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(polydata)

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(0.4, 0.4, 0.4)
        actor.GetProperty().SetLineWidth(1)

        return actor

    def load_environment(self, env):
        """Load tesseract environment."""
        self.scene.load_environment(env)
        # Focus camera on robot bounds only (not grid)
        bounds = self.scene.get_robot_bounds()
        if bounds:
            self.camera_ctrl.fit_to_bounds(bounds)
        else:
            self.camera_ctrl.reset_view()

    def update_joint_values(self, joint_values: dict[str, float]):
        """Update from joint values."""
        self.scene.update_joint_values(joint_values)

    def _on_mouse_press(self, event):
        """Handle mouse press."""
        self.camera_ctrl.on_mouse_press(event)

        # Check for link picking on left click without modifier
        if event.button() == Qt.MouseButton.LeftButton:
            if not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                self._pick_link(event.pos())

    def _on_mouse_move(self, event):
        """Handle mouse move."""
        if event.buttons():
            self.camera_ctrl.on_mouse_move(event)

    def _on_wheel(self, event):
        """Handle wheel."""
        self.camera_ctrl.on_wheel(event)

    def _pick_link(self, pos):
        """Pick link at screen position."""
        x, y = pos.x(), self.vtk_widget.height() - pos.y()

        self.picker.Pick(x, y, 0, self.renderer)
        actor = self.picker.GetActor()

        if actor:
            # Find which link this actor belongs to
            for key, a in self.scene.actors.items():
                if a == actor:
                    link_name = key.split("/")[0]
                    self.linkClicked.emit(link_name)
                    return

    def _on_reset_view(self):
        """Reset camera view to fit robot only (excludes grid)."""
        # Temporarily hide grid/workspace to exclude from bounds
        grid_vis = self.grid_actor.GetVisibility()
        self.grid_actor.SetVisibility(False)
        ws_actor = getattr(self.scene, "workspace_actor", None)
        ws_vis = ws_actor.GetVisibility() if ws_actor else False
        if ws_actor:
            ws_actor.SetVisibility(False)

        self.camera_ctrl.reset_view()

        # Restore visibility
        self.grid_actor.SetVisibility(grid_vis)
        if ws_actor:
            ws_actor.SetVisibility(ws_vis)

    def _on_toggle_ortho(self, checked: bool):
        """Toggle orthographic projection."""
        self.camera_ctrl.mode = ViewMode.ORTHO if checked else ViewMode.ORBIT

    def _on_toggle_grid(self, checked: bool):
        """Toggle grid visibility."""
        self.grid_actor.SetVisibility(checked)
        self.vtk_widget.GetRenderWindow().Render()

    def _on_toggle_axes(self, checked: bool):
        """Toggle axes widget."""
        if checked:
            self.axes_widget.EnabledOn()
        else:
            self.axes_widget.EnabledOff()
        self.vtk_widget.GetRenderWindow().Render()

    def _on_toggle_frames(self, checked: bool):
        """Toggle all link frames."""
        for link_name in self.scene.link_actors.keys():
            self.scene.show_frame(link_name, checked)
        self.vtk_widget.GetRenderWindow().Render()

    def _on_toggle_tcp(self, checked: bool):
        """Toggle TCP frame."""
        self.scene.show_tcp_frame(checked)
        self.vtk_widget.GetRenderWindow().Render()

    def set_frame_size(self, size: float):
        """Set coordinate frame size."""
        self.scene.set_frame_size(size)
        self.vtk_widget.GetRenderWindow().Render()

    def set_tcp_link(self, link_name: str | None):
        """Set TCP link."""
        self.scene.set_tcp_link(link_name)

    def render(self):
        """Force render."""
        self.vtk_widget.GetRenderWindow().Render()

    def resizeEvent(self, event):
        """Handle resize to trigger VTK redraw."""
        super().resizeEvent(event)
        if hasattr(self, "vtk_widget"):
            self.vtk_widget.GetRenderWindow().Render()

    def save_screenshot(self, filepath: str):
        """Save current view as PNG.

        Args:
            filepath: Output PNG path
        """
        from pathlib import Path

        w2i = vtk.vtkWindowToImageFilter()
        w2i.SetInput(self.vtk_widget.GetRenderWindow())
        w2i.SetScale(1)
        w2i.SetInputBufferTypeToRGB()
        w2i.ReadFrontBufferOff()
        w2i.Update()

        writer = vtk.vtkPNGWriter()
        writer.SetFileName(str(Path(filepath)))
        writer.SetInputConnection(w2i.GetOutputPort())
        writer.Write()

    def export_scene(self, filepath: str):
        """Export scene as STL or OBJ.

        Args:
            filepath: Output file path (.stl or .obj)
        """
        from pathlib import Path

        path = Path(filepath)
        suffix = path.suffix.lower()

        # Collect all visible geometry
        append = vtk.vtkAppendPolyData()
        for actor in self.scene.actors.values():
            if not actor.GetVisibility():
                continue

            mapper = actor.GetMapper()
            if not mapper:
                continue

            # Get polydata from mapper
            mapper.Update()
            polydata = mapper.GetInput()
            if not polydata:
                continue

            # Apply actor transform
            transform_filter = vtk.vtkTransformPolyDataFilter()
            transform_filter.SetInputData(polydata)

            # Combine user transform and actor transform
            combined = vtk.vtkTransform()
            if actor.GetUserTransform():
                combined.Concatenate(actor.GetUserTransform())
            if actor.GetMatrix():
                combined.Concatenate(actor.GetMatrix())

            transform_filter.SetTransform(combined)
            transform_filter.Update()
            append.AddInputData(transform_filter.GetOutput())

        append.Update()
        merged = append.GetOutput()

        if suffix == ".stl":
            writer = vtk.vtkSTLWriter()
        elif suffix == ".obj":
            writer = vtk.vtkOBJWriter()
        else:
            raise ValueError(f"Unsupported format: {suffix}")

        writer.SetFileName(str(path))
        writer.SetInputData(merged)
        writer.Write()
