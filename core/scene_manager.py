"""VTK scene manager for Tesseract environments."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import vtk

from tesseract_robotics import tesseract_common
from tesseract_robotics import tesseract_geometry as tg
from tesseract_robotics import tesseract_scene_graph as sg

from .contact_viz import ContactVisualizer


class SceneManager:
    """Manages VTK scene from Tesseract environment."""

    def __init__(self, renderer: vtk.vtkRenderer):
        self.renderer = renderer
        self.actors: dict[str, vtk.vtkActor] = {}
        self.link_actors: dict[str, list[vtk.vtkActor]] = {}
        self.path_actors: dict[str, list[vtk.vtkActor]] = {}
        self.frame_actors: dict[str, vtk.vtkAxesActor] = {}
        self._visual_origins: dict = {}  # Visual origin transforms
        self.frame_size: float = 0.1
        self._env = None
        self._tcp_link: str | None = None
        self.workspace_actor: vtk.vtkActor | None = None
        self.contact_viz = ContactVisualizer(renderer)
        self._fk_actors: dict[str, list[vtk.vtkActor]] = {}

    def clear(self):
        """Remove all actors from scene."""
        for actor in self.actors.values():
            self.renderer.RemoveActor(actor)
        self.actors.clear()
        self.link_actors.clear()
        self._visual_origins.clear()
        self._clear_paths()
        self._clear_frames()
        self._clear_workspace()
        self.contact_viz.clear()
        self.clear_fk_viz()

    def load_environment(self, env):
        """Load tesseract environment into VTK scene."""
        self.clear()
        self._env = env
        self._visual_origins = {}  # Store visual origins for transform combining

        scene_graph = env.getSceneGraph()

        for link in scene_graph.getLinks():
            link_name = link.getName()
            self.link_actors[link_name] = []

            for i, visual in enumerate(link.visual):
                actor = self._create_actor_from_geometry(visual.geometry)
                if actor is None:
                    continue

                # Store visual origin for later transform combining
                key = f"{link_name}/visual_{i}"
                self._visual_origins[key] = visual.origin

                # Set material color (API returns numpy array [r,g,b,a] in 0.7.1+)
                if visual.material is not None and visual.material.color is not None:
                    c = visual.material.color
                    if hasattr(c, 'r'):  # Old API
                        actor.GetProperty().SetColor(c.r, c.g, c.b)
                        if c.a < 1.0:
                            actor.GetProperty().SetOpacity(c.a)
                    else:  # New API - numpy array [r,g,b,a]
                        actor.GetProperty().SetColor(c[0], c[1], c[2])
                        if len(c) > 3 and c[3] < 1.0:
                            actor.GetProperty().SetOpacity(c[3])
                else:
                    # Default gray
                    actor.GetProperty().SetColor(0.7, 0.7, 0.7)

                key = f"{link_name}/visual_{i}"
                self.actors[key] = actor
                self.link_actors[link_name].append(actor)
                self.renderer.AddActor(actor)

        # Get initial state and apply transforms
        self.update_from_state(env.getState())

    def update_from_state(self, state):
        """Update transforms from environment state."""
        for link_name, actors in self.link_actors.items():
            try:
                link_transform = state.link_transforms[link_name]

                for i, actor in enumerate(actors):
                    key = f"{link_name}/visual_{i}"
                    visual_origin = self._visual_origins.get(key)

                    # Combine link transform with visual origin
                    if visual_origin is not None:
                        combined = link_transform * visual_origin
                        actor.SetUserTransform(self._isometry_to_vtk(combined))
                    else:
                        actor.SetUserTransform(self._isometry_to_vtk(link_transform))

                # Update frame if visible (frames don't have visual origin)
                if link_name in self.frame_actors:
                    self.frame_actors[link_name].SetUserTransform(self._isometry_to_vtk(link_transform))
            except (KeyError, AttributeError):
                pass

    def update_joint_values(self, joint_values: dict[str, float]):
        """Update scene from joint values."""
        if self._env is None:
            return

        # Set joint positions using dict overload
        try:
            self._env.setState(joint_values)
        except Exception as e:
            print(f"setState error: {e}")

        self.update_from_state(self._env.getState())
        rw = self.renderer.GetRenderWindow()
        if rw:
            rw.Render()

    def _create_actor_from_geometry(self, geometry) -> vtk.vtkActor | None:
        """Create VTK actor from tesseract geometry."""
        geom_type = geometry.getType()
        source = None

        GT = tg.GeometryType

        if geom_type == GT.SPHERE:
            source = vtk.vtkSphereSource()
            source.SetRadius(geometry.getRadius())
            source.SetPhiResolution(24)
            source.SetThetaResolution(24)

        elif geom_type == GT.CYLINDER:
            source = vtk.vtkCylinderSource()
            source.SetRadius(geometry.getRadius())
            source.SetHeight(geometry.getLength())
            source.SetResolution(24)
            # Rotate to match tesseract convention (Z-axis)
            transform = vtk.vtkTransform()
            transform.RotateX(90)
            transformer = vtk.vtkTransformPolyDataFilter()
            transformer.SetTransform(transform)
            transformer.SetInputConnection(source.GetOutputPort())
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(transformer.GetOutputPort())
            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            return actor

        elif geom_type == GT.CAPSULE:
            return self._create_capsule(geometry.getRadius(), geometry.getLength())

        elif geom_type == GT.CONE:
            source = vtk.vtkConeSource()
            source.SetRadius(geometry.getRadius())
            source.SetHeight(geometry.getLength())
            source.SetResolution(24)

        elif geom_type == GT.BOX:
            source = vtk.vtkCubeSource()
            dims = geometry.getDimensions()
            source.SetXLength(dims[0])
            source.SetYLength(dims[1])
            source.SetZLength(dims[2])

        elif geom_type in (GT.MESH, GT.CONVEX_MESH, GT.POLYGON_MESH):
            return self._create_mesh_actor(geometry)

        if source is None:
            return None

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(source.GetOutputPort())

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        return actor

    def _create_capsule(self, radius: float, length: float) -> vtk.vtkActor:
        """Create capsule geometry (cylinder + hemispheres)."""
        append = vtk.vtkAppendPolyData()

        # Cylinder body
        cylinder = vtk.vtkCylinderSource()
        cylinder.SetRadius(radius)
        cylinder.SetHeight(length)
        cylinder.SetResolution(24)
        cylinder.CappingOff()

        # Rotate to Z-axis
        transform = vtk.vtkTransform()
        transform.RotateX(90)
        cyl_transformer = vtk.vtkTransformPolyDataFilter()
        cyl_transformer.SetTransform(transform)
        cyl_transformer.SetInputConnection(cylinder.GetOutputPort())
        append.AddInputConnection(cyl_transformer.GetOutputPort())

        # Top hemisphere
        top_sphere = vtk.vtkSphereSource()
        top_sphere.SetRadius(radius)
        top_sphere.SetPhiResolution(24)
        top_sphere.SetThetaResolution(24)
        top_sphere.SetStartPhi(0)
        top_sphere.SetEndPhi(90)
        top_sphere.SetCenter(0, 0, length / 2)
        append.AddInputConnection(top_sphere.GetOutputPort())

        # Bottom hemisphere
        bot_sphere = vtk.vtkSphereSource()
        bot_sphere.SetRadius(radius)
        bot_sphere.SetPhiResolution(24)
        bot_sphere.SetThetaResolution(24)
        bot_sphere.SetStartPhi(90)
        bot_sphere.SetEndPhi(180)
        bot_sphere.SetCenter(0, 0, -length / 2)
        append.AddInputConnection(bot_sphere.GetOutputPort())

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(append.GetOutputPort())

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        return actor

    def _create_mesh_actor(self, geometry) -> vtk.vtkActor | None:
        """Create actor from mesh geometry."""
        try:
            # Try file path first
            uri = str(geometry.getFilePath()) if hasattr(geometry, 'getFilePath') else None
            scale = geometry.getScale() if hasattr(geometry, 'getScale') else None

            if uri and uri.strip():
                polydata = self._load_mesh_file(uri, scale)
                if polydata is not None:
                    mapper = vtk.vtkPolyDataMapper()
                    mapper.SetInputData(polydata)
                    actor = vtk.vtkActor()
                    actor.SetMapper(mapper)
                    return actor

            # Try getting mesh vertices/faces directly
            vertices = geometry.getVertices() if hasattr(geometry, 'getVertices') else None
            faces = geometry.getFaces() if hasattr(geometry, 'getFaces') else None

            if vertices is not None and len(vertices) > 0:
                polydata = self._vertices_faces_to_polydata(vertices, faces)
                if polydata is not None:
                    mapper = vtk.vtkPolyDataMapper()
                    mapper.SetInputData(polydata)
                    actor = vtk.vtkActor()
                    actor.SetMapper(mapper)
                    return actor

        except Exception as e:
            print(f"Failed to create mesh actor: {e}")

        return None

    def _vertices_faces_to_polydata(self, vertices, faces) -> vtk.vtkPolyData | None:
        """Convert vertices and faces to VTK polydata."""
        if len(vertices) == 0:
            return None

        points = vtk.vtkPoints()
        for v in vertices:
            points.InsertNextPoint(float(v[0]), float(v[1]), float(v[2]))

        polys = vtk.vtkCellArray()
        if faces is not None and len(faces) > 0:
            i = 0
            while i < len(faces):
                n = int(faces[i])
                if n >= 3:
                    poly = vtk.vtkPolygon()
                    poly.GetPointIds().SetNumberOfIds(n)
                    for j in range(n):
                        poly.GetPointIds().SetId(j, int(faces[i + 1 + j]))
                    polys.InsertNextCell(poly)
                i += n + 1

        polydata = vtk.vtkPolyData()
        polydata.SetPoints(points)
        polydata.SetPolys(polys)

        # Compute normals
        normals = vtk.vtkPolyDataNormals()
        normals.SetInputData(polydata)
        normals.ComputePointNormalsOn()
        normals.Update()

        return normals.GetOutput()

    def _load_mesh_file(self, uri: str, scale=None) -> vtk.vtkPolyData | None:
        """Load mesh from file."""
        path = Path(uri)
        if not path.exists():
            return None

        suffix = path.suffix.lower()
        reader = None

        if suffix == ".stl":
            reader = vtk.vtkSTLReader()
        elif suffix == ".obj":
            reader = vtk.vtkOBJReader()
        elif suffix == ".ply":
            reader = vtk.vtkPLYReader()

        if reader is None:
            return None

        reader.SetFileName(str(path))
        reader.Update()
        polydata = reader.GetOutput()

        if scale is not None:
            try:
                sx, sy, sz = float(scale[0]), float(scale[1]), float(scale[2])
                if (sx, sy, sz) != (1.0, 1.0, 1.0):
                    transform = vtk.vtkTransform()
                    transform.Scale(sx, sy, sz)
                    transformer = vtk.vtkTransformPolyDataFilter()
                    transformer.SetInputData(polydata)
                    transformer.SetTransform(transform)
                    transformer.Update()
                    polydata = transformer.GetOutput()
            except (TypeError, IndexError):
                pass

        return polydata

    def _isometry_to_vtk(self, isometry) -> vtk.vtkTransform:
        """Convert Eigen Isometry3d to vtkTransform."""
        t = vtk.vtkTransform()
        try:
            matrix = isometry.matrix()
            m = vtk.vtkMatrix4x4()
            for i in range(4):
                for j in range(4):
                    m.SetElement(i, j, float(matrix[i, j]))
            t.SetMatrix(m)
        except Exception:
            pass
        return t

    def set_link_visibility(self, link_name: str, visible: bool):
        """Set visibility of link actors."""
        if link_name in self.link_actors:
            for actor in self.link_actors[link_name]:
                actor.SetVisibility(visible)

    def highlight_link(self, link_name: str, highlight: bool = True):
        """Highlight link with color change."""
        if link_name in self.link_actors:
            for actor in self.link_actors[link_name]:
                if highlight:
                    actor.GetProperty().SetColor(1.0, 0.6, 0.0)
                    actor.GetProperty().SetAmbient(0.4)
                else:
                    actor.GetProperty().SetColor(0.7, 0.7, 0.7)
                    actor.GetProperty().SetAmbient(0.0)

    def add_tool_path(
        self,
        path_id: str,
        points: np.ndarray,
        color: tuple[float, float, float] = (1.0, 0.0, 0.0),
        line_width: float = 2.0,
        show_waypoints: bool = True,
        waypoint_radius: float = 0.01,
    ):
        """Add tool path visualization.

        Args:
            path_id: Unique identifier for path
            points: Nx3 array of waypoint coordinates
            color: RGB color tuple (0-1)
            line_width: Width of path line
            show_waypoints: Whether to show waypoint spheres
            waypoint_radius: Radius of waypoint spheres
        """
        if path_id in self.path_actors:
            self.clear_path(path_id)

        self.path_actors[path_id] = []

        if len(points) < 2:
            return

        # Create polyline for path
        vtk_points = vtk.vtkPoints()
        for pt in points:
            vtk_points.InsertNextPoint(float(pt[0]), float(pt[1]), float(pt[2]))

        lines = vtk.vtkCellArray()
        for i in range(len(points) - 1):
            line = vtk.vtkLine()
            line.GetPointIds().SetId(0, i)
            line.GetPointIds().SetId(1, i + 1)
            lines.InsertNextCell(line)

        polydata = vtk.vtkPolyData()
        polydata.SetPoints(vtk_points)
        polydata.SetLines(lines)

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(polydata)

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(*color)
        actor.GetProperty().SetLineWidth(line_width)

        self.renderer.AddActor(actor)
        self.path_actors[path_id].append(actor)

        # Add waypoint spheres
        if show_waypoints:
            for pt in points:
                sphere = vtk.vtkSphereSource()
                sphere.SetCenter(float(pt[0]), float(pt[1]), float(pt[2]))
                sphere.SetRadius(waypoint_radius)
                sphere.SetPhiResolution(16)
                sphere.SetThetaResolution(16)

                mapper = vtk.vtkPolyDataMapper()
                mapper.SetInputConnection(sphere.GetOutputPort())

                actor = vtk.vtkActor()
                actor.SetMapper(mapper)
                actor.GetProperty().SetColor(*color)

                self.renderer.AddActor(actor)
                self.path_actors[path_id].append(actor)

    def add_path_segment(
        self,
        path_id: str,
        segment_id: str,
        points: np.ndarray,
        color: tuple[float, float, float] = (0.0, 1.0, 0.0),
        line_width: float = 2.0,
    ):
        """Add colored path segment.

        Args:
            path_id: Parent path identifier
            segment_id: Unique segment identifier
            points: Nx3 array of segment points
            color: RGB color tuple
            line_width: Width of segment line
        """
        full_id = f"{path_id}/{segment_id}"
        self.add_tool_path(full_id, points, color, line_width, show_waypoints=False)

    def clear_path(self, path_id: str):
        """Remove specific path from scene."""
        if path_id not in self.path_actors:
            return

        for actor in self.path_actors[path_id]:
            self.renderer.RemoveActor(actor)

        del self.path_actors[path_id]

    def _clear_paths(self):
        """Remove all paths from scene."""
        for actors in self.path_actors.values():
            for actor in actors:
                self.renderer.RemoveActor(actor)
        self.path_actors.clear()

    def _clear_frames(self):
        """Remove all coordinate frames from scene."""
        for actor in self.frame_actors.values():
            self.renderer.RemoveActor(actor)
        self.frame_actors.clear()

    def _clear_workspace(self):
        """Remove workspace actor from scene."""
        if self.workspace_actor:
            self.renderer.RemoveActor(self.workspace_actor)
            self.workspace_actor = None

    def show_frame(self, link_name: str, visible: bool = True):
        """Show/hide coordinate frame at link origin.

        Args:
            link_name: Name of link
            visible: Show or hide frame
        """
        if visible:
            if link_name not in self.frame_actors:
                # Create new axes actor
                axes = vtk.vtkAxesActor()
                axes.SetShaftTypeToCylinder()
                axes.SetCylinderRadius(0.02)
                axes.SetConeRadius(0.05)
                axes.SetTotalLength(self.frame_size, self.frame_size, self.frame_size)
                axes.AxisLabelsOff()

                self.frame_actors[link_name] = axes
                self.renderer.AddActor(axes)

                # Apply current transform
                if self._env and link_name in self.link_actors:
                    try:
                        state = self._env.getState()
                        transform = state.link_transforms[link_name]
                        axes.SetUserTransform(self._isometry_to_vtk(transform))
                    except (KeyError, AttributeError):
                        pass
            else:
                self.frame_actors[link_name].VisibilityOn()
        else:
            if link_name in self.frame_actors:
                self.frame_actors[link_name].VisibilityOff()

    def set_frame_size(self, size: float):
        """Set size of coordinate frames.

        Args:
            size: Frame axis length in meters
        """
        self.frame_size = size
        for axes in self.frame_actors.values():
            axes.SetTotalLength(size, size, size)

    def set_tcp_link(self, link_name: str | None):
        """Set TCP (tool center point) link for special highlighting.

        Args:
            link_name: Name of TCP link, or None to clear
        """
        self._tcp_link = link_name

    def show_tcp_frame(self, visible: bool = True):
        """Show TCP frame if TCP link is set.

        Args:
            visible: Show or hide TCP frame
        """
        if self._tcp_link:
            self.show_frame(self._tcp_link, visible)

    def visualize_contacts(self, contact_results):
        """Visualize collision/contact results.

        Args:
            contact_results: ContactResultVector from tesseract collision checking
        """
        self.contact_viz.visualize_contacts(contact_results, self.link_actors)

    def clear_contacts(self):
        """Clear contact visualization."""
        self.contact_viz.clear()

    def get_tcp_pose(self, joint_values: dict[str, float], tcp_link: str) -> tesseract_common.Isometry3d | None:
        """Get TCP pose from joint values via FK.

        Args:
            joint_values: Joint name -> value mapping
            tcp_link: Target link name

        Returns:
            TCP transform or None if FK fails
        """
        if self._env is None:
            return None

        try:
            # Update env state with joint values
            for name, value in joint_values.items():
                self._env.setState([name], [value])

            state = self._env.getState()
            return state.link_transforms.get(tcp_link)
        except Exception as e:
            print(f"FK failed: {e}")
            return None

    def show_tcp_marker(self, pose: tesseract_common.Isometry3d,
                        radius: float = 0.02,
                        color: tuple[float, float, float] = (1.0, 0.0, 1.0)):
        """Display TCP position marker at pose.

        Args:
            pose: TCP transform
            radius: Marker sphere radius
            color: RGB color
        """
        marker_id = "tcp_marker"
        self._clear_fk_actors(marker_id)

        # Create sphere at TCP position
        sphere = vtk.vtkSphereSource()
        trans = pose.translation
        sphere.SetCenter(float(trans[0]), float(trans[1]), float(trans[2]))
        sphere.SetRadius(radius)
        sphere.SetPhiResolution(16)
        sphere.SetThetaResolution(16)

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(sphere.GetOutputPort())

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(*color)

        self.renderer.AddActor(actor)
        self._fk_actors[marker_id] = [actor]

    def show_fk_chain(self, joint_values: dict[str, float],
                      base_link: str,
                      tip_link: str,
                      line_width: float = 3.0,
                      color: tuple[float, float, float] = (0.0, 1.0, 1.0)):
        """Visualize FK chain as lines between link origins.

        Args:
            joint_values: Joint values
            base_link: Chain start link
            tip_link: Chain end link
            line_width: Line width
            color: RGB color
        """
        chain_id = "fk_chain"
        self._clear_fk_actors(chain_id)

        if self._env is None:
            return

        try:
            # Update state
            for name, value in joint_values.items():
                self._env.setState([name], [value])

            state = self._env.getState()
            sg_obj = self._env.getSceneGraph()

            # Get chain from base to tip
            path = sg_obj.getShortestPath(base_link, tip_link)
            if not path or len(path.links) < 2:
                return

            # Extract link origins
            points = vtk.vtkPoints()
            for link_name in path.links:
                if link_name in state.link_transforms:
                    tf = state.link_transforms[link_name]
                    trans = tf.translation
                    points.InsertNextPoint(float(trans[0]), float(trans[1]), float(trans[2]))

            if points.GetNumberOfPoints() < 2:
                return

            # Create polyline
            lines = vtk.vtkCellArray()
            for i in range(points.GetNumberOfPoints() - 1):
                line = vtk.vtkLine()
                line.GetPointIds().SetId(0, i)
                line.GetPointIds().SetId(1, i + 1)
                lines.InsertNextCell(line)

            polydata = vtk.vtkPolyData()
            polydata.SetPoints(points)
            polydata.SetLines(lines)

            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputData(polydata)

            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(*color)
            actor.GetProperty().SetLineWidth(line_width)

            self.renderer.AddActor(actor)
            self._fk_actors[chain_id] = [actor]

        except Exception as e:
            print(f"FK chain viz failed: {e}")

    def clear_fk_viz(self):
        """Clear all FK visualization actors."""
        for actors in self._fk_actors.values():
            for actor in actors:
                self.renderer.RemoveActor(actor)
        self._fk_actors.clear()

    def _clear_fk_actors(self, viz_id: str):
        """Clear specific FK viz actors."""
        if viz_id in self._fk_actors:
            for actor in self._fk_actors[viz_id]:
                self.renderer.RemoveActor(actor)
            del self._fk_actors[viz_id]
    def sample_workspace(
        self,
        joint_names: list[str],
        joint_limits: dict[str, tuple[float, float]],
        n_samples: int = 1000,
        tcp_link: str | None = None,
    ) -> np.ndarray:
        """Sample robot workspace by randomizing joints.

        Args:
            joint_names: List of joint names to sample
            joint_limits: Dict mapping joint name to (min, max) limits
            n_samples: Number of random samples
            tcp_link: Link to track position (defaults to self._tcp_link)

        Returns:
            Nx3 array of TCP positions
        """
        if self._env is None:
            return np.array([])

        tcp = tcp_link or self._tcp_link
        if tcp is None:
            return np.array([])

        points = []
        for _ in range(n_samples):
            # Random joint config
            values = {}
            for name in joint_names:
                lo, hi = joint_limits.get(name, (-3.14, 3.14))
                values[name] = np.random.uniform(lo, hi)

            # Set state
            for name, val in values.items():
                try:
                    self._env.setState([name], [val])
                except Exception:
                    pass

            # Get TCP position
            try:
                state = self._env.getState()
                transform = state.link_transforms[tcp]
                matrix = transform.matrix()
                points.append([matrix[0, 3], matrix[1, 3], matrix[2, 3]])
            except (KeyError, AttributeError):
                pass

        return np.array(points)

    def compute_manipulability(
        self,
        points: np.ndarray,
        reference: np.ndarray | None = None,
    ) -> np.ndarray:
        """Compute scalar metric for point cloud coloring.

        Args:
            points: Nx3 point array
            reference: Reference point for distance computation (defaults to centroid)

        Returns:
            N-length array of scalars (0-1 normalized)
        """
        if len(points) == 0:
            return np.array([])

        if reference is None:
            reference = points.mean(axis=0)

        # Distance from reference
        dists = np.linalg.norm(points - reference, axis=1)

        # Normalize to 0-1
        if dists.max() > 0:
            return dists / dists.max()
        return np.zeros(len(points))

    def show_workspace(
        self,
        points: np.ndarray,
        scalars: np.ndarray | None = None,
        point_size: float = 3.0,
        opacity: float = 0.6,
    ):
        """Display workspace as point cloud.

        Args:
            points: Nx3 point positions
            scalars: Optional N-length scalar array for coloring
            point_size: Point render size
            opacity: Point opacity (0-1)
        """
        self._clear_workspace()

        if len(points) == 0:
            return

        # VTK points
        vtk_points = vtk.vtkPoints()
        for pt in points:
            vtk_points.InsertNextPoint(float(pt[0]), float(pt[1]), float(pt[2]))

        polydata = vtk.vtkPolyData()
        polydata.SetPoints(vtk_points)

        # Vertex cells
        vertices = vtk.vtkCellArray()
        for i in range(len(points)):
            vertices.InsertNextCell(1)
            vertices.InsertCellPoint(i)
        polydata.SetVerts(vertices)

        # Scalars for color mapping
        if scalars is not None and len(scalars) == len(points):
            vtk_scalars = vtk.vtkFloatArray()
            for s in scalars:
                vtk_scalars.InsertNextValue(float(s))
            polydata.GetPointData().SetScalars(vtk_scalars)

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(polydata)

        if scalars is not None:
            # Blue-to-red colormap
            lut = vtk.vtkLookupTable()
            lut.SetHueRange(0.667, 0.0)  # blue to red
            lut.SetNumberOfTableValues(256)
            lut.Build()
            mapper.SetLookupTable(lut)
            mapper.SetScalarRange(scalars.min(), scalars.max())

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetPointSize(point_size)
        actor.GetProperty().SetOpacity(opacity)

        self.workspace_actor = actor
        self.renderer.AddActor(actor)

    def hide_workspace(self):
        """Remove workspace visualization."""
        self._clear_workspace()

    def show_ik_target(self, pose):
        """Display IK target as small axes/frame.

        Args:
            pose: Target transform (Isometry3d)
        """
        target_id = "ik_target"

        # Clear existing target
        if target_id in self.frame_actors:
            self.renderer.RemoveActor(self.frame_actors[target_id])
            del self.frame_actors[target_id]

        # Create axes actor
        axes = vtk.vtkAxesActor()
        axes.SetShaftTypeToCylinder()
        axes.SetCylinderRadius(0.02)
        axes.SetConeRadius(0.05)
        axes.SetTotalLength(0.15, 0.15, 0.15)  # Slightly larger than default frame
        axes.AxisLabelsOff()

        # Apply target transform
        axes.SetUserTransform(self._isometry_to_vtk(pose))

        self.frame_actors[target_id] = axes
        self.renderer.AddActor(axes)
