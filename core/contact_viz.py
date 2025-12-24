"""Contact/collision results visualization."""
from __future__ import annotations

import numpy as np
import vtk


class ContactVisualizer:
    """Visualize collision/contact results from tesseract."""

    def __init__(self, renderer: vtk.vtkRenderer):
        self.renderer = renderer
        self.contact_actors: list[vtk.vtkActor] = []
        self.normal_actors: list[vtk.vtkActor] = []
        self.highlighted_links: dict[str, tuple] = {}  # link_name -> (actors, original_colors)

    def clear(self):
        """Clear all contact visualization."""
        for actor in self.contact_actors + self.normal_actors:
            self.renderer.RemoveActor(actor)
        self.contact_actors.clear()
        self.normal_actors.clear()

        # Restore highlighted links
        for actors, colors in self.highlighted_links.values():
            for actor, color in zip(actors, colors):
                actor.GetProperty().SetColor(*color)
                actor.GetProperty().SetAmbient(0.0)
        self.highlighted_links.clear()

    def visualize_contacts(self, contact_results, link_actors: dict[str, list[vtk.vtkActor]] = None):
        """
        Visualize contact results.

        Args:
            contact_results: ContactResultVector from tesseract collision checking
            link_actors: Dict mapping link names to their actors for highlighting
        """
        self.clear()

        for contact in contact_results:
            # Contact points as spheres
            if hasattr(contact, 'nearest_points') and len(contact.nearest_points) >= 2:
                for pt in contact.nearest_points[:2]:
                    self._add_contact_point(pt)

            # Contact normal as arrow
            if hasattr(contact, 'nearest_points') and hasattr(contact, 'normal'):
                if len(contact.nearest_points) >= 1:
                    self._add_contact_normal(contact.nearest_points[0], contact.normal)

            # Highlight colliding links
            if link_actors and hasattr(contact, 'link_names') and len(contact.link_names) >= 2:
                for link_name in contact.link_names[:2]:
                    if link_name not in self.highlighted_links and link_name in link_actors:
                        self._highlight_link(link_name, link_actors[link_name])

    def _add_contact_point(self, point, radius: float = 0.01, color: tuple = (1.0, 0.2, 0.2)):
        """Add contact point marker (small sphere)."""
        sphere = vtk.vtkSphereSource()
        sphere.SetCenter(float(point[0]), float(point[1]), float(point[2]))
        sphere.SetRadius(radius)
        sphere.SetPhiResolution(8)
        sphere.SetThetaResolution(8)

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(sphere.GetOutputPort())

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(*color)

        self.renderer.AddActor(actor)
        self.contact_actors.append(actor)

    def _add_contact_normal(self, point, normal, scale: float = 0.1, color: tuple = (0.2, 1.0, 0.2)):
        """Add contact normal as arrow."""
        # Arrow source
        arrow = vtk.vtkArrowSource()
        arrow.SetTipResolution(8)
        arrow.SetShaftResolution(8)

        # Transform to position and orient
        transform = vtk.vtkTransform()
        transform.Translate(float(point[0]), float(point[1]), float(point[2]))

        # Compute rotation from default arrow direction (X-axis) to normal
        norm = np.array([float(normal[0]), float(normal[1]), float(normal[2])])
        norm_len = np.linalg.norm(norm)
        if norm_len > 1e-6:
            norm = norm / norm_len
            default_dir = np.array([1.0, 0.0, 0.0])

            # Rotation axis
            axis = np.cross(default_dir, norm)
            axis_len = np.linalg.norm(axis)

            if axis_len > 1e-6:
                axis = axis / axis_len
                angle = np.arccos(np.clip(np.dot(default_dir, norm), -1.0, 1.0))
                transform.RotateWXYZ(np.degrees(angle), axis[0], axis[1], axis[2])

        transform.Scale(scale, scale, scale)

        transformer = vtk.vtkTransformPolyDataFilter()
        transformer.SetTransform(transform)
        transformer.SetInputConnection(arrow.GetOutputPort())

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(transformer.GetOutputPort())

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(*color)

        self.renderer.AddActor(actor)
        self.normal_actors.append(actor)

    def _highlight_link(self, link_name: str, actors: list[vtk.vtkActor], color: tuple = (1.0, 0.3, 0.0)):
        """Highlight link in collision."""
        # Store original colors
        original_colors = []
        for actor in actors:
            original_colors.append(actor.GetProperty().GetColor())
            actor.GetProperty().SetColor(*color)
            actor.GetProperty().SetAmbient(0.5)

        self.highlighted_links[link_name] = (actors, original_colors)
