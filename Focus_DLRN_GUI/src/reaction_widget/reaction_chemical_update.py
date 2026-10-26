from uuid import UUID
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLineEdit, QFileDialog, QLabel, QMessageBox, QCheckBox
from PySide6.QtCore import Signal
from PySide6.QtGui import QDoubleValidator

from .reaction_chemical import Chemical, Plus

class ChemicalUpdateWidget(QWidget):
    """
    A widget for updating the label and spectrum path of a selected Chemical.
    
    Emits:
        signal_remove_selected (UUID): Emitted when the selected chemical is removed.
    """
    selected_node: Chemical|Plus|None
    spectrum_path: str|None
    signal_remove_selected = Signal(UUID)

    def __init__(self,global_widget, parent=None): 
        """
        Initializes the widget with input fields and action buttons.
        """
        super().__init__(parent)
        self.selected_node = None
        self.spectrum_path = None
        self.setMinimumWidth(200)
        self.global_widget = global_widget

        self.label_input = QLineEdit(placeholderText="Chemical name")
        self.concentration_input = QLineEdit(placeholderText="Chemical concentration")
        #self.update_concentration_input_state()
        
        # Elements for loading a spectrum
        self.spectrum_path_label = QLineEdit(placeholderText="Path to spectrum (Optional)", readOnly=True)
        self.spectrum_path_button = QPushButton("Load")
        spec_load_layout = QHBoxLayout()
        self.spectrum_path_button.pressed.connect(self.load_spectrum)
        spec_load_layout.addWidget(self.spectrum_path_label, stretch=3)
        spec_load_layout.addWidget(self.spectrum_path_button, stretch=1)

        self.is_active_checkbox = QCheckBox("Is active")
        self.is_active_checkbox.setChecked(True)

        self.confirm_button = QPushButton("Update")
        self.confirm_button.pressed.connect(self.pass_info_to_selected)
        
        self.remove_button = QPushButton("Remove")
        self.remove_button.pressed.connect(self.remove_chemical)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Chemical name:"))
        layout.addWidget(self.label_input)
        layout.addWidget(QLabel("Concentration:"))
        layout.addWidget(self.concentration_input)
        layout.addWidget(QLabel("Spectrum:"))
        layout.addLayout(spec_load_layout)
        layout.addWidget(QLabel("Spectrum is active:"))
        layout.addWidget(self.is_active_checkbox)
        layout.addSpacing(20)
        layout.addWidget(self.confirm_button)
        layout.addWidget(self.remove_button)
        self.setLayout(layout)

        self.set_elements_enabled(False)


    def change_selected(self, selected: Chemical|None):
        """
        Sets the current selected chemical and populates the input fields.

        Args:
            selected (Chemical | None): The selected chemical to edit.
        """
        self.label_input.clear()
        self.concentration_input.clear()
        self.spectrum_path_label.clear()

        self.selected_node = selected

        if self.selected_node and type(self.selected_node) == Chemical:
            self.label_input.setText(self.selected_node.label)
            self.concentration_input.setText(str(self.selected_node.concentration))
            if self.selected_node.spectrum_path:
                self.spectrum_path_label.setText(self.selected_node.spectrum_path)
            self.is_active_checkbox.setChecked(self.selected_node.is_active)
            self.set_elements_enabled(True)

        elif self.selected_node and type(self.selected_node) == Plus:
            self.set_elements_enabled(False)
            self.remove_button.setEnabled(True)

        else:
            self.set_elements_enabled(False)

    def set_elements_enabled(self, enable: bool):
        """
        Iterates through all sub-widget and Enables or Disables them based on the given bool.
        """
        if not enable: 
            self.is_active_checkbox.setChecked(False)
        for widget in [
            self.label_input,
            self.concentration_input,
            self.spectrum_path_label,
            self.spectrum_path_button,
            self.confirm_button,
            self.remove_button,
            self.is_active_checkbox
        ]:
            widget.setEnabled(enable)

    def pass_info_to_selected(self):
        """
        Updates the selected chemical's label and spectrum path based on user input.
        """
        if self.selected_node and type(self.selected_node) == Chemical:
            new_label = self.label_input.text()
            if len(new_label)==0 or new_label == self.selected_node.label:
                new_label = None

            new_concentration = self.get_concentration_input()
            new_spectrum_path = self.spectrum_path

            self.selected_node.update_info(
                new_label,
                new_concentration,
                new_spectrum_path,
                self.is_active_checkbox.isChecked()
            )
    
    def get_concentration_input(self) -> float|None:
        new_concentration_str = self.concentration_input.text()
        if len(new_concentration_str) > 0:
            try:
                return float(new_concentration_str)
            except ValueError:
                QMessageBox.critical(
                    self, "Invalid concentration",
                    f"Invalid concentration provided: {new_concentration_str}"
                )
        return None

    def remove_chemical(self):
        """
        Emits a signal to remove the selected chemical and clears the input fields.
        """
        if self.selected_node:
            self.signal_remove_selected.emit(self.selected_node.node_id)
            self.spectrum_path = None
            self.change_selected(None)

    def load_spectrum(self):
        if self.selected_node:
            dialog = QFileDialog(self, "Load spectrum file")
            dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
            # dialog.setNameFilter("TXT files (*.txt)")
            if dialog.exec():
                path = dialog.selectedFiles()[0]
                self.spectrum_path = path
                self.spectrum_path_label.setText(path)
    # def update_concentration_input_state(self):
    #     print(self.global_widget.min_max_conc)
    #     if self.global_widget.min_max_conc !=None:
    #         self.concentration_input.setPlaceholderText("In this setting not available")
    #         self.concentration_input.setReadOnly(True)
    #         self.concentration_input.setStyleSheet("color: gray;")

    #         self.concentration_input.setText("In this setting not available")
    #     else:
    #         self.concentration_input.setReadOnly(False)
    #         self.concentration_input.setStyleSheet("") 


                
