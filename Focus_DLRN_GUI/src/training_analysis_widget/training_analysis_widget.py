from PySide6.QtWidgets import QWidget, QPushButton, QGridLayout, QLineEdit, QCheckBox, QFileDialog, QMessageBox, QGroupBox,QVBoxLayout,QApplication
from DNN_pipeline.training import training
from DNN_pipeline.analysis import analysis
from training_analysis_widget.progress_display_widget import Progress_Report_Widget
from tensorflow.keras import models
from tensorflow.keras.layers import TFSMLayer
import numpy as np
import os



class Training_and_Analysis_Widget(QWidget):
    model_file_dir: str | None
    #model = tfmodel | None

    def __init__(self, global_widget, reaction_widget, parent = None):
        super().__init__(parent)
        self.initUI()

        self.global_widget = global_widget
        self.reaction_widget = reaction_widget
        self.model_file_dir = None
        self.model = None

        self.model_pred_accuracy = []
        self.residuals = []
        self.residual_sums = []
        self.residual_aves = []
        self.concentrationtraces = []
        self.rate_constants = []
        self.system_model_list = []

    
    def initUI(self):
        """
        Set up the user interface components.
        
        Creates and arranges all UI elements including text fields, buttons, and checkbox
        with appropriate connections to handler methods.
        """
        layout = QGridLayout()

        # --- first row: Loading DNN model ---
        self.model_label = QLineEdit(placeholderText="Path to DNN_Model(optional)", readOnly=True)
        layout.addWidget(self.model_label, 0, 0)

        self.model_load_button = QPushButton("Load trained DNN_Model")
        self.model_load_button.pressed.connect(self.select_model_dir)
        layout.addWidget(self.model_load_button, 0, 1)

        self.model_clear_button = QPushButton("Clear")
        self.model_clear_button.pressed.connect(self.clear_model)
        layout.addWidget(self.model_clear_button, 0, 2)

        # --- second row: start analysis or training ---
        self.spectrum_load_button = QPushButton("Start Analysis")
        self.spectrum_load_button.pressed.connect(self.start_analysis)
        layout.addWidget(self.spectrum_load_button, 1, 0, 1,-1)

        # --- third row: progress report ---
        self.progress_group_box = QGroupBox("Status Report")
        self.progress_group_layout = QVBoxLayout()
        self.progress_display = Progress_Report_Widget()
        self.progress_group_layout.addWidget(self.progress_display)
        self.progress_group_box.setLayout(self.progress_group_layout)

        layout.addWidget(self.progress_group_box, 2, 0, 1, -1)

        self.setLayout(layout)
    
    def select_model_dir(self):
         """
         Open a file dialog to select an existing model file.
        
         Updates the model_file_dir attribute and updates the text in the
         corresponding QLineEdit when a file is selected.
         """
         dialog = QFileDialog(self, "Select a model file")
         dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
         if dialog.exec():
             path = dialog.selectedFiles()[0]
             self.model_file_dir = path
             self.model_label.setText(path)
        

    def clear_model(self):
        if self.model_file_dir:
            self.model_file_dir = None
            self.model_label.setText("")

    def  save_analysis(self):
        output_dir_path = self.global_widget.output_dir_path
        system_model_list = self.reaction_widget.stochio_matrix_list
        for i in range(len(system_model_list)):
            folder_path = output_dir_path + "/model" +str(i)
            os.makedirs(folder_path)
            np.savetxt(folder_path + "/" + "stochiometric_reaction_presentation.csv",np.array(system_model_list[i]), delimiter=";")
            np.savetxt(folder_path + "/" + "residual.csv",np.array(self.residuals[i]), delimiter=";")
            np.savetxt(folder_path + "/" + "concentration_trace_matrix.csv",np.array(self.concentrationtraces[i]), delimiter=";")

            #create also general information file e.g rate cosnmtants and prediction metrics




    def start_analysis(self):

        time_resolved_spectrum = self.global_widget.spectrum_data
        timescale_data = self.global_widget.timescale_data
        is_transient_absorption = self.global_widget.is_transient_absorption
        output_dir_path = self.global_widget.output_dir_path
        concentration_range = self.global_widget.min_max_conc
        print(concentration_range)

        #print(np.shape(time_resolved_spectrum))
        #print(np.shape(timescale_data))
        #print(is_transient_absorption)
        #print(output_dir_path)
        self.reaction_widget.collect_inputs()
        system_model_list = self.reaction_widget.stochio_matrix_list
        known_spectra_list = self.reaction_widget.known_spectra_list
        concentration_list = self.reaction_widget.concentration_list
        chemicals_index_dict_list = self.reaction_widget.chemicals_index_dict_list
        active_states_list = self.reaction_widget.active_states_list
        

        species_list = [[0 for i in range(len(chemicals_index_dict_list[j].keys()))] for j in range(len(chemicals_index_dict_list))]
        
        for idx_model in range(len(chemicals_index_dict_list)): 
            for key in chemicals_index_dict_list[idx_model].keys():
                species_list[idx_model][chemicals_index_dict_list[idx_model][key]] = key
        #print(species_list)

        #print(system_model_list)
        #print(known_spectra_list)
        #print(concentration_list)
        #print(chemicals_index_dict_list)
        #print(active_states_list)
        
        if self.model_file_dir == None:
            #start training
            self.progress_display.update_widget("Training started. This can take up to 45 min.")
            QApplication.processEvents()
            self.model = training(time_resolved_spectrum,system_model_list,active_states_list,is_transient_absorption,species_list,
                                  known_spectra_list,concentration_list,concentration_range)
            self.model.save(output_dir_path + "/trained_DNN_model.keras")
            self.progress_display.update_widget("Training finished")
            QApplication.processEvents()
        else:
            self.model = models.load_model(self.model_file_dir,compile=False)

        #start analysis
        self.progress_display.update_widget("Analysis started")
        QApplication.processEvents()
        results = analysis(time_resolved_spectrum,system_model_list,timescale_data,self.model,active_states_list,
                           is_transient_absorption,species_list,known_spectra_list,concentration_list,concentration_range)
        for i in range(len(system_model_list)):
            self.model_pred_accuracy.append(results["model_pred_likelihood"][i])
            print(results["model_pred_likelihood"][i])
            self.residuals.append(results["residual"][i])
            print(np.shape(results["residual"][i]))
            self.concentrationtraces.append(results["concentration_traces"][i])
            print(np.shape(results["concentration_traces"][i]))
            self.residual_aves.append(results["res_ave"][i])
            print(results["res_ave"][i])
            self.residual_sums.append(results["res_sum"][i])
            print(results["res_sum"][i])
            self.rate_constants.append(results["rate_constants"][i])
            print(results["rate_constants"][i])
            print("DONE")

        #self.save_analysis()
        self.progress_display.update_widget("Analysis finished")

            
    
