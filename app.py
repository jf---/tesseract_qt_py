"""Tesseract Qt Viewer."""
from __future__ import annotations

import sys
import os

# CRITICAL: macOS VTK+Qt setup - NO X11
if sys.platform == 'darwin':
    os.environ.pop('DISPLAY', None)
    os.environ['QT_QPA_PLATFORM'] = 'cocoa'

# Force QOpenGLWidget base for VTK - required for rendering to work
import vtkmodules.qt
vtkmodules.qt.QVTKRWIBase = "QOpenGLWidget"

from loguru import logger
logger.add("/tmp/tesseract_viewer.log", rotation="1 MB", level="DEBUG")
logger.info("Starting tesseract_qt_py viewer")

from pathlib import Path

from PySide6.QtCore import Qt, QSettings
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QDockWidget, QFileDialog, QMessageBox, QStatusBar,
    QInputDialog,
)
from PySide6.QtGui import QAction, QKeySequence, QShortcut

from tesseract_robotics.tesseract_environment import Environment
from tesseract_robotics.tesseract_common import GeneralResourceLocator, FilesystemPath
from tesseract_robotics.tesseract_scene_graph import JointType

from widgets.render_widget import RenderWidget
from widgets.joint_slider import JointSliderWidget
from widgets.scene_tree import SceneTreeWidget
from widgets.ik_widget import IKWidget
from widgets.info_panel import RobotInfoPanel
from core.state_manager import StateManager


