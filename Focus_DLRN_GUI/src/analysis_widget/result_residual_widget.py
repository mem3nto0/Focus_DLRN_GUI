import numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure


class ResultResidualsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.figure = Figure(figsize=(5.1, 2.8), dpi=100)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.canvas.setMinimumSize(420, 220)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def plot(self, data: list[list[float]], time: list[float] | None = None):
        self.figure.clear()
        ax = self.figure.add_axes([0.10, 0.18, 0.80, 0.72])

        try:
            arr = np.asarray(data, dtype=float)
        except Exception:
            arr = np.array([])

        if arr.size == 0 or arr.ndim < 2:
            ax.text(0.5, 0.5, "No residual data", ha="center", va="center")
            ax.set_axis_off()
            self.canvas.draw()
            return

        arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
        if not np.isfinite(arr).all():
            arr = np.nan_to_num(arr)

        if arr.shape[0] == 0 or arr.shape[1] == 0:
            ax.text(0.5, 0.5, "No residual data", ha="center", va="center")
            ax.set_axis_off()
            self.canvas.draw()
            return

        plot_arr = arr
        x_extent = None
        if time is not None:
            time_arr = np.asarray(time, dtype=float)
            if len(time_arr) == arr.shape[0]:
                plot_arr = arr.T
                x_extent = [float(time_arr.min()), float(time_arr.max())]
            elif len(time_arr) == arr.shape[1]:
                x_extent = [float(time_arr.min()), float(time_arr.max())]

        vmin = float(np.nanmin(plot_arr))
        vmax = float(np.nanmax(plot_arr))
        if np.isclose(vmin, vmax):
            vmin -= 0.1
            vmax += 0.1

        if x_extent is not None:
            im = ax.imshow(
                plot_arr,
                cmap="rainbow",
                origin="lower",
                aspect="auto",
                extent=[x_extent[0], x_extent[1], 0, plot_arr.shape[0]],
                vmin=vmin,
                vmax=vmax,
            )
        else:
            im = ax.imshow(plot_arr, cmap="rainbow", origin="lower", aspect="auto", vmin=vmin, vmax=vmax)

        ax.set_xlabel("time", fontsize=7, fontweight="bold")
        ax.set_ylabel("wl", fontsize=7, fontweight="bold")
        ax.tick_params(axis="both", labelsize=6, width=1.0, labelcolor="black")
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontweight("bold")

        cbar = self.figure.colorbar(im, ax=ax, fraction=0.045, pad=0.03)
        cbar.ax.tick_params(labelsize=6, width=1.0, labelcolor="black")
        for label in cbar.ax.get_yticklabels():
            label.set_fontweight("bold")
        cbar.ax.yaxis.label.set_fontsize(7)
        cbar.ax.yaxis.label.set_fontweight("bold")

        self.figure.subplots_adjust(left=0.12, right=0.94, bottom=0.15, top=0.96)
        self.canvas.draw()