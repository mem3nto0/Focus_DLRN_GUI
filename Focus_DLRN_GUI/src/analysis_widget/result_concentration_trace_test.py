#%%%
import numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt



def plot(data: list[list[float]],time: list, component_names: list[str]):

    arr = np.asarray(data, dtype=float)

    if arr.ndim != 2:
        raise ValueError("data must be a 2D list of numeric values")

    arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)

    fig, ax = plt.subplots()

    names = (
        list(component_names)
        if component_names is not None
        else [f"Trace {idx + 1}" for idx in range(arr.shape[0])]
    )

    
    for idx in range(min(arr.shape[0], len(names))):
        ax.plot(time,arr[idx], label=names[idx])

    if ax.lines:
        ax.legend(loc="upper right")

    ax.set_xlabel("Time")
    ax.set_ylabel("Concentration")
    fig.tight_layout()


data = np.array([[1,2,3] for i in range(100)])
labels=["A","B","C"]
time = [i for i in range(100)]

plot(data.T,time,labels)

