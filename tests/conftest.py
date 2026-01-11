"""pytest config - macOS VTK+Qt setup, fixtures."""

# CRITICAL: macOS VTK+Qt env BEFORE imports
import os

os.environ.pop("DISPLAY", None)
os.environ["QT_QPA_PLATFORM"] = "cocoa"

import sys
from pathlib import Path
import pytest

# add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="session", autouse=True)
def vtk_qt_setup():
    """configure VTK Qt rendering for macOS."""
    try:
        import vtkmodules.qt

        vtkmodules.qt.QVTKRWIBase = "QOpenGLWidget"
    except ImportError:
        pass  # VTK not needed for widget-only tests
    yield


@pytest.fixture(scope="session")
def qapp():
    """Qt application fixture."""
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def sample_trajectory():
    """sample trajectory for testing player widget."""

    class MockWaypoint:
        def __init__(self, time, positions=None):
            self.time = time
            self.positions = positions or []

    return [MockWaypoint(i * 0.033, [0.0] * 6) for i in range(30)]
