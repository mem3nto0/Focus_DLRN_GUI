from PySide6.QtWidgets import (
    QWidget, QGridLayout, QButtonGroup, QMessageBox
)
from PySide6.QtCore import Signal

from .train_widget import TrainWidget
from .load_widget import LoadWidget
from .user_input import TrainingInput, AnalysisInput

class TrainValidateWidget(QWidget):
    """
    A widget that integrates model training and validation functionality.
    
    This widget serves as a control panel for machine learning model operations, 
    allowing users to either train a new model or load an existing one, and then
    validate it. It coordinates between training, loading, and validation components,
    manages the workflow states, and displays validation results.
    
    The widget provides:
    - Options to choose between training a new model or loading an existing one
    - A button to start the selected process
    - Display of validation metrics after validation is complete
    - Proper thread management for non-blocking UI during processing
    
    Attributes:
        perform_training (bool): Whether to train a new model (True) or load an existing one (False).
        model (Model | None): The current model being used, either trained or loaded.
        already_processed (bool): Flag indicating if validation has already been performed.
        toggle_navigation_buttons_enabled (Signal): Signal to enable/disable navigation buttons 
                                                  in the parent container.
    """
    perform_training: bool
    model_path: str | None
    already_processed: bool

    training_input: TrainingInput | None
    analysis_input: AnalysisInput | None

    toggle_navigation_buttons_enabled = Signal(bool)

    def __init__(self, parent=None):
        """
        Initialize the TrainValidateWidget.
        
        Sets up the initial state and calls initUI() to create the user interface.
        
        Args:
            parent (QWidget, optional): Parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.perform_training = True
        self.model_path = None
        self.already_processed = False

        self.training_input = None
        self.analysis_input = None

        self.initUI()

    def initUI(self):
        """
        Create and configure the user interface components.
        
        Sets up the layout with train/load option widgets, radio button logic,
        start button, and validation results display. Connects signals and slots
        for user interactions.
        """
        layout = QGridLayout()

        # Initialize the train / load widgets
        self.train_widget = TrainWidget()
        self.train_widget.setChecked(True)
        self.train_widget.toggle_enabled(True)
        self.train_widget.start_button.clicked.connect(self.start_training)
        layout.addWidget(self.train_widget,0,0,1,-1)

        self.load_widget = LoadWidget(self)
        self.load_widget.train_validation_widget = self
        self.load_widget.toggle_enabled(False)
        layout.addWidget(self.load_widget,1,0,1,-1)

        # Set up radio button logic
        self.button_group = QButtonGroup(self)
        self.button_group.addButton(self.train_widget.radio_button, 1)
        self.button_group.addButton(self.load_widget.radio_button, 2)
        self.button_group.buttonClicked.connect(self.on_radio_button_clicked)

        # The training widget contains the request-specific Start Training button.
        # The old parent-level start button has been removed to keep the form layout
        # focused on the train/load selection only.
        self.setLayout(layout)
        self.toggle_navigation_buttons_enabled.emit(False)

    def on_radio_button_clicked(self):
        """
        Handle radio button selection changes.
        
        Updates the UI state when the user switches between training and loading options.
        Enables/disables appropriate widgets and updates the start button text to
        reflect the selected operation.
        """
        train_widget_checked = self.train_widget.isChecked()

        self.train_widget.toggle_enabled(train_widget_checked)
        self.load_widget.toggle_enabled(not train_widget_checked)
        self.perform_training = train_widget_checked
        self.model_path = None
        self.toggle_navigation_buttons_enabled.emit(False)

        # No parent-level start button is used anymore; the train widget owns its own
        # start action and the load section remains unchanged.

    def load_data(
            self, 
            training_input: TrainingInput | None,
            analysis_input: AnalysisInput | None
        ):
        """
        Adds the data needed for training and/or validation to the object. This function
        is called when the user switches from the system model creation page (second page) to
        the training and validation page (third page).
        """
        self.training_input = training_input
        self.analysis_input = analysis_input

    def forget_data(self):
        self.training_input = None
        self.analysis_input = None


    def start_training(self):
        """
        Start the training and/or validation process.
        
        If training is selected, starts the training process in a background thread,
        followed by validation when training completes. If loading is selected,
        loads the model and proceeds directly to validation.
        
        If no validation data is found, shown an error message and returns. The same
        is done if model training is selected and no training data is found.

        If validation has already been performed, prompts the user to confirm
        whether they want to run the process again.
        """
        if not self.training_input:
            QMessageBox.critical(
                self, f"No training data found",
                f"No training input data found"
            )
            return

        # If the button is pressed again after validation was already completed
        if self.already_processed:
            # Give the user the option to not run the process again
            ret = QMessageBox.question(
                self, "Training already completed",
                "A training run is already finished. Do you want to run the process again?",
                buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                defaultButton=QMessageBox.StandardButton.No
            )
            if ret == QMessageBox.StandardButton.No:
                return
            
        self.train_widget.collect_additional_training_inputs(self.training_input, self.analysis_input)
        self.toggle_navigation_buttons_enabled.emit(False)

        if self.perform_training:
            if not self.training_input:
                QMessageBox.critical(
                    self, f"No training data found",
                    f"No training input data found"
                )
                return
            else:
                self.toggle_enabled_widgets_training(False)
                self.train_widget.train_model(self.training_input)
                self.train_widget.worker.training_finished.connect(self.on_training_completed) # type: ignore (worker properly set in train_model)
                self.train_widget.worker.training_error.connect(self.on_training_error) # type: ignore

        # else:
        #     self.model = self.load_widget.load_model()
        #     if self.model:
        #         if self.analysis_input is not None:
        #             if self.load_widget.gpu_checkbox.isChecked():
        #                 self.analysis_input.workers = int(self.load_widget.workers_spinbox.value())
        #                 self.analysis_input.GPU = int(self.load_widget.gpu_spinbox.value())
        #         self.toggle_navigation_buttons_enabled.emit(True)
        #         self.validate_model()

    def on_training_completed(self):
        """
        Handle successful completion of the training process.
        
        Stores the trained model and initiates the validation process.
        Re-enables UI elements that were disabled during training.
        
        Args:
            model (Model): The trained Keras model.
        """
        self.model_path = self.train_widget.get_model()
        self.toggle_navigation_buttons_enabled.emit(self.model_path is not None)
        #self.validate_model()
        self.toggle_enabled_widgets_training(True)

    def on_training_error(self, e: str):
        """
        Handle errors that occur during training.
        
        Re-enables UI elements that were disabled during training.
        
        Args:
            e (str): The error message.
        """
        self.toggle_enabled_widgets_training(True)

    def toggle_enabled_widgets_training(self, set_enabled: bool):
        """
        Enable or disable widgets during the training process.
        
        Controls which UI elements are interactive during training.
        Also emits a signal to enable/disable navigation buttons in the parent container.
        
        Args:
            set_enabled (bool): True to enable widgets, False to disable them.
        """
        self.train_widget.start_button.setEnabled(set_enabled)
        self.load_widget.setEnabled(set_enabled)
        if set_enabled:
            self.toggle_navigation_buttons_enabled.emit(self.model_path is not None)
        else:
            self.toggle_navigation_buttons_enabled.emit(False)

