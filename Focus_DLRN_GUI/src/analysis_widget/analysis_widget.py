import os

import numpy as np
import pandas as pd
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QPushButton, QLabel, QApplication

from .single_analysis_widget import SingleAnalysisWidget
from DNN_pipeline.Pipeline_Analysis_general_dataset import analysis, residual_and_conc_traces


class AnalysisWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.analysis_input = None
        self.model_path = None
        self.model_prob = []
        self.tau_values = []
        self.residuals = []
        self.residual_sums = []
        self.residual_mse = []
        self.concentration_traces = []
        self.rate_constants = []
        self.analysis_tabs = QTabWidget()
        self.analysis_tabs.setVisible(True)
        self.initUI()

    def get_input_data(self, training_widget):
        self.analysis_input = training_widget.analysis_input
        self.model_path = training_widget.model_path

    def initUI(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(8)

        self.analysis_tabs.setVisible(False)

        main_layout.addStretch(1)

        self.start_analysis_button = QPushButton("Start Analysis")
        self.start_analysis_button.setMinimumHeight(40)
        self.start_analysis_button.setStyleSheet("font-size: 16px; font-weight: 700;")
        self.start_analysis_button.clicked.connect(self.start_analysis)
        main_layout.addWidget(self.start_analysis_button, alignment=Qt.AlignmentFlag.AlignCenter)

        self.status_label = QLabel("Status: Select input")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 13px; font-weight: 700;")
        main_layout.addWidget(self.status_label, alignment=Qt.AlignmentFlag.AlignCenter)

        main_layout.addStretch(1)
        main_layout.addWidget(self.analysis_tabs)

    def start_analysis(self):
        self.start_analysis_button.setEnabled(False)
        self.start_analysis_button.repaint()
        self.status_label.setVisible(True)
        self.status_label.setText("Status: Analysis in process, this might take some time")
        self.status_label.setStyleSheet("font-size: 13px; font-weight: 700;")
        QApplication.processEvents()

        if self.analysis_input is None:
            self.status_label.setText("Status: No analysis input available")
            self.start_analysis_button.setEnabled(True)
            QApplication.processEvents()
            return

        data = self.analysis_input.data
        norm_factor, predictions = analysis(self.model_path, data)
        model_prob, tau_values = predictions
        self.model_prob, self.tau_values = np.array(model_prob[0]), np.array(tau_values[0])
        self.norm_factor = norm_factor
        print(self.model_prob)
        print(self.tau_values)

        QTimer.singleShot(1000, self.finish_analysis)

    def finish_analysis(self):
        self.start_analysis_button.setEnabled(False)
        self.start_analysis_button.setVisible(False)
        self.status_label.setVisible(False)
        self.analysis_tabs.setVisible(True)
        self.draw_results()

    def clear_results(self):
        self.analysis_tabs.clear()
        self.analysis_tabs.setVisible(False)
        self.model_prob = []
        self.tau_values = []
        self.residuals = []
        self.residual_sums = []
        self.residual_mse = []
        self.concentration_traces = []
        self.rate_constants = []
        self.analysis_input = None
        self.model_path = None
        self.start_analysis_button.setVisible(True)
        self.start_analysis_button.setEnabled(True)
        self.status_label.setVisible(True)
        self.status_label.setText("Status: Select input")
        self.status_label.setStyleSheet("font-size: 13px; font-weight: 700;")

    def conc_to_nico_conc(self,concentrations):
        main_c = ["A","B","C","D","GS"]
        
        main_c_value = [0 for c in main_c]
        side_c_value = [0 for rp in range(10)]
        for react in concentrations.keys():
            if react in main_c:
                index = main_c.index(react)
                main_c_value[index] = concentrations[react]
            else:
                index = int(react)-1
                side_c_value[index] = concentrations[react]

        return main_c_value,side_c_value

    def active_spec_to_nico_spec(self,active_spec):
            main_c = ["A","B","C","D","GS"]
            
            active_spec_value = [False for rp in range(15)]
            
            for react in active_spec.keys():
                if react in main_c:
                    index = main_c.index(react)
                    active_spec_value[index] = active_spec[react]
                else:
                    index = int(react)+4
                    active_spec_value[index] = active_spec[react]
    
            return active_spec_value



    def draw_results(self):
        if self.analysis_input is None:
            return

        self.analysis_tabs.clear()

        reaction_count = len(getattr(self.analysis_input, "reaction_strings_list", []))
        if reaction_count == 0:
            reaction_count = max(len(self.model_prob), len(self.residuals), len(self.concentration_traces))

        if reaction_count == 0:
            return

        results_dir = os.path.join(getattr(self.analysis_input, "output_path", os.getcwd()), "results")
        os.makedirs(results_dir, exist_ok=True)

        excel_path = os.path.join(results_dir, "analysis_results.xlsx")
        try:
            workbook = pd.ExcelWriter(excel_path, engine="openpyxl")
        except ImportError:
            workbook = pd.ExcelWriter(excel_path, engine="xlsxwriter")

        try:
            for i in range(reaction_count):
                model_probability = float(self.model_prob[i])
                tau_pred = self.tau_values
                active_states = self.analysis_input.active_states_list[i]
                active_states_converted = self.active_spec_to_nico_spec(active_states)
                data=self.analysis_input.data
                reaction_strings = self.analysis_input.reaction_strings_list[i]
                norm_factor = self.norm_factor
                concentration_list = self.analysis_input.concentration_list[i]
                main_c_value,side_c_value = self.conc_to_nico_conc(concentration_list)
                chem_name_to_label_dict = self.analysis_input.chem_name_to_label_dict_list[i]

                residual,res_sum,res_mean,reconstructed_signal,kinetic_traces,time_analysis,k_values,used_kinetic_labels = residual_and_conc_traces(data,reaction_strings,norm_factor,tau_pred,main_c_value,side_c_value,active_states_converted)

                used_kinetic_labels=[chem_name_to_label_dict[name] for name in used_kinetic_labels]

                model_widget = SingleAnalysisWidget(
                    model_probability=model_probability,
                    residual_sum=res_sum,
                    residual_mean=res_mean,
                    residual=residual,
                    concentration_traces=kinetic_traces,
                    rate_constants=k_values,
                    tau_values= tau_pred,
                    reaction_string=reaction_strings,
                    used_kinetic_labels=used_kinetic_labels,
                    time=time_analysis,
                    reconstructed_signal=reconstructed_signal,
                    input_data=data,
                    chem_name_to_label_dict=chem_name_to_label_dict
                )

                sheet_name = f"System Model {i + 1}"
                model_widget.save_residual_image(results_dir, f"system_model_{i + 1}_residual.png")
                model_widget.save_concentration_trace_image(results_dir, f"system_model_{i + 1}_concentration_traces.png")

                summary_df = pd.DataFrame([
                    ["Predicted Likelihood", f"{model_probability:.3f}"],
                    ["Residual sum", f"{res_sum:.3f}"],
                    ["Residual MSE", f"{res_mean:.3f}"],
                ])
                summary_df.to_excel(workbook, sheet_name=sheet_name, index=False, header=False, startrow=0)

                table_df = pd.DataFrame(model_widget.subreaction_table, columns=["Subreaction", "Tau", "k"])
                table_df.to_excel(workbook, sheet_name=sheet_name, index=False, startrow=5)

                self.analysis_tabs.addTab(model_widget, f"System Model {i + 1}")
        finally:
            workbook.close()

    def fill_tabs(self):
        self.draw_results()