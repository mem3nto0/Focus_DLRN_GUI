import os

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy

from .result_concentration_trace_widget import ResultConcTraceWidget
from .result_residual_widget import ResultResidualsWidget
from .result_residual_widget_low_wl import ResultResidualsWidget_Low_wl


class SingleAnalysisWidget(QWidget):
    def __init__(
        self,
        model_probability: float = 0.0,
        residual_sum: float = 0.0,
        residual_mean: float = 0.0,
        residual=None,
        concentration_traces=None,
        rate_constants=None,
        tau_values=None,
        reaction_string=None,
        time=None,
        used_kinetic_labels=None,
        reconstructed_signal=None,
        input_data=None,
        chem_name_to_label_dict=None,
        parent=None,
    ):
        super().__init__(parent)
        self.model_probability = float(model_probability)
        self.residual_sum = residual_sum
        self.residual_mse = residual_mean
        self.residual = residual
        self.concentration_traces = concentration_traces
        self.rate_constants = rate_constants if rate_constants is not None else []
        self.tau_values = tau_values if tau_values is not None else []
        self.reaction_string = reaction_string if reaction_string is not None else []
        self.time = time
        self.used_kinetic_labels = used_kinetic_labels
        self.reconstructed_signal = reconstructed_signal
        self.input_data = input_data
        self.chem_name_to_label_dict = chem_name_to_label_dict if chem_name_to_label_dict is not None else {}
        self.subreaction_table = self._build_subreaction_table()

        self.result_residuals_widget = None
        self.result_conc_traces_widget = None
        self.initUI()

    def _create_residual_widget(self):
        if self._use_low_wl_residual_widget():
            widget = ResultResidualsWidget_Low_wl(self)
            if self.reconstructed_signal is not None and self.input_data is not None and self.time is not None:
                widget.plot(np.asarray(self.reconstructed_signal), self.time, self.input_data)
            return widget

        widget = ResultResidualsWidget(self)
        if self.residual is not None:
            widget.plot(np.asarray(self.residual))
        return widget

    def _normalise_value(self, value):
        if isinstance(value, (list, tuple, np.ndarray)):
            if len(value) == 0:
                return 0.0
            value = value[0]
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
        
    def reaction_string_renaming(self):
        new_reac_string = []
        label_map = self.chem_name_to_label_dict if self.chem_name_to_label_dict is not None else {}
        for substring in self.reaction_string:
            new_sub = " ".join(label_map.get(token, token) for token in substring.split())
            new_reac_string.append(new_sub)
        return new_reac_string

    def _build_subreaction_table(self):
        reaction_rows = self.reaction_string_renaming()
        tau_values = self.tau_values if isinstance(self.tau_values, (list, tuple, np.ndarray)) else [self.tau_values]
        rate_values = self.rate_constants if isinstance(self.rate_constants, (list, tuple, np.ndarray)) else [self.rate_constants]

        rows = []
        n_rows = min(len(reaction_rows), len(tau_values), len(rate_values))

        for idx in range(n_rows):
            tau_value = self._normalise_value(tau_values[idx])
            rate_value = self._normalise_value(rate_values[idx])
            if np.isclose(rate_value, 0.0):
                continue
            rows.append([
                str(reaction_rows[idx]),
                f"{tau_value:.6g}",
                f"{rate_value:.6g}",
            ])

        return rows if rows else [["-", "-", "-"]]

    def _get_placeholder_pixmap(self, title: str, color: str = "#e6edf7") -> QPixmap:
        pixmap = QPixmap(420, 220)
        pixmap.fill(QColor("#f7f7f7"))

        painter = QPainter(pixmap)
        painter.setPen(QColor("#b9c5d4"))
        painter.setBrush(QColor(color))
        painter.drawRect(10, 10, pixmap.width() - 20, pixmap.height() - 20)

        painter.setPen(QColor("#333333"))
        painter.setFont(self.font())
        painter.drawText(
            0,
            0,
            pixmap.width(),
            pixmap.height(),
            Qt.AlignmentFlag.AlignCenter,
            title,
        )
        painter.end()
        return pixmap

    def _get_wavelength_count(self) -> int:
        if self.input_data is None:
            return 0

        if hasattr(self.input_data, "columns"):
            columns = [col for col in self.input_data.columns if str(col) != "Time"]
            return len(columns)

        if isinstance(self.input_data, np.ndarray):
            return self.input_data.shape[1] if self.input_data.ndim > 1 else 0

        return 0

    def _use_low_wl_residual_widget(self) -> bool:
        return self._get_wavelength_count() < 10

    def _build_image_panel(self, label_text: str, pixmap: QPixmap | None = None, panel_title: str = "", plot_widget: QWidget | None = None) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        title_label = QLabel(panel_title)
        title_label.setStyleSheet("font-size: 12px; font-weight: 700;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        frame = QWidget()
        frame.setMinimumSize(420, 220)
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        frame.setStyleSheet("border: 1px solid #cfcfcf; background: white;")

        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSpacing(0)

        if plot_widget is not None:
            plot_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            frame_layout.addWidget(plot_widget, stretch=1)
        else:
            image_label = QLabel()
            image_label.setFixedSize(420, 220)
            image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            image_label.setStyleSheet("border: none; background: transparent;")

            if pixmap is None:
                pixmap = self._get_placeholder_pixmap(label_text)
            image_label.setPixmap(pixmap.scaled(420, 220, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            frame_layout.addWidget(image_label)

        layout.addWidget(frame)
        return panel

    def _build_stats_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        def make_metric_block(label_text: str, value_text: str, label_font_size: int = 12, value_font_size: int = 12):
            block = QWidget()
            block_layout = QVBoxLayout(block)
            block_layout.setContentsMargins(0, 0, 0, 0)
            block_layout.setSpacing(2)
            block_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            label = QLabel(label_text)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet(f"font-size: {label_font_size}px; font-weight: 700;")

            value = QLabel(value_text)
            value.setAlignment(Qt.AlignmentFlag.AlignCenter)
            value.setStyleSheet(f"font-size: {value_font_size}px; font-weight: 600;")

            block_layout.addWidget(label)
            block_layout.addWidget(value)
            return block

        layout.addStretch(1)
        layout.addWidget(make_metric_block("Predicted likelihood:", f"{self.model_probability:.2f}%"), alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(make_metric_block("Residual sum:", f"{float(self.residual_sum):.3f}", 11, 11), alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(make_metric_block("Residual mean:", f"{float(self.residual_mse):.3f}", 11, 11), alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch(1)
        return panel

    def _build_table(self) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Subreaction", "Tau", "k"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        table.setMinimumHeight(180)

        rows = self.subreaction_table if self.subreaction_table else [["-", "-", "-"]]

        table.setRowCount(len(rows))
        for row_idx, row in enumerate(rows):
            for col_idx, value in enumerate(row[:3]):
                table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))

        return table

    def save_residual_image(self, output_dir: str, file_name: str | None = None):
        if not output_dir:
            return

        os.makedirs(output_dir, exist_ok=True)
        if file_name is None:
            file_name = "residual_plot.png"

        save_path = os.path.join(output_dir, file_name)
        if self.result_residuals_widget is not None and hasattr(self.result_residuals_widget, "figure"):
            self.result_residuals_widget.figure.tight_layout()
            self.result_residuals_widget.canvas.draw()
            self.result_residuals_widget.figure.savefig(save_path, dpi=200, bbox_inches="tight")

    def save_concentration_trace_image(self, output_dir: str, file_name: str | None = None):
        if not output_dir:
            return

        os.makedirs(output_dir, exist_ok=True)
        if file_name is None:
            file_name = "concentration_traces.png"

        save_path = os.path.join(output_dir, file_name)
        if self.result_conc_traces_widget is not None and hasattr(self.result_conc_traces_widget, "figure"):
            self.result_conc_traces_widget.figure.tight_layout()
            self.result_conc_traces_widget.canvas.draw()
            self.result_conc_traces_widget.figure.savefig(save_path, dpi=200, bbox_inches="tight")

    def initUI(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        self.result_residuals_widget = self._create_residual_widget()
        self.result_conc_traces_widget = ResultConcTraceWidget(self)

        if self.concentration_traces is not None:
            traces = np.asarray(self.concentration_traces)
            self.result_conc_traces_widget.plot(traces, self.time, self.used_kinetic_labels)

        panel_title = "Reconstructed Signal" if self._use_low_wl_residual_widget() else "Residual"
        top_row_layout = QHBoxLayout()
        summary_panel = self._build_stats_panel()
        residual_panel = self._build_image_panel("Residual", panel_title=panel_title, plot_widget=self.result_residuals_widget)
        top_row_layout.addWidget(summary_panel, stretch=1)
        top_row_layout.addWidget(residual_panel, stretch=4)
        main_layout.addLayout(top_row_layout)

        table = self._build_table()
        main_layout.addWidget(table)

    def fill_with_data(self):
        self.subreaction_table = self._build_subreaction_table()
        if self.result_residuals_widget is not None:
            if self._use_low_wl_residual_widget():
                if self.reconstructed_signal is not None and self.input_data is not None and self.time is not None:
                    self.result_residuals_widget.plot(np.asarray(self.reconstructed_signal), self.time, self.input_data)
            elif self.residual is not None:
                self.result_residuals_widget.plot(np.asarray(self.residual))
        self.update()

