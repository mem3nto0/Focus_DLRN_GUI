#%%
import numpy as np
from .Utility_barCoding import *
import matplotlib.pyplot as plt
import os


def Generate_training_data_DLRN_focus(select_model, 
                                        N_training_data,
                                        Save_path,
                                        N_model,
                                        Concentraion_range,
                                        time_const_range,
                                        index,
                                        Dark_state,
                                        Full_spectra_generation,
                                        N_traces
                                        ):

       
    # create the wl
    wl = np.arange(0,256,1)
    
    # time scale vector new version   

    time_1 = np.arange(0,2,0.2)       
    time_2 = np.arange(2,20,0.5)
    time_3 = np.logspace(1, 2.304, num=(256 -(len(time_1) + len(time_2))), base=20)
    time =  np.concatenate((time_1, time_2,time_3), axis = 0)


    # Given species_list1
    species_list1 = ["A", "B", "C", "D", "GS"]

    # all possible reaction pathways:

    reactions_paths = [
        ("A", "B"),
        ("A", "C"),
        ("A", "D"),
        ("A", "GS"),
        ("B", "C"),
        ("B", "D"),
        ("B", "GS"),
        ("C", "D"),
        ("C", "GS"),
        ("D", "GS")
    ]

    # //////// Generate a dictionary for the reactions paths /////////
    #maybe needed get amx order from model
    Model_one_hot = Create_one_hot_model(reactions_paths, species_list1, select_model, 2)

    if Dark_state == True:
        N_traces = N_traces - 1

    # /// here we are creating the signal for the training ///

    for i in range(N_training_data):

        # /// creating the kinetic lists ////

        reaction_list, active_k = Generate_reaction_list(Model_one_hot, 
                                                         reactions_paths,
                                                         select_model)

        # /// Calculate the initial concentration of species involved ////

        Initial_Con = Generate_initial_concentrations(Concentraion_range, reaction_list)
                    
        # /// 
        # Generates the time constants depending on the concentration.
        # This is important because to scale time costants in a range that can be
        # analyzed by the neural network. It need to see data between 0 - 1000.
        # ////

        k_values, k_values_for_training = Generate_kvalues_barcode(active_k, 
                                            time_const_range, 
                                            reaction_list, 
                                            Initial_Con) 
        
        kinetic_traces = Create_kinetc_signal(reaction_list, 
                                              k_values, 
                                              Initial_Con, 
                                              time)
        
        kinetic_traces = kinetic_traces[:,:5]

        coeff = np.random.choice(np.array([1,2,4]))
        Spectra = Spectra_generator(wl, 5, TA_spectra = False)

        if Full_spectra_generation == True:

            if Dark_state == True:

                Spectra[:,0] = Spectra[:,0]*0

            # /// Input for the training ///

            Final_data = np.matmul(Spectra,kinetic_traces.T)
            Final_data = (Final_data + np.random.normal(0, 0.02 / coeff, (Final_data.shape[0],Final_data.shape[0])))

        else:

            Final_data = np.zeros([256,256])

            if Dark_state == True:
                kinetic_traces = kinetic_traces[:,1:N_traces + 1]

            Amp_values = np.random.randint(4, 11, size = N_traces) / 10
            total_traces_image = N_traces*2

            trace_width = int(250/total_traces_image) - int((250/total_traces_image)*0.2)
            space = (250 - total_traces_image*trace_width)/total_traces_image
            var_gen = 2

            track_traces = np.where( np.sum(kinetic_traces, axis = 0) > 0)[0]
            track_traces = len(track_traces)

            for k in range(0, len(Amp_values)):

                coeff = np.random.choice(np.array([1,2,4]))

                for j in range(var_gen):

                    if np.max(kinetic_traces[:, k]) == 0: # to remove

                        back_ground = 0.0 # np.random.randint(1,3) / 10

                        single_tr = np.random.normal(0, 0.02 / coeff, (256)) + back_ground
                        start = k*int(trace_width*(var_gen) + space*(var_gen)) + int(trace_width*(j) + space*(j))
                        end = int(start + trace_width)

                    else:

                        single_tr = Amp_values[track_traces - k - 1]*kinetic_traces[:, track_traces - k - 1] +  np.random.normal(0, 0.02 / coeff, (256))
                        start = k*int(trace_width*(var_gen) + space*(var_gen)) + int(trace_width*(j) + space*(j))
                        end = int(start + trace_width)

                    Final_data[start:end,:] = single_tr

        norm_coeff = np.abs(np.max(Final_data))
        Final_data = (Final_data / norm_coeff)

        # /// First output of the training (model prediction) ///
        output_1_training = np.zeros(N_model)
        output_1_training [index] = 1

        # /// second output of the training (tau predictions) ///
        output_2_training = Generate_tau_output(k_values_for_training, 
                                                Model_one_hot)

        file_name = f"DLRN_train_data_{index}_{i}.npz"
        np.savez_compressed(os.path.join(Save_path,file_name), train = Final_data, 
                            label1 = output_1_training,  
                            label2 = output_2_training,
                            label3 = Spectra[:,:-1], # i have to generate correctly specta for single trace
                            input_2 = Initial_Con)

    return Final_data, output_1_training, output_2_training, Initial_Con, kinetic_traces
