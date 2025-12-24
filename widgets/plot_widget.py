"""Joint trajectory plotting widget."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QToolBar
from PySide6.QtGui import QAction
import pyqtgraph as pg
import numpy as np


class PlotWidget(QWidget):
    """Plot widget for joint values over time."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.traces: dict[str, pg.PlotDataItem] = {}
        self.colors = [
            (255, 0, 0),      # red
            (0, 255, 0),      # green
            (0, 0, 255),      # blue
            (255, 255, 0),    # yellow
            (255, 0, 255),    # magenta
            (0, 255, 255),    # cyan
            (255, 128, 0),    # orange
            (128, 0, 255),    # purple
        ]
        self.data: dict[str, tuple[list[float], list[float]]] = {}

        self._setup_ui()

    def _setup_ui(self):
        """Setup widget layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        self.toolbar = QToolBar()
        self.toolbar.setMovable(False)

        self.action_clear = QAction("Clear", self)
        self.action_clear.triggered.connect(self.clear)
        self.toolbar.addAction(self.action_clear)

        self.action_autoscale = QAction("Auto Scale", self)
        self.action_autoscale.triggered.connect(self.autoscale)
        self.toolbar.addAction(self.action_autoscale)

        layout.addWidget(self.toolbar)

        # Plot widget
        pg.setConfigOptions(antialias=True)
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setLabel('left', 'Joint Value', units='rad')
        self.plot_widget.setLabel('bottom', 'Time', units='s')
        self.plot_widget.addLegend()

        layout.addWidget(self.plot_widget)

    def add_joint(self, name: str):
        """Add joint to plot."""
        if name in self.traces:
            return

        color_idx = len(self.traces) % len(self.colors)
        pen = pg.mkPen(color=self.colors[color_idx], width=2)
        trace = self.plot_widget.plot([], [], name=name, pen=pen)
        self.traces[name] = trace
        self.data[name] = ([], [])

    def add_joints(self, names: list[str]):
        """Add multiple joints."""
        for name in names:
            self.add_joint(name)

    def update_point(self, name: str, time: float, value: float):
        """Add single data point for joint."""
        if name not in self.traces:
            self.add_joint(name)

        times, values = self.data[name]
        times.append(time)
        values.append(value)

        self.traces[name].setData(times, values)

    def update_points(self, joint_values: dict[str, float], time: float):
        """Update all joints at once."""
        for name, value in joint_values.items():
            self.update_point(name, time, value)

    def set_trajectory(self, name: str, times: list[float], values: list[float]):
        """Set full trajectory for joint."""
        if name not in self.traces:
            self.add_joint(name)

        self.data[name] = (list(times), list(values))
        self.traces[name].setData(times, values)

    def clear(self):
        """Clear all data."""
        for name in self.data:
            self.data[name] = ([], [])
            self.traces[name].setData([], [])

    def reset(self):
        """Remove all traces and clear."""
        self.plot_widget.clear()
        self.traces.clear()
        self.data.clear()
        self.plot_widget.addLegend()

    def autoscale(self):
        """Auto-scale axes to fit data."""
        self.plot_widget.autoRange()
