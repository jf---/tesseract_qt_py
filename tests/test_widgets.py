"""Test widget functionality."""
import pytest


def test_plot_widget_load_trajectory(qapp):
    """Test PlotWidget loads trajectory data."""
    from widgets.plot_widget import PlotWidget

    plot = PlotWidget()

    trajectory = [
        {"time": 0.0, "joints": {"j1": 0.0, "j2": 0.0}},
        {"time": 1.0, "joints": {"j1": 1.0, "j2": -0.5}},
        {"time": 2.0, "joints": {"j1": 0.5, "j2": 0.5}},
    ]

    plot.load_trajectory(trajectory, ["j1", "j2"])

    assert "j1" in plot.data
    assert "j2" in plot.data
    assert len(plot.data["j1"][0]) == 3  # 3 time points
    assert plot.data["j1"][1] == [0.0, 1.0, 0.5]  # j1 values


def test_plot_widget_frame_marker(qapp):
    """Test PlotWidget frame marker."""
    from widgets.plot_widget import PlotWidget

    plot = PlotWidget()

    trajectory = [
        {"time": 0.0, "joints": {"j1": 0.0}},
        {"time": 1.0, "joints": {"j1": 1.0}},
        {"time": 2.0, "joints": {"j1": 2.0}},
    ]

    plot.load_trajectory(trajectory, ["j1"])
    plot.set_frame_marker(1)

    assert plot.frame_line is not None


def test_contact_widget_results(qapp):
    """Test ContactComputeWidget results table."""
    from widgets.contact_compute_widget import ContactComputeWidget

    widget = ContactComputeWidget()

    widget.add_result(
        "link_a", "link_b", 0.001,
        [0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [1.0, 0.0, 0.0]
    )

    assert widget.contact_results_widget.rowCount() == 1
    assert widget.contact_results_widget.item(0, 0).text() == "link_a"
    assert widget.contact_results_widget.item(0, 1).text() == "link_b"

    widget.clear_results()
    assert widget.contact_results_widget.rowCount() == 0


def test_ik_widget_signals(qapp):
    """Test IKWidget has required signals."""
    from widgets.ik_widget import IKWidget

    widget = IKWidget()

    assert hasattr(widget, 'solutionFound')
    assert hasattr(widget, 'targetPoseSet')
    assert hasattr(widget, 'planRequested')
    assert hasattr(widget, 'set_planning_status')


def test_scene_tree_signals(qapp):
    """Test SceneTreeWidget has required signals."""
    from widgets.scene_tree import SceneTreeWidget

    widget = SceneTreeWidget()

    assert hasattr(widget, 'linkSelected')
    assert hasattr(widget, 'linkVisibilityChanged')
    assert hasattr(widget, 'linkDeleteRequested')


def test_all_docks_in_view_menu():
    """Test all dock widgets are accessible via View menu."""
    from pathlib import Path
    import re

    app_py = Path(__file__).parent.parent / "app.py"
    content = app_py.read_text()

    dock_pattern = r'self\.(\w+_dock)\s*=\s*QDockWidget'
    created_docks = set(re.findall(dock_pattern, content))

    menu_pattern = r'view_menu\.addAction\(self\.(\w+_dock)\.toggleViewAction'
    menu_docks = set(re.findall(menu_pattern, content))

    missing = created_docks - menu_docks
    assert not missing, f"Docks missing from View menu: {missing}"


def test_window_size_reasonable():
    """Test app.py configures reasonable window size."""
    from pathlib import Path
    import re

    app_py = Path(__file__).parent.parent / "app.py"
    content = app_py.read_text()

    # Check resize() call
    match = re.search(r'self\.resize\((\d+),\s*(\d+)\)', content)
    assert match, "No resize() call found"

    width, height = int(match.group(1)), int(match.group(2))
    assert width <= 1600, f"Default width too large: {width}"
    assert height <= 1000, f"Default height too large: {height}"