class TesseractViewer(QMainWindow):
    """Main viewer window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tesseract Viewer")
        self.resize(1400, 900)
        self._env = None
        self._paths = (None, None)  # urdf, srdf
        self._settings = QSettings("tesseract_qt", "viewer")
        self._recent_actions = []
        self.state_mgr = StateManager()
        self._setup()

    def _setup(self):
        # Widgets
        self.render = RenderWidget()
        self.setCentralWidget(self.render)

        self.tree_dock = QDockWidget("Scene", self)
        self.tree = SceneTreeWidget()
        self.tree_dock.setWidget(self.tree)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.tree_dock)

        self.joint_dock = QDockWidget("Joints", self)
        self.joints = JointSliderWidget()
        self.joint_dock.setWidget(self.joints)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.joint_dock)

        self.ik_dock = QDockWidget("IK Solver", self)
        self.ik_widget = IKWidget()
        self.ik_dock.setWidget(self.ik_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.ik_dock)

        self.info_dock = QDockWidget("Robot Info", self)
        self.info_panel = RobotInfoPanel()
        self.info_dock.setWidget(self.info_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.info_dock)

        self.setStatusBar(QStatusBar())

        # Menu
        file_menu = self.menuBar().addMenu("File")
        file_menu.addAction("Open URDF...", self._open_urdf, QKeySequence.StandardKey.Open)
        file_menu.addAction("Open SRDF...", self._open_srdf)
        file_menu.addSeparator()

        self._recent_menu = file_menu.addMenu("Recent Files")
        for i in range(10):
            act = QAction(self)
            act.setVisible(False)
            act.triggered.connect(lambda checked=False, idx=i: self._open_recent(idx))
            self._recent_actions.append(act)
            self._recent_menu.addAction(act)
        self._update_recent_menu()

        file_menu.addSeparator()
        file_menu.addAction("Reload", self._reload, QKeySequence.StandardKey.Refresh)
        file_menu.addSeparator()

        export_menu = file_menu.addMenu("Export")
        export_menu.addAction("Screenshot (PNG)...", self._export_screenshot)
        export_menu.addAction("Scene (STL)...", self._export_stl)
        export_menu.addAction("Scene (OBJ)...", self._export_obj)

        file_menu.addSeparator()
        file_menu.addAction("Quit", self.close, QKeySequence.StandardKey.Quit)

        state_menu = self.menuBar().addMenu("State")
        state_menu.addAction("Save Configuration...", self._save_config, QKeySequence("Ctrl+S"))
        state_menu.addAction("Load Configuration...", self._load_config, QKeySequence("Ctrl+O"))
        state_menu.addSeparator()
        state_menu.addAction("Save Pose As...", self._save_pose)
        state_menu.addAction("Load Pose...", self._load_pose)

        view_menu = self.menuBar().addMenu("View")
        view_menu.addAction(self.tree_dock.toggleViewAction())
        view_menu.addAction(self.joint_dock.toggleViewAction())
        view_menu.addAction(self.ik_dock.toggleViewAction())
        view_menu.addAction(self.info_dock.toggleViewAction())

        # Connections
        self.joints.jointValuesChanged.connect(self.render.update_joint_values)
        self.joints.jointValuesChanged.connect(self.info_panel.update_joint_values)
        self.tree.linkSelected.connect(lambda n: (self.render.scene.highlight_link(n), self.render.render()))
        self.tree.linkVisibilityChanged.connect(lambda n, v: (self.render.scene.set_link_visibility(n, v), self.render.render()))
        self.tree.linkFrameToggled.connect(lambda n, v: (self.render.scene.show_frame(n, v), self.render.render()))
        self.render.linkClicked.connect(self.tree.select_link)
        self.ik_widget.solutionFound.connect(self.joints.set_values)

        # Keyboard shortcuts
        self._setup_shortcuts()

    def load(self, urdf: str | Path, srdf: str | Path = None):
        """Load robot from URDF."""
        try:
            logger.info(f"Loading URDF: {urdf}")
            self._paths = (Path(urdf), Path(srdf) if srdf else None)
            self._env = Environment()
            loc = GeneralResourceLocator()

            if srdf:
                logger.info(f"Loading with SRDF: {srdf}")
                if not self._env.init(str(urdf), str(srdf), loc):
                    raise RuntimeError("Failed to init environment with SRDF")
            else:
                logger.info("Loading URDF only (no SRDF)")
                if not self._env.init(str(urdf), loc):
                    raise RuntimeError("Failed to init environment from URDF")

            logger.info("Environment initialized, loading into render widget")
            self.render.load_environment(self._env)
            logger.info("Render loaded, setting up tree")
            self.tree.load_environment(self._env)
            logger.info("Tree loaded, setting up joints")
            self._setup_joints()
            logger.info("Joints setup, loading info panel")
            self.info_panel.load_environment(self._env)
            logger.info("Info panel loaded, setting up IK widget")
            self.ik_widget.set_environment(self._env)
            self.statusBar().showMessage(f"Loaded: {urdf}")
            self._add_recent(str(Path(urdf).resolve()))
            logger.success(f"Successfully loaded: {urdf}")

        except Exception as e:
            logger.exception(f"Failed to load: {e}")
            QMessageBox.critical(self, "Error", str(e))

    def _setup_joints(self):
        sg = self._env.getSceneGraph()
        movable = (JointType.REVOLUTE, JointType.CONTINUOUS, JointType.PRISMATIC)
        joints = {}
        for j in sg.getJoints():
            if j.type in movable:
                lim = j.limits
                lo, hi = (lim.lower, lim.upper) if lim else (-3.14, 3.14)
                joints[j.getName()] = (lo, hi, 0.0)
        self.joints.set_joints(joints)

    def _open_urdf(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open URDF", "", "URDF (*.urdf);;All (*)")
        if path:
            self.load(path)

    def _open_srdf(self):
        if not self._paths[0]:
            QMessageBox.information(self, "Info", "Load URDF first")
            return
        path, _ = QFileDialog.getOpenFileName(self, "Open SRDF", str(self._paths[0].parent), "SRDF (*.srdf)")
        if path:
            self.load(self._paths[0], path)

    def _add_recent(self, path: str):
        """Add to recent files."""
        recent = self._settings.value("recent", []) or []
        if path in recent:
            recent.remove(path)
        recent.insert(0, path)
        self._settings.setValue("recent", recent[:10])
        self._update_recent_menu()

    def _update_recent_menu(self):
        """Update recent files menu."""
        recent = self._settings.value("recent", []) or []
        for i, act in enumerate(self._recent_actions):
            if i < len(recent):
                p = Path(recent[i])
                act.setText(f"{i+1}. {p.name}")
                act.setToolTip(str(p))
                act.setVisible(True)
            else:
                act.setVisible(False)
        self._recent_menu.setEnabled(len(recent) > 0)

    def _open_recent(self, idx: int):
        """Open recent file."""
        recent = self._settings.value("recent", []) or []
        if idx < len(recent):
            path = Path(recent[idx])
            if path.exists():
                self.load(path)
            else:
                QMessageBox.warning(self, "Not Found", f"File not found: {path}")
                recent.remove(str(path))
                self._settings.setValue("recent", recent)
                self._update_recent_menu()

    def _reload(self):
        if self._paths[0]:
            self.load(*self._paths)

    def _save_config(self):
        """Save joint config to JSON."""
        if not self.joints.sliders:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save Config", "", "JSON (*.json)")
        if path:
            try:
                values = self.joints.get_values()
                path = Path(path)
                import json
                with path.open("w") as f:
                    json.dump(values, f, indent=2)
                self.statusBar().showMessage(f"Saved: {path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _load_config(self):
        """Load joint config from JSON."""
        if not self.joints.sliders:
            return
        path, _ = QFileDialog.getOpenFileName(self, "Load Config", "", "JSON (*.json)")
        if path:
            try:
                path = Path(path)
                import json
                with path.open("r") as f:
                    values = json.load(f)
                self.joints.set_values(values)
                self.statusBar().showMessage(f"Loaded: {path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _save_pose(self):
        """Save current config as named pose."""
        if not self.joints.sliders:
            return
        name, ok = QInputDialog.getText(self, "Save Pose", "Pose name:")
        if ok and name:
            values = self.joints.get_values()
            self.state_mgr.save_pose(name, values)
            self.statusBar().showMessage(f"Saved pose: {name}")

    def _load_pose(self):
        """Load named pose."""
        if not self.joints.sliders:
            return
        poses = self.state_mgr.list_poses()
        if not poses:
            QMessageBox.information(self, "Info", "No saved poses")
            return
        name, ok = QInputDialog.getItem(self, "Load Pose", "Select pose:", poses, 0, False)
        if ok and name:
            values = self.state_mgr.load_pose(name)
            if values:
                self.joints.set_values(values)
                self.statusBar().showMessage(f"Loaded pose: {name}")


    def _export_screenshot(self):
        """Export screenshot as PNG."""
        path, _ = QFileDialog.getSaveFileName(self, "Export Screenshot", "", "PNG (*.png)")
        if path:
            try:
                self.render.save_screenshot(path)
                self.statusBar().showMessage(f"Saved: {path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _export_stl(self):
        """Export scene as STL."""
        path, _ = QFileDialog.getSaveFileName(self, "Export STL", "", "STL (*.stl)")
        if path:
            try:
                self.render.export_scene(path)
                self.statusBar().showMessage(f"Saved: {path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _export_obj(self):
        """Export scene as OBJ."""
        path, _ = QFileDialog.getSaveFileName(self, "Export OBJ", "", "OBJ (*.obj)")
        if path:
            try:
                self.render.export_scene(path)
                self.statusBar().showMessage(f"Saved: {path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _setup_shortcuts(self):
        """Setup global keyboard shortcuts."""
        # View shortcuts
        QShortcut("Home", self, self.render.action_reset.trigger)
        QShortcut("F", self, self.render.action_fit.trigger)
        QShortcut("1", self, self.render.action_front.trigger)
        QShortcut("2", self, self.render.action_back.trigger)
        QShortcut("3", self, self.render.action_left.trigger)
        QShortcut("4", self, self.render.action_right.trigger)
        QShortcut("5", self, self.render.action_top.trigger)
        QShortcut("6", self, self.render.action_bottom.trigger)
        QShortcut("7", self, self.render.action_iso.trigger)
        QShortcut("G", self, self.render.action_grid.trigger)
        QShortcut("A", self, self.render.action_axes.trigger)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    v = TesseractViewer()
    v.show()

    # macOS: VTK needs re-initialization after window is shown
    v.render.vtk_widget.Initialize()
    v.render.vtk_widget.Start()
    v.render.vtk_widget.GetRenderWindow().Render()

    # Bring window to front
    v.raise_()
    v.activateWindow()

    if len(sys.argv) > 1:
        v.load(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
        v.render.vtk_widget.GetRenderWindow().Render()  # Force render after load

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
