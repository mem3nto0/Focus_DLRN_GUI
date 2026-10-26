import os
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QGridLayout, QRadioButton, QPushButton, QLineEdit,
    QMessageBox, QFileDialog, QLabel, QCheckBox, QSpinBox
)
from tensorflow.keras.models import Model, load_model # type: ignore
import tensorflow as tf

class LoadWidget(QWidget):
    """
    A widget for loading pre-trained machine learning models.
    
    This widget provides a user interface for selecting and loading TensorFlow Keras models 
    from the file system. It includes a radio button for activation, a read-only text field 
    displaying the selected model path, and buttons for loading and clearing the selection.
    
    Attributes:
        model_file_path (str | None): Path to the selected model file, or None if no model is selected.
    """
    model_file_path: str | None

    def __init__(self, parent=None):
        """
        Initialize the LoadWidget.
        
        Creates the UI elements for model selection and loading, including a radio button,
        text field for the file path, and buttons for loading and clearing.
        
        Args:
            parent (QWidget, optional): Parent widget. Defaults to None.
        """
        super().__init__(parent)

        self.model_file_path = None
        self.train_validation_widget = parent

        layout = QGridLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        self.radio_button = QRadioButton("Load an existing model")
        layout.addWidget(self.radio_button, 0, 0)

        self.model_label = QLineEdit(placeholderText="Path to the model file", readOnly=True)
        layout.addWidget(self.model_label, 2, 0, 1, 3)

        self.spectrum_load_button = QPushButton("Load model")
        self.spectrum_load_button.pressed.connect(self.select_model_path)
        layout.addWidget(self.spectrum_load_button, 2, 3)

        self.spectrum_clear_button = QPushButton("Clear")
        self.spectrum_clear_button.pressed.connect(self.clear_model_path)
        layout.addWidget(self.spectrum_clear_button, 2, 4)

        self.gpu_checkbox = QCheckBox("Computational settings")
        layout.addWidget(self.gpu_checkbox, 1, 0, 1, 2)

        self.gpu_label = QLabel("GPU")
        layout.addWidget(self.gpu_label, 1, 1)
        self.gpu_spinbox = QSpinBox()
        self.gpu_spinbox.setRange(0, 16)
        layout.addWidget(self.gpu_spinbox, 1, 2)

        self.workers_label = QLabel("Workers")
        layout.addWidget(self.workers_label, 1, 3)
        self.workers_spinbox = QSpinBox()
        self.workers_spinbox.setRange(1, 64)
        layout.addWidget(self.workers_spinbox, 1, 4)

        self.gpu_checkbox.toggled.connect(self._update_optional_settings_state)
        self._update_optional_settings_state()

        self.setLayout(layout)

    def select_model_path(self):
        """
        Open a file dialog to select a model file.
        
        Updates the model_file_path attribute and the text in the
        corresponding QLineEdit when a valid file is selected.
        """
        dialog = QFileDialog(self, "Select a spectrum file")
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        if dialog.exec():
            path = dialog.selectedFiles()[0]
            if self.valid_path(path):
                self.model_file_path = path
                self.model_label.setText(path)

                try:
                    #loaded_model = self.load_model(path)
                    if self.train_validation_widget is not None: #and loaded_model is not None
                        self.train_validation_widget.model_path = self.model_file_path 
                        if self.train_validation_widget.analysis_input is not None:
                            if self.gpu_checkbox.isChecked():
                                self.train_validation_widget.analysis_input.workers = int(self.workers_spinbox.value())
                                self.train_validation_widget.analysis_input.GPU = int(self.gpu_spinbox.value())
                        self.train_validation_widget.toggle_navigation_buttons_enabled.emit(
                            self.train_validation_widget.model_path is not None
                        )
                except Exception:
                    QMessageBox.critical(
                        self, "Load model - Loading failed",
                        f"Failed to load model from '{path}'"
                    )

    def clear_model_path(self):
        """
        Clear the currently selected model path.
        
        Resets the model_file_path attribute to None and clears the text
        in the model path display field.
        """
        if self.model_file_path:
            self.model_file_path = None
            self.model_label.setText("")
            if self.train_validation_widget is not None:
                self.train_validation_widget.model_path = None
                self.train_validation_widget.toggle_navigation_buttons_enabled.emit(False)

    def isChecked(self) -> bool:
        """
        Check if the widget's radio button is checked.
        
        Returns:
            bool: True if the radio button is checked, False otherwise.
        """ 
        return self.radio_button.isChecked()

    def _update_optional_settings_state(self):
        self.gpu_label.setEnabled(self.gpu_checkbox.isChecked() and self.radio_button.isChecked())
        self.gpu_spinbox.setEnabled(self.gpu_checkbox.isChecked() and self.radio_button.isChecked())
        self.workers_label.setEnabled(self.gpu_checkbox.isChecked() and self.radio_button.isChecked())
        self.workers_spinbox.setEnabled(self.gpu_checkbox.isChecked() and self.radio_button.isChecked())

    def toggle_enabled(self, enabled: bool):
        """
        Enable or disable the widget components.
        
        Controls the enabled state of the text field and buttons.
        The radio button state is not affected.
        
        Args:
            enabled (bool): True to enable the components, False to disable them.
        """
        self.radio_button.setEnabled(True)
        self.model_label.setEnabled(enabled)
        self.spectrum_load_button.setEnabled(enabled)
        self.spectrum_clear_button.setEnabled(enabled)
        self.gpu_checkbox.setEnabled(enabled)
        self._update_optional_settings_state()

    def setChecked(self, checked: bool):
        """
        Set the checked state of the widget's radio button.
        
        Args:
            checked (bool): The state to set the radio button to.
        """
        self.radio_button.setChecked(checked)

    # def load_model(self, path: str | None = None) -> Model | None:
    #     """
    #     Load the selected TensorFlow Keras model.
        
    #     Attempts to load the model from the selected file path using Keras's
    #     load_model function. Shows an error message if no model is selected
    #     or if loading fails.
        
    #     Returns:
    #         Model | None: The loaded Keras model if successful, None otherwise.
    #     """
    #     target_path = path or self.model_file_path

    #     if not target_path:
    #         QMessageBox.critical(
    #             self, f"Load model - No model loaded",
    #             f"No model has been selected."
    #         )
    #         return None

    #     try:
    #         loaded_model = tf.keras.models.load_model(target_path, compile=False)
    #         self.model_file_path = target_path
    #         self.model_path = loaded_model
    #         return loaded_model
    #     except Exception:
    #         QMessageBox.critical(
    #             self, f"Load model - Loading failed",
    #             f"Failed to load model from '{target_path}'"
    #         )
    #         return None

    def valid_path(self, path: str | None) -> bool:
        """
        Validate if the given path points to a valid file.
        
        Checks if the path exists, is not empty, and is not a directory.
        Shows appropriate error messages if validation fails.
        
        Args:
            path (str | None): The file path to validate.
            
        Returns:
            bool: True if the path is valid, False otherwise.
        """
        if not path:
            QMessageBox.critical(
                self, f"Load model - Invalid path",
                f"No path given."
            )
            return False

        elif not os.path.exists(path):
            QMessageBox.critical(
                self, f"Load model - Invalid path",
                f"Path does not exist."
            )
            return False
        elif os.path.isdir(path):
            QMessageBox.critical(
                self, f"Load model - Invalid path",
                f"Expected path to a file, but points to a directory: {path}"
            )
            return False
        return True
