import os

import numpy as np
import tensorflow as tf
from PySide6.QtWidgets import (
    QWidget, QGridLayout, QHBoxLayout, QRadioButton,
    QMessageBox, QLineEdit, QDoubleSpinBox, QSpinBox,
    QLabel, QPushButton, QCheckBox
)
from PySide6.QtCore import QThread, Qt
#from tensorflow.keras.models import Model # type: ignore
from .workers import TrainingWorker
from .user_input import TrainingInput, AnalysisInput


class TrainWidget(QWidget):
    """Widget for configuring and starting a new model training run."""

    trained_model_path: str | None
    worker: TrainingWorker | None
    worker_thread: QThread | None

    def __init__(self, parent=None):
        super().__init__(parent)

        self.trained_model_path = None
        self.worker = None
        self.worker_thread = None
        self.range_rows = []

        self._build_ui()

    def _build_ui(self):
        layout = QGridLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        self.radio_button = QRadioButton("Train a new model")
        layout.addWidget(self.radio_button, 0, 0)

        self.model_name_label = QLabel("Model name")
        layout.addWidget(self.model_name_label, 0, 1)

        self.model_name_input = QLineEdit()
        self.model_name_input.setPlaceholderText("my_model")
        layout.addWidget(self.model_name_input, 0, 2, 1, 3)

        self.min_concentration_label = QLabel("Min. concentration")
        layout.addWidget(self.min_concentration_label, 1, 0)
        self.min_concentration_input = QDoubleSpinBox()
        self.min_concentration_input.setRange(0, 100000)
        self.min_concentration_input.setDecimals(2)
        layout.addWidget(self.min_concentration_input, 1, 1)

        self.max_concentration_label = QLabel("Max. concentration")
        layout.addWidget(self.max_concentration_label, 1, 2)
        self.max_concentration_input = QDoubleSpinBox()
        self.max_concentration_input.setRange(0, 100000)
        self.max_concentration_input.setDecimals(2)
        layout.addWidget(self.max_concentration_input, 1, 3, 1, 2)

        self.tau_range_checkbox = QCheckBox("Training Tau range")
        layout.addWidget(self.tau_range_checkbox, 2, 0, 1, 2)

        self._build_tau_range_rows(layout)

        self.tau_range_checkbox.toggled.connect(self._toggle_tau_range_visibility)

        self.gpu_checkbox = QCheckBox("Computational settings")
        layout.addWidget(self.gpu_checkbox, 7, 0)

        self.gpu_label = QLabel("GPU")
        layout.addWidget(self.gpu_label, 7, 1)
        self.gpu_spinbox = QSpinBox()
        self.gpu_spinbox.setRange(0, 16)
        layout.addWidget(self.gpu_spinbox, 7, 2)

        self.workers_label = QLabel("Workers")
        layout.addWidget(self.workers_label, 7, 3)
        self.workers_spinbox = QSpinBox()
        self.workers_spinbox.setRange(1, 64)
        layout.addWidget(self.workers_spinbox, 7, 4)

        self.batch_checkbox = QCheckBox("Batch settings")
        layout.addWidget(self.batch_checkbox, 8, 0)

        self.n_batches_label = QLabel("N_batches")
        layout.addWidget(self.n_batches_label, 8, 1)
        self.n_batches_spinbox = QSpinBox()
        self.n_batches_spinbox.setRange(1, 100000)
        layout.addWidget(self.n_batches_spinbox, 8, 2)

        self.batch_size_label = QLabel("Batch size")
        layout.addWidget(self.batch_size_label, 8, 3)
        self.batch_size_spinbox = QSpinBox()
        self.batch_size_spinbox.setRange(1, 10000)
        layout.addWidget(self.batch_size_spinbox, 8, 4)

        self.start_button = QPushButton("Start Training")
        self.start_button.setMinimumHeight(32)
        self.start_button.setStyleSheet("font-size: 14px; font-weight: 600;")
        layout.addWidget(self.start_button, 9, 0, 1, 6, alignment=Qt.AlignmentFlag.AlignCenter)

        self.status_text = QLabel("Status: Select input")
        self.status_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_text.setStyleSheet("font-size: 13px; font-weight: 700;")
        layout.addWidget(self.status_text, 11, 0, 1, 6)

        self.model_accuracy_label = QLabel("Model accuracy")
        layout.addWidget(self.model_accuracy_label, 12, 0)
        self.model_accuracy_output = QLineEdit()
        self.model_accuracy_output.setPlaceholderText("--")
        self.model_accuracy_output.setReadOnly(True)
        self.model_accuracy_output.setEnabled(False)
        layout.addWidget(self.model_accuracy_output, 12, 1, 1, 2)

        self.tau_mape_label = QLabel("tau_MAPE")
        layout.addWidget(self.tau_mape_label, 12, 3)
        self.tau_mape_output = QLineEdit()
        self.tau_mape_output.setPlaceholderText("--")
        self.tau_mape_output.setReadOnly(True)
        self.tau_mape_output.setEnabled(False)
        layout.addWidget(self.tau_mape_output, 12, 4)

        self.gpu_checkbox.toggled.connect(self._update_optional_settings_state)
        self.batch_checkbox.toggled.connect(self._update_optional_settings_state)

        self.toggle_enabled(False)

    def _build_tau_range_rows(self, layout):
        for row_idx in range(3):
            row_index = 3 + row_idx

            row_container = QWidget()
            row_layout = QHBoxLayout(row_container)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(6)

            label_from = QLabel("From")
            value_from = QDoubleSpinBox()
            value_from.setRange(1, 600)
            value_from.setDecimals(6)

            label_to = QLabel("To")
            value_to = QDoubleSpinBox()
            value_to.setRange(1, 600)
            value_to.setDecimals(6)

            label_step = QLabel("Step")
            value_step = QDoubleSpinBox()
            value_step.setRange(0, 100)
            value_step.setDecimals(6)

            row_layout.addWidget(label_from)
            row_layout.addWidget(value_from)
            row_layout.addStretch(1)
            row_layout.addWidget(label_to)
            row_layout.addWidget(value_to)
            row_layout.addStretch(1)
            row_layout.addWidget(label_step)
            row_layout.addWidget(value_step)

            layout.addWidget(row_container, row_index, 1, 1, 6)

            self.range_rows.append({
                "label_from": label_from,
                "value_from": value_from,
                "label_to": label_to,
                "value_to": value_to,
                "label_step": label_step,
                "value_step": value_step,
                "widgets": [label_from, value_from, label_to, value_to, label_step, value_step],
            })

    def isChecked(self) -> bool:
        return self.radio_button.isChecked()

    def setChecked(self, checked: bool):
        self.radio_button.setChecked(checked)

    def toggle_enabled(self, enabled: bool):
        self.radio_button.setEnabled(True)
        self.model_name_input.setEnabled(enabled)
        self.model_name_label.setEnabled(enabled)
        self.min_concentration_label.setEnabled(enabled)
        self.min_concentration_input.setEnabled(enabled)
        self.max_concentration_label.setEnabled(enabled)
        self.max_concentration_input.setEnabled(enabled)
        self.tau_range_checkbox.setEnabled(enabled)

        for row in self.range_rows:
            for widget in row["widgets"]:
                widget.setEnabled(enabled and self.tau_range_checkbox.isChecked())

        self.gpu_checkbox.setEnabled(enabled)
        self.gpu_label.setEnabled(enabled and self.gpu_checkbox.isChecked())
        self.gpu_spinbox.setEnabled(enabled and self.gpu_checkbox.isChecked())
        self.workers_label.setEnabled(enabled and self.gpu_checkbox.isChecked())
        self.workers_spinbox.setEnabled(enabled and self.gpu_checkbox.isChecked())

        self.batch_checkbox.setEnabled(enabled)
        self.n_batches_label.setEnabled(enabled and self.batch_checkbox.isChecked())
        self.n_batches_spinbox.setEnabled(enabled and self.batch_checkbox.isChecked())
        self.batch_size_label.setEnabled(enabled and self.batch_checkbox.isChecked())
        self.batch_size_spinbox.setEnabled(enabled and self.batch_checkbox.isChecked())

        self.start_button.setEnabled(enabled)
        self.status_text.setEnabled(enabled)
        self.model_accuracy_label.setEnabled(enabled)
        self.model_accuracy_output.setEnabled(enabled)
        self.tau_mape_label.setEnabled(enabled)
        self.tau_mape_output.setEnabled(enabled)

        self._update_optional_settings_state()

    def _update_optional_settings_state(self):
        self.gpu_label.setEnabled(self.gpu_checkbox.isChecked() and self.radio_button.isChecked())
        self.gpu_spinbox.setEnabled(self.gpu_checkbox.isChecked() and self.radio_button.isChecked())
        self.workers_label.setEnabled(self.gpu_checkbox.isChecked() and self.radio_button.isChecked())
        self.workers_spinbox.setEnabled(self.gpu_checkbox.isChecked() and self.radio_button.isChecked())

        self.n_batches_label.setEnabled(self.batch_checkbox.isChecked() and self.radio_button.isChecked())
        self.n_batches_spinbox.setEnabled(self.batch_checkbox.isChecked() and self.radio_button.isChecked())
        self.batch_size_label.setEnabled(self.batch_checkbox.isChecked() and self.radio_button.isChecked())
        self.batch_size_spinbox.setEnabled(self.batch_checkbox.isChecked() and self.radio_button.isChecked())

        for row in self.range_rows:
            for widget in row["widgets"]:
                widget.setEnabled(self.radio_button.isChecked() and self.tau_range_checkbox.isChecked())

    def _toggle_tau_range_visibility(self, checked: bool):
        for row in self.range_rows:
            for widget in row["widgets"]:
                widget.setEnabled(self.radio_button.isChecked() and checked)

    def set_status(self, status: str):
        self.status_text.setText(f"Status: {status}")

    def train_model(self, training_input: TrainingInput):
        self.training_input = training_input
        self.set_status("Training in process (might take a while)")
        self.worker_thread = QThread()
        self.worker = TrainingWorker(training_input)
        self.worker.moveToThread(self.worker_thread)

        self.worker_thread.started.connect(self.worker.train)
        #self.worker.process_updated.connect(self.update_progress)

        self.worker.training_finished.connect(self.handle_training_completed)
        self.worker.training_error.connect(self.handle_training_error)

        self.worker.training_finished.connect(self.worker_thread.quit)
        self.worker.training_error.connect(self.worker_thread.quit)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.start()

    @staticmethod
    def create_validation_data_from_dir(training_data_dir: str, max_samples: int = 1000):
        if not os.path.isdir(training_data_dir):
            raise FileNotFoundError(f"Training data folder not found: {training_data_dir}")

        file_names = sorted(
            file_name for file_name in os.listdir(training_data_dir)
            if file_name.endswith(".npz")
        )
        selected_files = file_names[: max_samples]

        if not selected_files:
            raise ValueError(f"No training samples found in {training_data_dir}")

        x_val_list = []
        y_model_list = []
        y_tau_list = []

        for file_name in selected_files:
            file_path = os.path.join(training_data_dir, file_name)
            with np.load(file_path) as sample:
                x_val_list.append(np.asarray(sample["train"], dtype=np.float32))
                y_model_list.append(np.asarray(sample["label1"], dtype=np.float32))
                y_tau_list.append(np.asarray(sample["label2"], dtype=np.float32))

        return (
            np.stack(x_val_list, axis=0),
            np.stack(y_model_list, axis=0),
            np.stack(y_tau_list, axis=0),
        )

    @staticmethod
    def evaluate_validation_predictions(y_true_model, y_pred_model, y_true_tau, y_pred_tau):
        y_true_model = np.asarray(y_true_model, dtype=np.float32)
        y_pred_model = np.asarray(y_pred_model, dtype=np.float32)
        y_true_tau = np.asarray(y_true_tau, dtype=np.float32)
        y_pred_tau = np.asarray(y_pred_tau, dtype=np.float32)

        accuracy = float(np.mean(np.argmax(y_pred_model, axis=1) == np.argmax(y_true_model, axis=1)))

        epsilon = np.finfo(np.float32).eps
        absolute_error = np.abs(y_true_tau - y_pred_tau)
        scale = np.maximum(np.abs(y_true_tau), epsilon)
        mape = float(np.mean(absolute_error / scale))

        return accuracy, mape

    def _validate_trained_model(self, model_path: str):
        if not model_path or not os.path.exists(model_path):
            self.set_status("Validation skipped: model file missing")
            return

        training_data_dir = os.path.join(self.training_input.output_path, "training_data")
        x_val, y_model_val, y_tau_val = self.create_validation_data_from_dir(training_data_dir, max_samples=1000)

        validation_path = os.path.join(self.training_input.output_path, "validation_data_1000.npz")
        np.savez_compressed(validation_path, x=x_val, y_model=y_model_val, y_tau=y_tau_val)

        model = tf.keras.models.load_model(model_path, compile=False)
        predictions = model.predict(x_val[..., np.newaxis], verbose=0)

        if isinstance(predictions, dict):
            model_predictions = np.asarray(predictions["output_1"], dtype=np.float32)
            tau_predictions = np.asarray(predictions["output_2"], dtype=np.float32)
        elif isinstance(predictions, (list, tuple)) and len(predictions) >= 2:
            model_predictions = np.asarray(predictions[0], dtype=np.float32)
            tau_predictions = np.asarray(predictions[1], dtype=np.float32)
        else:
            model_predictions = np.asarray(predictions, dtype=np.float32)
            tau_predictions = np.asarray(predictions, dtype=np.float32)

        accuracy, mape = self.evaluate_validation_predictions(
            y_model_val,
            model_predictions,
            y_tau_val,
            tau_predictions,
        )

        self.model_accuracy_output.setText(f"{accuracy:.4f}")
        self.tau_mape_output.setText(f"{mape:.4f}")
        self.set_status("Validation finished")

    def handle_training_completed(self, model):
        self.trained_model_path = model
        self.set_status("Training finished")
        if self.training_input is not None:
            self._validate_trained_model(model)

    def handle_training_error(self, error_message):
        self.set_status("Training failed")
        QMessageBox.critical(
            self, "Training failed",
            f"Failed to train a new model: {error_message}"
        )

    def get_model(self) -> str | None:
        return self.trained_model_path

    def collect_additional_training_inputs(self, training_input: TrainingInput, analysis_input: AnalysisInput | None = None):
        if training_input is None:
            return

        entered_model_name = self.model_name_input.text().strip()
        training_input.model_name = entered_model_name if entered_model_name else "my_model"
        training_input.min_conc = float(self.min_concentration_input.value())
        training_input.max_conc = float(self.max_concentration_input.value())

        if analysis_input is not None:
            analysis_input.model_name = entered_model_name if entered_model_name else "my_model"

        if self.tau_range_checkbox.isChecked():
            tau_lists = []
            for row in self.range_rows:
                start_value = float(row["value_from"].value())
                end_value = float(row["value_to"].value())
                step_value = float(row["value_step"].value())

                if step_value <= 0:
                    step_value = 1.0

                if end_value < start_value:
                    start_value, end_value = end_value, start_value

                tau_values = []
                current_value = start_value
                while current_value <= end_value + 1e-9:
                    tau_values.append(float(current_value))
                    current_value += step_value

                if tau_values:
                    tau_lists.append(tau_values)

            training_input.tau_lists = tau_lists if tau_lists else None
            if analysis_input is not None:
                analysis_input.tau_lists = tau_lists if tau_lists else None
        else:
            training_input.tau_lists = None
            if analysis_input is not None:
                analysis_input.tau_lists = None

        if self.batch_checkbox.isChecked():
            training_input.N_train_batch = int(self.n_batches_spinbox.value())
            training_input.batch_size = int(self.batch_size_spinbox.value())

        if self.gpu_checkbox.isChecked():
            training_input.workers = int(self.workers_spinbox.value())
            training_input.GPU = int(self.gpu_spinbox.value())
            if analysis_input is not None:
                analysis_input.workers = int(self.workers_spinbox.value())
                analysis_input.GPU = int(self.gpu_spinbox.value())

        training_input.full_spec_gen = True
