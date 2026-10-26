import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QStackedWidget, QPushButton, QHBoxLayout
from reaction_widget.reaction_widget import ReactionWidget
from global_input_widget.input_widget import GlobalInputWidget
from analysis_widget.analysis_widget import AnalysisWidget
from train_validation_widget.train_validation_widget import TrainValidateWidget
from train_validation_widget.user_input import TrainingInput, AnalysisInput


class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        # self.init_loading_section()

    def initUI(self):
        self.setWindowTitle("Focus DLRN")
        self.setMinimumSize(800, 400)

        self.main_widget = QWidget()
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.main_widget)

        self.central_stacked_widget = QStackedWidget()

        self.global_page = GlobalInputWidget()
        self.central_stacked_widget.insertWidget(0, self.global_page)

        self.reaction_widget = ReactionWidget(self.global_page)
        self.central_stacked_widget.insertWidget(1, self.reaction_widget)

        self.training_validation_widget = TrainValidateWidget(self)
        self.training_validation_widget.toggle_navigation_buttons_enabled.connect(self.toggle_navigation_buttons_enabled)
        self.central_stacked_widget.insertWidget(2, self.training_validation_widget)

        self.analysis_page = AnalysisWidget(self)
        self.central_stacked_widget.insertWidget(3, self.analysis_page)

        self.navigate_button_forward = QPushButton("Confirm and continue")
        self.navigate_button_forward.setEnabled(False)
        self.navigate_button_forward.pressed.connect(self.navigate_forward)
        self.global_page.data_label.textChanged.connect(self.update_continue_button_state)
        self.global_page.output_label.textChanged.connect(self.update_continue_button_state)
        self.navigate_button_backward = QPushButton("Go back")
        self.navigate_button_backward.pressed.connect(self.navigate_backward)
        self.navigate_button_backward.setEnabled(False)

        navigation_layout = QHBoxLayout()
        navigation_layout.addWidget(self.navigate_button_backward)
        navigation_layout.addWidget(self.navigate_button_forward)

        self.main_layout.addWidget(self.central_stacked_widget)
        self.main_layout.addLayout(navigation_layout)

        self.central_stacked_widget.currentChanged.connect(self.update_continue_button_state)
        self.central_stacked_widget.setCurrentIndex(0)
        self.update_continue_button_state()

    def update_continue_button_state(self):
        current_index = self.central_stacked_widget.currentIndex()

        if current_index == 0:
            self.navigate_button_forward.setEnabled(
                bool(self.global_page.data_file_path) and bool(self.global_page.output_dir_path)
            )
        elif current_index == 1:
            self.navigate_button_forward.setEnabled(True)
        elif current_index == 2:
            self.navigate_button_forward.setEnabled(self.training_validation_widget.model_path is not None)
        else:
            self.navigate_button_forward.setEnabled(False)

        self.navigate_button_backward.setEnabled(current_index > 0)

    def navigate_forward(self):
        current_page = self.central_stacked_widget.currentIndex()

        match current_page:
            case 0:
                global_input_variables = self.global_page.get_current_state()
                if global_input_variables:
                    self.central_stacked_widget.setCurrentIndex(current_page + 1)
                    self.update_continue_button_state()
            case 1:
                if not self.reaction_widget.reaction_widgets:
                    return
                train_input, analysis_input = self.collect_training_analysis_data()
                self.training_validation_widget.load_data(train_input, analysis_input)
                self.central_stacked_widget.setCurrentIndex(current_page + 1)
                self.update_continue_button_state()
            case 2:
                if not self.training_validation_widget.perform_training:
                    if self.training_validation_widget.model_path is None:
                        self.training_validation_widget.model_path = self.training_validation_widget.load_widget.load_model()
                    if self.training_validation_widget.model_path is None:
                        return
                    if self.training_validation_widget.analysis_input is not None:
                        if self.training_validation_widget.load_widget.gpu_checkbox.isChecked():
                            self.training_validation_widget.analysis_input.workers = int(self.training_validation_widget.load_widget.workers_spinbox.value())
                            self.training_validation_widget.analysis_input.GPU = int(self.training_validation_widget.load_widget.gpu_spinbox.value())
                elif self.training_validation_widget.model_path is None:
                    return
                self.analysis_page.get_input_data(self.training_validation_widget)
                self.central_stacked_widget.setCurrentIndex(current_page + 1)
                self.analysis_page.status_label.setText("Status: Select input")
                self.navigate_button_forward.setEnabled(False)
                self.navigate_button_backward.setEnabled(True)
            case 3:
                return

    def navigate_backward(self):
        current_page = self.central_stacked_widget.currentIndex()

        match current_page:
            case 1:
                self.central_stacked_widget.setCurrentIndex(current_page - 1)
                self.navigate_button_backward.setEnabled(False)
                self.navigate_button_forward.setEnabled(False)
            case 2:
                self.reaction_widget.forget_inputs()
                self.training_validation_widget.forget_data()
                self.central_stacked_widget.setCurrentIndex(current_page - 1)
                self.navigate_button_backward.setEnabled(True)
                self.navigate_button_forward.setEnabled(False)
            case 3:
                self.analysis_page.clear_results()
                self.central_stacked_widget.setCurrentIndex(current_page - 1)
                self.navigate_button_backward.setEnabled(True)
                self.navigate_button_forward.setEnabled(self.training_validation_widget.model_path is not None)

    def toggle_navigation_buttons_enabled(self, set_enabled: bool):
        current_index = self.central_stacked_widget.currentIndex()
        if current_index == 2:
            self.navigate_button_forward.setEnabled(set_enabled)
        elif current_index == 3:
            self.navigate_button_forward.setEnabled(False)
        else:
            self.update_continue_button_state()
        self.navigate_button_backward.setEnabled(current_index > 0)

    def collect_training_analysis_data(self) -> tuple[TrainingInput, AnalysisInput]:
        self.reaction_widget.collect_inputs()

        data = self.global_page.data
        is_transient_absorption = self.global_page.is_transient_absorption
        output_dir_path = self.global_page.output_dir_path
        dark_state = self.reaction_widget.dark_state
        reaction_strings_list = self.reaction_widget.reaction_strings_list
        known_spectra_list = self.reaction_widget.known_spectra_list
        concentration_list = self.reaction_widget.concentration_list
        chem_name_to_label_dict_list = self.reaction_widget.chem_name_to_label_dict_list
        active_states_list = self.reaction_widget.active_states_list

        train_input = TrainingInput(
            output_path=output_dir_path,
            data=data,
            reaction_strings_list=reaction_strings_list,
            active_states_list=active_states_list,
            TA=is_transient_absorption,
            known_spectra=known_spectra_list,
            dark_state=dark_state,
        )
        analysis_input = AnalysisInput(
            output_path=output_dir_path,
            data=data,
            reaction_strings_list=reaction_strings_list,
            concentration_list=concentration_list,
            active_states_list=active_states_list,
            chem_name_to_label_dict_list=chem_name_to_label_dict_list,
            TA=is_transient_absorption,
            known_spectra=known_spectra_list,
        )

        return train_input, analysis_input

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())