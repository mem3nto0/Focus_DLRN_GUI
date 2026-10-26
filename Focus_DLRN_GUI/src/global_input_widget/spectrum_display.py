from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout
import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure


class Matrix2dWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMaximumHeight(400)
        self.figure = Figure()
        self.canvas = FigureCanvasQTAgg(self.figure)

        self.timescale_data: np.ndarray | None = None
        self.spectrum_data: np.ndarray | None = None
        self.selected_spectrum_index = 0
        self.marker_index = 0
        self._pressed = False
        self._xlim: tuple[float, float] | None = None
        self._ylim: tuple[float, float] | None = None
        self._has_initial_view = False

        self.canvas.mpl_connect("scroll_event", self._on_scroll)
        self.canvas.mpl_connect("button_press_event", self._on_button_press)
        self.canvas.mpl_connect("motion_notify_event", self._on_mouse_move)
        self.canvas.mpl_connect("button_release_event", self._on_button_release)

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        self.clear()

    def plot(self, data: list[list[float]], timescale_data: list[float] | None = None, selected_spectrum_index: int = 0):
        if not data:
            self.clear()
            return

        spectrum_matrix = np.asarray(data, dtype=float)
        if spectrum_matrix.ndim == 1:
            spectrum_matrix = spectrum_matrix.reshape(1, -1)

        self.spectrum_data = spectrum_matrix
        self.timescale_data = np.asarray(timescale_data, dtype=float) if timescale_data is not None else np.arange(spectrum_matrix.shape[1], dtype=float)
        self.selected_spectrum_index = max(0, min(int(selected_spectrum_index), spectrum_matrix.shape[0] - 1))
        self.marker_index = min(max(0, self.marker_index), len(self.timescale_data) - 1)
        self._has_initial_view = False
        self._xlim = None
        self._ylim = None
        self._draw_plot()

    def set_selected_spectrum(self, index: int):
        if self.spectrum_data is None:
            return
        if index < 0:
            index = 0
        if index >= self.spectrum_data.shape[0]:
            index = self.spectrum_data.shape[0] - 1
        self.selected_spectrum_index = index
        self._draw_plot()

    def set_marker_index(self, index: int):
        if self.timescale_data is None:
            return
        idx = max(0, min(int(index), len(self.timescale_data) - 1))
        self.marker_index = idx
        self._draw_plot()

    def _snap_to_timepoint(self, x_value: float | None):
        if self.timescale_data is None:
            return self.marker_index

        if x_value is None:
            return self.marker_index

        x_min, x_max = self.figure.axes[0].get_xlim()
        if x_min > x_max:
            x_min, x_max = x_max, x_min

        visible_indices = np.where((self.timescale_data >= x_min) & (self.timescale_data <= x_max))[0]
        if visible_indices.size == 0:
            return int(np.clip(np.argmin(np.abs(self.timescale_data - x_value)), 0, len(self.timescale_data) - 1))

        distances = np.abs(self.timescale_data[visible_indices] - x_value)
        return int(visible_indices[np.argmin(distances)])

    def _on_button_press(self, event):
        if self.timescale_data is None or event.inaxes is None:
            return
        self._pressed = True
        self.set_marker_index(self._snap_to_timepoint(event.xdata))

    def _on_mouse_move(self, event):
        if self.timescale_data is None or not self._pressed or event.inaxes is None:
            return
        self.set_marker_index(self._snap_to_timepoint(event.xdata))

    def _on_button_release(self, event):
        self._pressed = False

    def _on_scroll(self, event):
        if self.timescale_data is None or event.inaxes is None:
            return
        ax = event.inaxes
        x_min, x_max = ax.get_xlim()
        span = x_max - x_min
        if span <= 0:
            return
        if event.button == 'up':
            scale = 0.85
        else:
            scale = 1.15

        anchor_x = event.xdata if event.xdata is not None else (x_min + x_max) / 2
        left = anchor_x - (anchor_x - x_min) * scale
        right = anchor_x + (x_max - anchor_x) * scale
        ax.set_xlim(left, right)
        self._xlim = tuple(ax.get_xlim())
        self._ymin, self._ymax = ax.get_ylim()
        self._ylim = (self._ymin, self._ymax)
        self._has_initial_view = True
        self.canvas.draw_idle()

    def _draw_plot(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        if self.spectrum_data is not None and self.timescale_data is not None and len(self.spectrum_data) > 0:
            trace = self.spectrum_data[self.selected_spectrum_index]
            ax.plot(self.timescale_data, trace, color="tab:blue", linewidth=1.8)

            if len(self.timescale_data) > 0:
                marker_time = self.timescale_data[self.marker_index]
                ax.axvline(marker_time, color="gray", linestyle="--", linewidth=1.5, alpha=0.9)
                ax.scatter([marker_time], [trace[self.marker_index]], color="gray", s=25, zorder=3)

            if self._xlim is not None and self._ylim is not None and self._has_initial_view:
                ax.set_xlim(self._xlim)
                ax.set_ylim(self._ylim)
            else:
                ax.set_xlim(float(np.min(self.timescale_data)), float(np.max(self.timescale_data)))
                all_values = self.spectrum_data.reshape(-1)
                y_min = float(np.min(all_values))
                y_max = float(np.max(all_values))
                if np.isclose(y_min, y_max):
                    y_min -= 1.0
                    y_max += 1.0
                ax.set_ylim(y_min, y_max)
                self._xlim = tuple(ax.get_xlim())
                self._ylim = tuple(ax.get_ylim())
                self._has_initial_view = True

            ax.set_xlabel("Time")
            ax.set_ylabel("Intensity")
            ax.set_title(f"Spectrum {self.selected_spectrum_index + 1}")
            ax.grid(True, alpha=0.2)
            self.figure.tight_layout()
        else:
            ax.plot([], [], color="tab:blue")
            ax.set_xlabel("Time")
            ax.set_ylabel("Intensity")
            ax.set_title("No spectrum loaded")
            ax.grid(True, alpha=0.2)
            self.figure.tight_layout()

        self.canvas.draw()

    def clear(self):
        self.timescale_data = None
        self.spectrum_data = None
        self.selected_spectrum_index = 0
        self.marker_index = 0
        self._xlim = None
        self._ylim = None
        self._has_initial_view = False
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.plot([], [], color="tab:blue")
        ax.set_xlabel("Time")
        ax.set_ylabel("Intensity")
        ax.set_title("No spectrum loaded")
        ax.grid(True, alpha=0.2)
        self.figure.tight_layout()
        self.canvas.draw()
