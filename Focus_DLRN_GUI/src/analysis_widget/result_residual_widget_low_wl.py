import numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import pandas as pd


class ResultResidualsWidget_Low_wl(QWidget):
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

    def plot(self, data: list[list[float]], time: list[float],input_data: pd.DataFrame):
        self.figure.clear()

        # Reserve space on the right for the legend
        ax = self.figure.add_axes([0.075, 0.18, 0.75, 0.72])

        input_data = input_data.drop(columns=["Time"])
        input_names = input_data.columns.to_list()

        input_array = input_data.values
        input_array = input_array / np.max(input_array)
        input_array = input_array.T

        arr = np.asarray(data, dtype=float).T

        for idx in range(len(input_names)):
            ax.plot(
                time, input_array[idx],
                label=input_names[idx],
                linewidth=1.0
            )
            ax.plot(
                time, arr[idx],
                linestyle="--",
                color="black",
                linewidth=0.8,
                label="Reconstructed" if idx == 0 else "_nolegend_"
            )

        # Legend outside the plot, on the right
        if ax.lines:
            legend = ax.legend(
                loc="center left",
                bbox_to_anchor=(1.01, 0.5),
                fontsize=6,
                handlelength=0.8,
                handletextpad=0.3,
                borderaxespad=0,
                labelspacing=0.4,
                frameon=False
            )

            for text in legend.get_texts():
                text.set_fontsize(6)
                text.set_fontweight("bold")

        ax.set_xlabel("time", fontsize=7, fontweight="bold", labelpad=2)
        ax.set_ylabel("norm. intensity", fontsize=7, fontweight="bold", labelpad=2)


        ax.tick_params(
            axis="both",
            labelsize=6,
            width=1.0,
            labelcolor="black"
        )

        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontweight("bold")

        y_max = max(float(np.max(arr)), float(np.max(input_array)))
        y_max = max(y_max * 1.12, 1.0)
        ax.set_ylim(0, y_max)

        # Make the plotted data reach the left and right borders
        ax.set_xlim(min(time), max(time))
        ax.margins(x=0, y=0.05)

        self.canvas.draw()