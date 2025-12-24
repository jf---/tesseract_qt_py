"""Joint trajectory plotting widget using matplotlib."""
from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout, QToolBar
from PySide6.QtGui import QAction
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import numpy as np


class PlotWidget(QWidget):
    """Plot widget for joint values over time."""

    COLORS = ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00', '#ffff33', '#a65628', '#f781bf']

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data: dict[str, tuple[list[float], list[float]]] = {}
        self.lines: dict[str, object] = {}
        self.frame_line = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar = QToolBar()
        toolbar.setMovable(False)

        action_clear = QAction("Clear", self)
        action_clear.triggered.connect(self.clear)
        toolbar.addAction(action_clear)

        action_autoscale = QAction("Auto Scale", self)
        action_autoscale.triggered.connect(self.autoscale)
        toolbar.addAction(action_autoscale)

        layout.addWidget(toolbar)

        # Matplotlib figure
        self.figure = Figure(figsize=(5, 3), dpi=100)
        self.figure.set_facecolor('white')
        self.ax = self.figure.add_subplot(111)
        self.ax.set_xlabel('Time (s)')
        self.ax.set_ylabel('Joint Value (rad)')
        self.ax.grid(True, alpha=0.3)
        self.figure.tight_layout()

        self.canvas = FigureCanvasQTAgg(self.figure)
        layout.addWidget(self.canvas)

    def add_joint(self, name: str):
        if name in self.lines:
            return
        color = self.COLORS[len(self.lines) % len(self.COLORS)]
        line, = self.ax.plot([], [], label=name, color=color, linewidth=1.5)
        self.lines[name] = line
        self.data[name] = ([], [])
        self.ax.legend(loc='upper right', fontsize='small')

    def set_trajectory(self, name: str, times: list[float], values: list[float]):
        if name not in self.lines:
            self.add_joint(name)
        self.data[name] = (list(times), list(values))
        self.lines[name].set_data(times, values)

    def clear(self):
        for name in self.data:
            self.data[name] = ([], [])
            self.lines[name].set_data([], [])
        if self.frame_line:
            self.frame_line.remove()
            self.frame_line = None
        self.canvas.draw_idle()

    def reset(self):
        self.ax.clear()
        self.ax.set_xlabel('Time (s)')
        self.ax.set_ylabel('Joint Value (rad)')
        self.ax.grid(True, alpha=0.3)
        self.lines.clear()
        self.data.clear()
        self.frame_line = None

    def autoscale(self):
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw_idle()

    def load_trajectory(self, trajectory: list[dict], joint_names: list[str]):
        """Load trajectory data and plot all joints."""
        self.reset()
        if not trajectory:
            return

        times = [wp["time"] for wp in trajectory]
        for joint_name in joint_names:
            values = [wp["joints"].get(joint_name, 0.0) for wp in trajectory]
            self.set_trajectory(joint_name, times, values)

        self.ax.legend(loc='upper right', fontsize='small')
        self.autoscale()

    def set_frame_marker(self, frame_idx: int):
        """Set vertical line marker at current frame."""
        if not self.data:
            return

        first_joint = next(iter(self.data.values()))
        times = first_joint[0]
        if not times or frame_idx >= len(times):
            return

        time_value = times[frame_idx]

        if self.frame_line:
            self.frame_line.set_xdata([time_value, time_value])
        else:
            self.frame_line = self.ax.axvline(x=time_value, color='red', linestyle='--', linewidth=1.5)

        self.canvas.draw_idle()

    # Legacy API compatibility
    def add_joints(self, names: list[str]):
        for name in names:
            self.add_joint(name)

    def update_point(self, name: str, time: float, value: float):
        if name not in self.lines:
            self.add_joint(name)
        times, values = self.data[name]
        times.append(time)
        values.append(value)
        self.lines[name].set_data(times, values)
        self.canvas.draw_idle()

    def update_points(self, joint_values: dict[str, float], time: float):
        for name, value in joint_values.items():
            self.update_point(name, time, value)
