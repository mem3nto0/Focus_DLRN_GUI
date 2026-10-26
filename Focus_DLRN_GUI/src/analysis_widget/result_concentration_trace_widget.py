import numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure


class ResultConcTraceWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.figure = Figure(figsize=(5.8, 3.4), dpi=120)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.canvas.setMinimumSize(540, 260)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def plot(self, data: list[list[float]],time:list[float], names: list[str]):
        self.figure.clear()
        ax = self.figure.add_axes([0.12, 0.15, 0.78, 0.72])

        arr = np.asarray(data, dtype=float)
        arr = arr.T
      
        arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)

        for idx in range(min(arr.shape[0], len(names))):
            ax.plot(time,arr[idx], label=names[idx])

        if ax.lines:
            legend = ax.legend(loc="upper right")
            if legend is not None:
                legend.set_title(None)
                for text in legend.get_texts():
                    text.set_fontsize(8)
                    text.set_fontweight("bold")

        ax.set_xlabel("time", fontsize=7, fontweight="bold")
        ax.set_ylabel("concentration", fontsize=7, fontweight="bold")
        ax.tick_params(axis="both", labelsize=6, width=1.0, labelcolor="black")
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontweight("bold")
        ax.set_ylim(0,np.max(arr)+1)
        ax.set_xlim(0,max(time))
        self.figure.subplots_adjust(left=0.12, right=0.97, bottom=0.15, top=0.95)
        self.canvas.draw()

