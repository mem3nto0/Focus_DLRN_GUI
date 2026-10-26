#%%

import numpy as np
from .Utility_barCoding import *
import matplotlib.pyplot as plt
 
def Generate_kvalues_analysis(active_vector, tau_analysis, reaction_list, Initial_Con):

    k_values = []; # k values used for the generation of the kinetic traces
    probe_list = list(reaction_list.items())

    # ////////// select the min and max values of the subsets ////////

    index_probe_list = 0

    for i in range( len(active_vector) ):

        probe = active_vector[i]

        for jj in range (probe):

            path, order_and_idx = probe_list[index_probe_list + jj]                    
            order , index_path = order_and_idx

            probe_time = tau_analysis[index_probe_list + jj] 

            if order > 1:
                
                if i == 0:

                    Con1 = Initial_Con[i] 
                    Con2 = Initial_Con[index_path + 5]

                    k_adjusted = Calculate_adjusting_factor(probe_time, Con1, Con2)
                    k_values.append(k_adjusted)

                else:
                        
                    adjust_factor = Initial_Con[index_path + 5]                        
                    k_values.append(1/(probe_time*adjust_factor))                                           

            else:

                k_values.append(1/probe_time)                    

        index_probe_list += probe

    return k_values


def Generate_trace_after_analysis(time, select_model, tau_values, Initial_Con):

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


    Model_one_hot = Create_one_hot_model(reactions_paths, 
                                         species_list1, 
                                         select_model, 
                                         order = 2)

    print(Model_one_hot)

    reaction_list, active_k = Generate_reaction_list(Model_one_hot, 
                                                     reactions_paths,
                                                     select_model)

    k_values = Generate_kvalues_analysis(active_k,
                                            tau_values, 
                                            reaction_list,
                                            Initial_Con)


    kinetic_traces = Create_kinetc_signal(reaction_list, 
                                            k_values, 
                                            Initial_Con, 
                                            time)
    
    #kinetic_traces = kinetic_traces[:,:5]

    return kinetic_traces,k_values


def Extract_tau_analysis(select_model, Tau_predicted):

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

    # Given species_list1
    species_list1 = ["A", "B", "C", "D", "GS"]

    # //////// Generate a dictionary for the reactions paths /////////

    Model_one_hot = Create_one_hot_model(reactions_paths, 
                                         species_list1, 
                                         select_model, 
                                         order = 2)
    
    k_val_index = np.where(Model_one_hot[:,1:] > 0)[0]

    Final_taus = np.zeros(len(k_val_index))

    for i in range(len(k_val_index)):

        tau = Tau_predicted[k_val_index[i]]

        Final_taus[i] = tau # Maybe to change 

    return Final_taus