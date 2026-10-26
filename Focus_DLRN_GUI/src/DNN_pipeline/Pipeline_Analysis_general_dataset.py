#%%
import pandas as pd
import matplotlib.pyplot as plt
import tensorflow as tf
import os
import numpy as np
from .utility_analysis import Generate_trace_after_analysis, Extract_tau_analysis
import numpy as np



def analysis(model_path:str,data:pd.DataFrame):

    model = tf.keras.models.load_model(model_path, compile= False)

    # select the folder to analyze 
    #data_folder = "DLRN_file_analysis/ACD_analysis_enzyme_new_data" # Toehold_analysis_data_40-40-40-40" "New_data_202607_different_conditions" "PH_analysis_Parallel" "PH_analysis_linear" "Enzime_analysis" "LInear_data_statistics"
    #list_data = os.listdir(data_folder)


    # === time scale used for the training === 
    time_1 = np.arange(0,2,0.2)       
    time_2 = np.arange(2,20,0.5)
    time_3 = np.logspace(1, 2.304, num=(256 -(len(time_1) + len(time_2))), base=20)
    time_training =  np.concatenate((time_1, time_2, time_3), axis = 0)

    time_uploaded = data["Time"].to_numpy()

    data = data.iloc[:, 1:]
    n_spectra = data.shape[1]

    
    data_to_analyze = np.zeros([256,256,1])
    data_to_interpolate = np.zeros([256,len(time_uploaded)])

    trace_width = int(250/(n_spectra*3)) - int((250/(n_spectra*3))*0.2)
    space = (250 - ((n_spectra*3))*trace_width)/(n_spectra*3)

    var_gen = 2 # int(6/len(names))

    for i in range(0,n_spectra):
        
        for j in range(var_gen):

            name = data.columns[-i -1] # to do reverse, otherwise just i

            # name = names[i] # to do reverse, otherwise just i

            single_tr = data[name].to_numpy()

            start = i*int(trace_width*(var_gen) + space*(var_gen)) + int(trace_width*(j) + space*(j))
            end = int(start + trace_width)

            data_to_interpolate[start:end,:] = single_tr


    max_val = np.max(time_uploaded)
    max_val_2 = np.max(time_training)
    time_uploaded = time_uploaded*(max_val_2/max_val)

    for j in range(256):

        data_to_analyze[j,:,0] = np.interp(time_training, time_uploaded, data_to_interpolate[j,:])

    norm_factor = np.max(np.abs(data_to_analyze))

    data_to_analyze = (data_to_analyze) / norm_factor

    data_to_analyze = np.expand_dims(data_to_analyze, axis=0)
    predictions = model.predict(data_to_analyze)

    return norm_factor,predictions


def Parse_initial_conditions(file_name,
                             initial_cond_1,
                             initial_cond_2,
                             cond_2_slots = None):
    """
    Read the concentrations encoded in the file name, e.g.

        "ABCD_40_40_20_40_apta_0mM.xlsx"  ->  [40, 40, 20, 40]

    The first number is the active concentration of Initial_cond_1 (constant across
    the dataset), the remaining ones replace, in order, the entries of Initial_cond_2
    given by cond_2_slots (by default the non zero positions of the template, i.e. the
    species that are actually loaded).

    Only the numeric tokens that directly follow the first token are used, so trailing
    labels such as "_apta_0mM" or "_ThC" are ignored.

    Returns (Initial_Con, cond_1, cond_2). If the file name does not carry the expected
    amount of numbers the template values are kept unchanged.
    """

    stem = os.path.splitext(os.path.basename(file_name))[0]
    tokens = stem.split("_")

    values = []
    for tok in tokens[1:]:
        if tok.isdigit():
            values.append(float(tok))
        elif values:   # stop at the first non numeric token after the concentrations
            break

    cond_1 = np.asarray(initial_cond_1, dtype = float).copy()
    cond_2 = np.asarray(initial_cond_2, dtype = float).copy()

    if cond_2_slots is None:
        slots = np.nonzero(np.asarray(initial_cond_2))[0]
    else:
        slots = np.asarray(cond_2_slots, dtype = int)

    if len(values) == len(slots) + 1:
        cond_1[0]     = values[0]
        cond_2[slots] = values[1:]
    else:
        print("[warning] " + str(file_name) + ": found " + str(len(values)) +
              " concentrations, expected " + str(len(slots) + 1) +
              " -> template initial conditions kept")

    return np.concatenate((cond_1, cond_2), axis = 0), cond_1, cond_2


