"""Trajectory playback widget."""
from __future__ import annotations

from PySide6.QtCore import Signal, Qt, QTimer
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSlider,
    QLabel,
    QPushButton,
    QDoubleSpinBox,
)


class TrajectoryPlayerWidget(QWidget):
    """Play/scrub through robot trajectory."""

    frameChanged = Signal(int)  # frame index
    stateChanged = Signal(str)  # playing/paused/stopped

    def __init__(self, parent=None):
        super().__init__(parent)
        self._trajectory = None
        self._frame = 0
        self._frame_count = 0
        self._playing = False
        self._speed = 1.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_timer)
        self._updating = False

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Transport controls
        controls = QHBoxLayout()
        controls.setSpacing(4)

        self.btn_play = QPushButton("▶")
        self.btn_play.setFixedSize(32, 32)
        self.btn_play.clicked.connect(self._on_play_pause)
        controls.addWidget(self.btn_play)

        self.btn_stop = QPushButton("■")
        self.btn_stop.setFixedSize(32, 32)
        self.btn_stop.clicked.connect(self._on_stop)
        controls.addWidget(self.btn_stop)

        # Speed control
        controls.addWidget(QLabel("Speed:"))
        self.speed_spinbox = QDoubleSpinBox()
        self.speed_spinbox.setRange(0.1, 5.0)
        self.speed_spinbox.setValue(1.0)
        self.speed_spinbox.setSingleStep(0.1)
        self.speed_spinbox.setDecimals(1)
        self.speed_spinbox.setSuffix("x")
        self.speed_spinbox.setFixedWidth(70)
        self.speed_spinbox.valueChanged.connect(self._on_speed_changed)
        controls.addWidget(self.speed_spinbox)

        controls.addStretch()

        # Frame/time display
        self.frame_label = QLabel("0 / 0")
        self.frame_label.setFixedWidth(80)
        self.frame_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        controls.addWidget(self.frame_label)

        self.time_label = QLabel("0.000s")
        self.time_label.setFixedWidth(70)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        controls.addWidget(self.time_label)

        layout.addLayout(controls)

        # Scrubber slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 0)
        self.slider.valueChanged.connect(self._on_slider_changed)
        layout.addWidget(self.slider)

    def load_trajectory(self, trajectory):
        """Load JointTrajectory for playback.

        Args:
            trajectory: tesseract_robotics JointTrajectory or compatible structure
                       Expected to have waypoints accessible via iteration or indexing
        """
        self._trajectory = trajectory
        self._frame_count = len(trajectory) if trajectory else 0
        self._frame = 0

        self._updating = True
        self.slider.setRange(0, max(0, self._frame_count - 1))
        self.slider.setValue(0)
        self._updating = False

        self._update_labels()
        self._on_stop()

    def _on_play_pause(self):
        """Toggle play/pause."""
        if self._playing:
            self._pause()
        else:
            self._play()

    def _play(self):
        """Start playback."""
        if self._frame_count == 0:
            return

        self._playing = True
        self.btn_play.setText("⏸")
        self.stateChanged.emit("playing")

        # 30 FPS update rate
        self._timer.start(33)

    def _pause(self):
        """Pause playback."""
        self._playing = False
        self.btn_play.setText("▶")
        self._timer.stop()
        self.stateChanged.emit("paused")

    def _on_stop(self):
        """Stop and reset to start."""
        self._playing = False
        self.btn_play.setText("▶")
        self._timer.stop()
        self._frame = 0

        self._updating = True
        self.slider.setValue(0)
        self._updating = False

        self._update_labels()
        self.frameChanged.emit(0)
        self.stateChanged.emit("stopped")

    def _on_timer(self):
        """Advance frame during playback."""
        if not self._playing or self._frame_count == 0:
            return

        # Increment based on speed
        # Assume ~30ms per frame, get time delta from trajectory
        self._frame += 1

        if self._frame >= self._frame_count:
            if self._frame_count > 0:
                self._frame = 0  # Loop
            else:
                self._on_stop()
                return

        self._updating = True
        self.slider.setValue(self._frame)
        self._updating = False

        self._update_labels()
        self.frameChanged.emit(self._frame)

    def _on_slider_changed(self, value: int):
        """Handle manual scrubbing."""
        if self._updating:
            return

        self._frame = value
        self._update_labels()
        self.frameChanged.emit(self._frame)

    def _on_speed_changed(self, speed: float):
        """Update playback speed."""
        self._speed = speed

    def _update_labels(self):
        """Update frame/time displays."""
        self.frame_label.setText(f"{self._frame} / {max(0, self._frame_count - 1)}")

        # Get timestamp from trajectory if available
        time = 0.0
        if self._trajectory and self._frame_count > 0 and self._frame < self._frame_count:
            try:
                waypoint = self._trajectory[self._frame]
                # Try common attributes for time
                if hasattr(waypoint, 'time'):
                    time = waypoint.time
                elif hasattr(waypoint, 'time_from_start'):
                    time = waypoint.time_from_start
            except (IndexError, AttributeError):
                pass

        self.time_label.setText(f"{time:.3f}s")

    def get_frame(self) -> int:
        """Get current frame index."""
        return self._frame

    def set_frame(self, frame: int):
        """Jump to specific frame."""
        if 0 <= frame < self._frame_count:
            self._frame = frame
            self._updating = True
            self.slider.setValue(frame)
            self._updating = False
            self._update_labels()
            self.frameChanged.emit(frame)

    def is_playing(self) -> bool:
        """Check if currently playing."""
        return self._playing

    def get_waypoint(self):
        """Get current waypoint from trajectory."""
        if self._trajectory and 0 <= self._frame < self._frame_count:
            return self._trajectory[self._frame]
        return None
