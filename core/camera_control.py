"""Camera controllers for VTK viewport."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QMouseEvent, QWheelEvent

if TYPE_CHECKING:
    from vtkmodules.vtkRenderingCore import vtkRenderer


class ViewMode(Enum):
    ORBIT = "orbit"
    ORTHO = "ortho"


class CameraController:
    """Interactive camera controller with orbit/pan/zoom."""

    def __init__(self, renderer: vtkRenderer):
        self.renderer = renderer
        self.camera = renderer.GetActiveCamera()
        self._last_pos = QPoint()
        self._mode = ViewMode.ORBIT

        # Sensitivity settings
        self.orbit_speed = 0.5
        self.pan_speed = 0.01
        self.zoom_speed = 0.001

    @property
    def mode(self) -> ViewMode:
        return self._mode

    @mode.setter
    def mode(self, value: ViewMode):
        self._mode = value
        if value == ViewMode.ORTHO:
            self.camera.ParallelProjectionOn()
        else:
            self.camera.ParallelProjectionOff()
        self._render()

    def on_mouse_press(self, event: QMouseEvent):
        """Handle mouse press."""
        self._last_pos = event.pos()

    def on_mouse_move(self, event: QMouseEvent):
        """Handle mouse drag for camera control."""
        pos = event.pos()
        dx = pos.x() - self._last_pos.x()
        dy = pos.y() - self._last_pos.y()

        buttons = event.buttons()
        modifiers = event.modifiers()

        if buttons & Qt.MouseButton.LeftButton:
            if modifiers & Qt.KeyboardModifier.ShiftModifier:
                # Shift+Left = pan
                self._pan(dx, dy)
            else:
                # Left = orbit
                self._orbit(dx, dy)

        elif buttons & Qt.MouseButton.MiddleButton:
            # Middle = pan
            self._pan(dx, dy)

        elif buttons & Qt.MouseButton.RightButton:
            # Right = zoom
            self._zoom(dy)

        self._last_pos = pos
        self._render()

    def on_wheel(self, event: QWheelEvent):
        """Handle mouse wheel for zoom."""
        delta = event.angleDelta().y()
        factor = 1.0 + delta * self.zoom_speed
        self.camera.Zoom(factor)
        self._render()

    def _orbit(self, dx: int, dy: int):
        """Orbit camera around focal point."""
        self.camera.Azimuth(-dx * self.orbit_speed)
        self.camera.Elevation(-dy * self.orbit_speed)
        self.camera.OrthogonalizeViewUp()

    def _pan(self, dx: int, dy: int):
        """Pan camera in view plane."""
        # Get camera vectors
        fp = list(self.camera.GetFocalPoint())
        pos = list(self.camera.GetPosition())
        up = list(self.camera.GetViewUp())

        # Calculate right vector
        view = [fp[i] - pos[i] for i in range(3)]
        dist = sum(v * v for v in view) ** 0.5

        # Normalize
        if dist > 0:
            view = [v / dist for v in view]

        # Right = view x up
        right = [
            view[1] * up[2] - view[2] * up[1],
            view[2] * up[0] - view[0] * up[2],
            view[0] * up[1] - view[1] * up[0],
        ]

        # Scale by distance for consistent feel
        scale = dist * self.pan_speed

        # Move camera and focal point
        for i in range(3):
            delta = (-dx * right[i] + dy * up[i]) * scale
            fp[i] += delta
            pos[i] += delta

        self.camera.SetFocalPoint(*fp)
        self.camera.SetPosition(*pos)

    def _zoom(self, dy: int):
        """Zoom camera."""
        factor = 1.0 + dy * self.zoom_speed * 10
        self.camera.Zoom(factor)

    def reset_view(self):
        """Reset camera to fit all actors."""
        self.renderer.ResetCamera()
        self._render()

    def fit_to_bounds(self, bounds: tuple[float, float, float, float, float, float]):
        """Fit camera to specific bounds (xmin,xmax,ymin,ymax,zmin,zmax)."""
        xmin, xmax, ymin, ymax, zmin, zmax = bounds
        cx, cy, cz = (xmin + xmax) / 2, (ymin + ymax) / 2, (zmin + zmax) / 2

        # Compute diagonal distance
        import math

        diag = math.sqrt((xmax - xmin) ** 2 + (ymax - ymin) ** 2 + (zmax - zmin) ** 2)
        dist = diag * 1.5  # Add some margin

        # Set isometric view focused on bounds center
        self.camera.SetFocalPoint(cx, cy, cz)
        self.camera.SetPosition(cx + dist * 0.5, cy - dist * 0.7, cz + dist * 0.5)
        self.camera.SetViewUp(0, 0, 1)
        self.renderer.ResetCameraClippingRange()
        self._render()

    def set_view_front(self):
        """Set front view (looking at -Y)."""
        fp = self.camera.GetFocalPoint()
        dist = self.camera.GetDistance()
        self.camera.SetPosition(fp[0], fp[1] + dist, fp[2])
        self.camera.SetViewUp(0, 0, 1)
        self._render()

    def set_view_back(self):
        """Set back view (looking at +Y)."""
        fp = self.camera.GetFocalPoint()
        dist = self.camera.GetDistance()
        self.camera.SetPosition(fp[0], fp[1] - dist, fp[2])
        self.camera.SetViewUp(0, 0, 1)
        self._render()

    def set_view_left(self):
        """Set left view (looking at +X)."""
        fp = self.camera.GetFocalPoint()
        dist = self.camera.GetDistance()
        self.camera.SetPosition(fp[0] - dist, fp[1], fp[2])
        self.camera.SetViewUp(0, 0, 1)
        self._render()

    def set_view_right(self):
        """Set right view (looking at -X)."""
        fp = self.camera.GetFocalPoint()
        dist = self.camera.GetDistance()
        self.camera.SetPosition(fp[0] + dist, fp[1], fp[2])
        self.camera.SetViewUp(0, 0, 1)
        self._render()

    def set_view_top(self):
        """Set top view (looking at -Z)."""
        fp = self.camera.GetFocalPoint()
        dist = self.camera.GetDistance()
        self.camera.SetPosition(fp[0], fp[1], fp[2] + dist)
        self.camera.SetViewUp(0, 1, 0)
        self._render()

    def set_view_bottom(self):
        """Set bottom view (looking at +Z)."""
        fp = self.camera.GetFocalPoint()
        dist = self.camera.GetDistance()
        self.camera.SetPosition(fp[0], fp[1], fp[2] - dist)
        self.camera.SetViewUp(0, -1, 0)
        self._render()

    def set_view_isometric(self):
        """Set isometric view."""
        fp = self.camera.GetFocalPoint()
        dist = self.camera.GetDistance()
        d = dist / (3**0.5)
        self.camera.SetPosition(fp[0] + d, fp[1] + d, fp[2] + d)
        self.camera.SetViewUp(0, 0, 1)
        self._render()

    def _render(self):
        """Trigger render."""
        if self.renderer.GetRenderWindow():
            self.renderer.GetRenderWindow().Render()