def plot_pred(data: pd.DataFrame,reactions_list,norm_factor, model_analysis,tau_prediction, named_state_conc,reaction_part_conc,used_reaction_parts:list):
    # " adjust time zero "  # Maybe delete ????

    index = 1
    cut_index_start = 2
    time_analysis = data["Time"]

    data = data.iloc[:,:]
    data = data / np.max(data)

    time_1 = np.arange(0,2,0.2)       
    time_2 = np.arange(2,20,0.5)
    time_3 = np.logspace(1, 2.304, num=(256 -(len(time_1) + len(time_2))), base=20)
    time_training =  np.concatenate((time_1, time_2, time_3), axis = 0)

    max_val = np.max(time_analysis)
    max_val_2 = np.max(time_training)


    print(tau_prediction)

    #pred[1][0][0] = pred[1][0][0] * 1.1

    index_model = np.where(model_analysis == np.max(model_analysis))[0][0]

    select_model_analysis = reactions_list[index_model]

    tau_analysis = Extract_tau_analysis(select_model_analysis, tau_prediction)

    tau_analysis = tau_analysis / (max_val_2/max_val) 

    # named state concentrations (A,B,C,D,GS).
    #Initial_cond_1 = np.array([40,0,0,0,0])

    # reaction number add on concentrations (1,2,3,4,5,6,7,8,9,10).
    #Initial_cond_2 = np.array([40,40,0,0,40,0,0,0,0,0])

    # Initial_cond_2 = np.array([40,40,0,0,0,0,0,0,0,0])

    # positions of Initial_cond_2 that are actually loaded and therefore read from the
    # file name. None -> use the non zero entries of the template above (their order is
    # the order in which the concentrations appear in the file name). Now used_reaction parts [True,False...]
    #Initial_cond_2_slots = None

    # initial conditions of the file currently analyzed (index), read from its name
    Initial_Con, cond_1_index, cond_2_index = Parse_initial_conditions(data,
                                                                    named_state_conc,
                                                                    reaction_part_conc,
                                                                    used_reaction_parts)

    #print("initial conditions", list_data[index], Initial_Con)

    kinetic_traces = Generate_trace_after_analysis(time_analysis, 
                                                    select_model_analysis, 
                                                    tau_analysis, 
                                                    Initial_Con)

    kinetic_traces = kinetic_traces[:,1:]
    kinetic_traces = kinetic_traces / np.max(kinetic_traces)

    data_to_interpolate = data_to_interpolate[:,:]

    data = data * norm_factor

    amps = np.linalg.lstsq(kinetic_traces,data.T)[0]
    Reconstruct_signal = kinetic_traces[:,:] @ amps
    Reconstruct_signal = Reconstruct_signal.T

    res1 = np.sum( np.abs(data[130,:] - Reconstruct_signal[130,:]) )
    res2 = np.sum( np.abs(data[20,:] - Reconstruct_signal[20,:]) )

    print(index_model)
    print("one hot model", model_analysis)
    print("tau values", tau_analysis)

    plt.plot(time_analysis[:], data[20,:],"-o")
    plt.plot(time_analysis[:], data[130,:], "-o")
    plt.plot(time_analysis[:], data[220,:],"-o")

    plt.plot(time_analysis[:],Reconstruct_signal[20,:], "--", color = "black")
    plt.plot(time_analysis[:],Reconstruct_signal[130,:],"--", color = "black")
    plt.plot(time_analysis[:],Reconstruct_signal[220,:], "--", color = "black")

    plt.title(res1 + res2)
    plt.xlim(0,30)

def residual_and_conc_traces(data: pd.DataFrame,reaction_strings:list[str],norm_factor:float,tau_prediction:list[float], named_state_conc,reaction_part_conc,active_states:list):
    #!!!!!!!!!!!!!!! how to set states to non activate or active ?
    time_analysis = data["Time"].to_list()
    #print(time_analysis)
    
    data = data.drop(columns=["Time"])
    data = data.values.tolist()
    #print(data)
    data = data / np.max(data)

    time_1 = np.arange(0,2,0.2)       
    time_2 = np.arange(2,20,0.5)
    time_3 = np.logspace(1, 2.304, num=(256 -(len(time_1) + len(time_2))), base=20)
    time_training =  np.concatenate((time_1, time_2, time_3), axis = 0)

    max_val = np.max(time_analysis)
    max_val_2 = np.max(time_training)

    tau_analysis = Extract_tau_analysis(reaction_strings, tau_prediction)
    #print(tau_analysis)
    
    tau_analysis = tau_analysis / (max_val_2/max_val) 
    Initial_Con = named_state_conc+reaction_part_conc
    kinetic_traces,k_values = Generate_trace_after_analysis(time_analysis, 
                                                    reaction_strings, 
                                                    tau_analysis, 
                                                    Initial_Con)
    is_active_index = [i for i, x in enumerate(active_states) if x]
    kinetic_labels = np.array(["A","B","C","D","GS","1","2","3","4","5","6","7","8","9","10"])
    used_kinetic_labels = kinetic_labels[is_active_index]
    used_kinetic_traces =  kinetic_traces[:, is_active_index]
    #print(kinetic_traces)
    print(np.shape(used_kinetic_traces))
    
    #kinetic_traces = kinetic_traces[:,:] #?!!!!!!!!!!!!!!!! 1?
    kinetic_traces_max_norm = kinetic_traces / np.max(kinetic_traces)
    #print(np.shape(kinetic_traces))
    #print(np.shape(data))

    #remove non activate states
    
    active_kinetic_traces = kinetic_traces_max_norm[:, is_active_index]
    #print(np.shape(active_kinetic_traces))

    #maybe add to set all non activate traces to 0 ?
    
    data = data * norm_factor
    
    amps = np.linalg.lstsq(active_kinetic_traces,data)[0]
    Reconstruct_signal = active_kinetic_traces @ amps
    #Reconstruct_signal = Reconstruct_signal.T

    residual = abs(data-Reconstruct_signal)
    res_sum = np.sum(residual)
    res_mean = np.mean(residual)

    print(np.shape(residual))

    return residual,res_sum,res_mean,Reconstruct_signal,used_kinetic_traces,time_analysis,k_values,used_kinetic_labels



