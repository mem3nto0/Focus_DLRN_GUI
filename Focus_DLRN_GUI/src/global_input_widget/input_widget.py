from PySide6.QtWidgets import QWidget, QPushButton, QGridLayout, QLineEdit, QCheckBox, QFileDialog, QMessageBox, QLabel, QFrame, QSpinBox
from PySide6.QtCore import Qt
import os
import numpy as np
import pandas as pd

from .spectrum_display import Matrix2dWidget

class QHLine(QFrame):
    """
    Horizontal line. Taken from: https://stackoverflow.com/questions/5671354/how-to-programmatically-make-a-horizontal-line-in-qt
    """
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFrameShadow(QFrame.Shadow.Sunken)


class GlobalInputWidget(QWidget):
    """
    A widget for handling global input parameters for spectrum analysis.
    
    This widget provides a user interface for specifying:
    * Path to the time-resolved spectrum file
    * Path to the output directory for saving results
    * Whether the data represents transient absorption
    * Path to an existing model file (optional)
    
    Attributes:
        spectrum_file_path (str or None): Path to the selected spectrum file
        output_dir_path (str or None): Path to the selected output directory
        is_transient_absorption (bool): Flag indicating if data is transient absorption
        model_file_dir (str or None): Path to an existing model file if specified
    """
    data_file_path: str | None
    output_dir_path: str | None
    is_transient_absorption: bool
    model_file_dir: str | None

    spectrum_data: list[list[float]] | None
    timescale_data: list[float] | None

    def __init__(self, parent = None):
        super().__init__(parent)
        self.initUI()
        
        self.data_file_path = None
        self.output_dir_path = None
        self.is_transient_absorption = False
        self.model_file_dir = None

        self.data = None



    def initUI(self):
        """
        Set up the user interface components.
        
        Creates and arranges all UI elements including text fields, buttons, and checkbox
        with appropriate connections to handler methods.
        """
        layout = QGridLayout()

        # --- first part: Loading spectrum ---
        self.data_label = QLineEdit(placeholderText="Path to the data file (.csv/.tsv/.xlsx)", readOnly=True)
        layout.addWidget(self.data_label, 0, 0)

        self.data_load_button = QPushButton("Load data")
        self.data_load_button.pressed.connect(self.select_data_path)
        layout.addWidget(self.data_load_button, 0, 1)

        self.data_clear_button = QPushButton("Clear")
        self.data_clear_button.pressed.connect(self.clear_data_path)
        layout.addWidget(self.data_clear_button, 0, 2)

        self.spectrum_display = Matrix2dWidget()
        layout.addWidget(self.spectrum_display, 1, 0, 1, -1)

        layout.addWidget(QHLine(), 2, 0, 1, -1)

        self.spectrum_index_label = QLabel("Spectrum index:")
        layout.addWidget(self.spectrum_index_label, 3, 0)

        self.spectrum_index_spinbox = QSpinBox()
        self.spectrum_index_spinbox.setMinimum(1)
        self.spectrum_index_spinbox.setMaximum(1)
        self.spectrum_index_spinbox.valueChanged.connect(self._on_spectrum_index_changed)
        layout.addWidget(self.spectrum_index_spinbox, 3, 1)

        layout.addWidget(QHLine(), 4, 0, 1, -1)

        # --- third part : Concentration min and max ---
        #self.concentration_active = QCheckBox("Use concentration")
        #self.concentration_active.checkStateChanged.connect(self.update_concentration_active)
        #layout.addWidget(self.concentration_active, 6, 0)

        #self.concentration_min = QLineEdit()
        #self.concentration_min.setPlaceholderText("Concentration min")
        #self.concentration_min.setEnabled(False)
        #layout.addWidget(self.concentration_min, 6, 1)

        #self.concentration_max = QLineEdit()
        #self.concentration_max.setPlaceholderText("Concentration max")
        #self.concentration_max.setEnabled(False)
       # layout.addWidget(self.concentration_max, 6, 2)


        #layout.addWidget(QHLine(), 7, 0, 1, -1)

        # --- fifth part: Selecting output directory ---
        self.output_label = QLineEdit(placeholderText="Path to the output directory", readOnly=True)
        layout.addWidget(self.output_label, 8, 0)

        self.output_load_button = QPushButton("Select output directory")
        self.output_load_button.pressed.connect(self.select_output_dir)
        layout.addWidget(self.output_load_button, 8, 1)

        self.output_clear_button = QPushButton("Clear")
        self.output_clear_button.pressed.connect(self.clear_output)
        layout.addWidget(self.output_clear_button, 8, 2)

        layout.addWidget(QHLine(), 9, 0, 1, -1)

        # --- sixth part: Selecting transient absorption ---
        self.checkbox_trans_abs = QCheckBox("Transient absorption")
        self.checkbox_trans_abs.stateChanged.connect(self.update_trans_abs_state)
        layout.addWidget(self.checkbox_trans_abs, 10, 0, 1, -1, Qt.AlignmentFlag.AlignHCenter)

        # # --- seventh row: Selecting an existing model ---
        # self.model_label = QLineEdit(placeholderText="Path to an existing model directory (optional)", readOnly=True)
        # layout.addWidget(self.model_label, 6, 0)

        # self.model_load_button = QPushButton("Load model")
        # self.model_load_button.pressed.connect(self.select_model_dir)
        # layout.addWidget(self.model_load_button, 6, 1)

        # self.model_clear_button = QPushButton("Clear")
        # self.model_clear_button.pressed.connect(self.clear_model)
        # layout.addWidget(self.model_clear_button, 6, 2)

        self.setLayout(layout)


    def select_data_path(self):
        """
        Open a file dialog to select the spectrum file.
        
        Updates the spectrum_file_path attribute and updates the text in the
        corresponding QLineEdit when a file is selected.
        """
        dialog = QFileDialog(self, "Select a data file")
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        if dialog.exec():
            path = dialog.selectedFiles()[0]
            if self.valid_path(path, True, "Data file"):
                self.data_file_path = path
                self.data_label.setText(path)

                self.data = load_data(path)
                self.raw_data = self.data.copy()
                self.cut_index = None

                spectrum_data = np.transpose(self.data.iloc[:, 1:].values).tolist()
                timescale_data = self.data["Time"].tolist()
                self.spectrum_display.plot(spectrum_data, timescale_data, selected_spectrum_index=0)
                self.spectrum_index_spinbox.setRange(1, max(1, len(spectrum_data)))
                self.spectrum_index_spinbox.setValue(1)

    def clear_data_path(self):
        if self.data_file_path:
            self.data_file_path = None
            self.data = None
            self.raw_data = None
            self.cut_index = None
            self.data_label.setText("")
            self.spectrum_index_spinbox.setRange(1, 1)
            self.spectrum_index_spinbox.setValue(1)
            self.spectrum_display.clear()

    def _on_spectrum_index_changed(self, value: int):
        if self.spectrum_display is None:
            return
        self.spectrum_display.set_selected_spectrum(max(0, value - 1))


    def select_output_dir(self):
        """
        Open a directory dialog to select the output directory.
        
        Updates the output_dir_path attribute and updates the text in the
        corresponding QLineEdit when a directory is selected.
        """
        dialog = QFileDialog(self, "Select an output directory")
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        if dialog.exec():
            path = dialog.selectedFiles()[0]
            if self.valid_path(path, False, "Output directory"):
                self.output_dir_path = path
                self.output_label.setText(path)

    def clear_output(self):
        if self.output_dir_path:
            self.output_dir_path = None
            self.output_label.setText("")


    def update_trans_abs_state(self):
        """
        Update the transient absorption flag based on checkbox state.
        
        Sets the is_transient_absorption attribute to True if the checkbox is checked,
        False otherwise.
        """
        self.is_transient_absorption = self.checkbox_trans_abs.isChecked()


    # def select_model_dir(self):
    #     """
    #     Open a file dialog to select an existing model file.
        
    #     Updates the model_file_dir attribute and updates the text in the
    #     corresponding QLineEdit when a file is selected.
    #     """
    #     dialog = QFileDialog(self, "Select a model file")
    #     dialog.setFileMode(QFileDialog.FileMode.Directory)
    #     if dialog.exec():
    #         path = dialog.selectedFiles()[0]
    #         self.model_file_dir = path
    #         self.model_label.setText(path)

    # def clear_model(self):
    #     if self.model_file_dir:
    #         self.model_file_dir = None
    #         self.model_label.setText("")


    def valid_path(self, path: str | None, file: bool, input_box: str) -> bool:
        """
        Validate if a given path exists and is of the correct type.
        
        Checks if the specified path exists and is of the correct type (file or directory).
        Displays an error message dialog if validation fails.
        
        Args:
            path (str or None): Path to check
            file (bool): True if the path should point to a file, False if it should point to a directory
            input_box (str): Description of the input for use in error messages
            
        Returns:
            bool: True if path is valid, False otherwise
            
        Side Effects:
            Shows error message dialogs if validation fails
        """
        if not path:
            QMessageBox.critical(
                self, f"{input_box} - Invalid path",
                f"No path given."
            )
            return False

        elif not os.path.exists(path):
            QMessageBox.critical(
                self, f"{input_box} - Invalid path",
                f"Path does not exist."
            )
            return False
        elif file and os.path.isdir(path):
            QMessageBox.critical(
                self, f"{input_box} - Invalid path",
                f"Expected path to a file, but points to a directory: {path}"
            )
            return False
        elif not file and os.path.isfile(path):
            QMessageBox.critical(
                self, f"{input_box} - Invalid path",
                f"Expected path to a directory, but points to a file: {path}"
            )
            return False

        return True


    def _apply_time_cut(self):
        if self.data is None or self.raw_data is None or self.spectrum_display is None:
            return

        marker_index = getattr(self.spectrum_display, "marker_index", None)
        if marker_index is None:
            self.data = self.raw_data.copy()
            return

        self.cut_index = int(marker_index)
        timescaleshift =  self.data["Time"].to_list()[self.cut_index]
        data = self.raw_data.iloc[self.cut_index:].copy()
        data["Time"]= data["Time"]-timescaleshift
        #print(data)
        self.data = data

    def get_current_state(self) -> tuple[pd.DataFrame, str, bool] | None:
        """
        Validate and return the current input state.
        
        Validates all paths and returns a tuple containing the current input values if all
        required inputs are valid. If validation fails, returns None.
        
        Returns:
            tuple or None: If all required paths are valid, returns a tuple containing:
                - spectrum_file_path (str): Path to the spectrum file
                - output_dir_path (str): Path to the output directory
                - is_transient_absorption (bool): Flag indicating if data is transient absorption
                - model_file_dir (str or None): Path to an existing model file if specified, otherwise None
                
            If any required path is invalid, returns None.
        """
        if self.data is None or self.data.empty:
            QMessageBox.critical(
                self, f"Missing input - data file",
                f"No data file provided!."
            )
            return None

        elif not self.output_dir_path:
            QMessageBox.critical(
                self, f"Missing input - Output directory",
                f"No ouput directory provided!."
            )
            return None

        self._apply_time_cut()

        return (
            self.data,
            self.output_dir_path,
            self.is_transient_absorption
        ) # type: ignore (self.valid_path checks if None)
    
    
    

def load_data(path: str) -> pd.DataFrame:
    ext = os.path.splitext(path)[1]
    if ext in ['.csv','.tsv']:
        data = pd.read_csv(path, delimiter=';')
    elif ext in [".xlsx", ".xls"]:
        data = pd.read_excel(path)
    else:
        raise Exception(f"Invalid file extension {ext}")

    return data


