#%%

import numpy as np
from scipy.integrate import odeint


"""
////////////////////////////////////////////////////////
/// Generate a reaction list. It collect information about kinetic model ////
/////////////////////////////////////////////////////////

"""
"""
reaction_matrix = np.array([[0,0,1],
                           [1,0,0],
                           [1,0,0],
                           [0,1,0],
                           [0,1,0],
                           [1,0,0],
                           [1,0,0],
                           [1,0,0],
                           [0,1,0],
                           [1,0,0]])
"""


def Generate_reaction_list(Model_one_hot, reactions_paths, select_model):  # model_pred is the binary matrix of the kinetic model

    reaction_list = {}  # Initialize an empty dictionary
    species_count = {"A": 0, "B": 0, "C": 0, "D": 0 , "E": 0}  # Count occurrences


    second_order_species = np.zeros(len(reactions_paths), dtype="int")

    for reaction in select_model:

        reactants, product = reaction.split("->")
        letters = reactants.split("+")

        probe_ext_react = (letters[0].replace(" ", ""), product.replace(" ", ""))

        probe_ext_ind = reactions_paths.index(probe_ext_react)

        if len(letters) > 1:
            
            second_order_species[probe_ext_ind] = int(letters[1].replace(" ", "")) - 1

        else:

            second_order_species[probe_ext_ind] = - 1


    for i in range(len(reactions_paths)):

        if np.sum(Model_one_hot[i,1:]) == 1:

            reaction_index = np.where(Model_one_hot[i] == 1)[0][0]

            if second_order_species[i] >= 0:

                reaction_list[reactions_paths[i]] = (reaction_index, second_order_species[i])

            else:

                reaction_list[reactions_paths[i]] = (reaction_index, -1)

            # Count species appearances
            reactant, product = reactions_paths[i]
            if reactant in species_count:
                species_count[reactant] += 1

    activity_vector = np.array([count for count in species_count.values() if count > 0])

    return reaction_list, activity_vector


"""
///////////////////////////////////////
/// calculate the adjusting factor for second order reaction ////
///////////////////////////////////////

"""

def Calculate_adjusting_factor(tau, Con1, Con2):

    # Choose A0 and B0 such that A0 <= B0
    A0 = min(Con1, Con2)
    B0 = max(Con1, Con2)

    if np.isclose(A0, B0):

        Final_k = (2.72 -1)/(A0*tau)

    else:

        # Use second-order integrated law for unequal concentrations
        x = 0.632 * A0  # extent of reaction at tau
        num = B0 * (A0 - x)
        denom = A0 * (B0 - x)

        # // adjust the k value depending on the concentration variation and desire "experimenta tau" //
        
        ln_term = np.log(num / denom)
        Final_k = ln_term / ((B0 - A0) * tau)
        
    return np.abs(Final_k)


"""
///////////////////////////////////////
/// new version to generate random k values using a list of elements ////
///////////////////////////////////////

"""

def Generate_kvalues_barcode(active_vector, time_const_range, reaction_list, Initial_Con):

    N_real_states = len(active_vector)
    k_values = []; # k values used for the generation of the kinetic traces
    k_values_for_training = []; # k values used for the neural network outout (tau training)

    index_chosen = []; # index choses during the selection
    time = []; # tau values picked during the generation
    scale_index = np.arange(0,int(len(time_const_range) -1),1) # generate a vector of indexes
    
    start = np.zeros(1)
    index_chosen.append(int(start))

    # ////////// select the min and max values of the subsets ////////

    if N_real_states == 1:

        index_chosen.append(int(len(scale_index)))

    else:

        for j in range(N_real_states-1):

            if j == 0:

                rnd_choise = int(np.random.choice(scale_index[2:int(len(scale_index)/2.5)])) # int(len(scale_index)/2.5)
                index_chosen.append(rnd_choise)
                new_range = scale_index[rnd_choise:]

            else:

                rnd_choise = int(np.random.choice(new_range[10:int(len(new_range)/2)]))
                index_chosen.append(rnd_choise)
                new_range = new_range[int(np.where(new_range == rnd_choise)[0]):]

        index_chosen.append(int(len(scale_index)))

    # ////////// use the list to create random values of k ////////

    Count_states = 0;
    probe_list = list(reaction_list.items())
    index_probe_list = 0


    for i in range( len(active_vector) ):

        probe = active_vector[i]

        if probe > 0:

            Count_states +=1;

        for jj in range (probe):

            if jj == 0:

                path, order_and_idx = probe_list[index_probe_list + jj]                    
                order , index_path = order_and_idx

                min_val = time_const_range[index_chosen[Count_states -1]]
                max_val = time_const_range[index_chosen[Count_states]]

                if min_val < 1 or max_val < 1:

                    probe_time = np.random.randint(int(10*min_val), int(10*(max_val + 1)))        
                    probe_time = probe_time + round(np.random.uniform(0,1),1)
                    probe_time = probe_time / 10

                else:

                    probe_time = np.random.randint(min_val, (max_val + 1))        
                    probe_time = probe_time + round(np.random.uniform(0,1),1)


                if order > 1:

                    # for high order (>1), we have to dinamically create the range
                    # of values to pick. we need the concentration of the elements and
                    # expected range, that are picked before in the "index_choses".

                    if i == 0:

                        Con1 = Initial_Con[i] 
                        Con2 = Initial_Con[index_path + 5]

                        k_adjusted = Calculate_adjusting_factor(probe_time, Con1, Con2)

                        k_values.append(k_adjusted)
                        k_values_for_training.append(1/(probe_time))

                        time = probe_time

                    else:

                        adjust_factor = Initial_Con[index_path + 5]
                        
                        k_values.append(1/(probe_time*adjust_factor))                    
                        k_values_for_training.append(1/(probe_time))
                        
                        time = probe_time

                else:

                    adjust_factor = 1
                    k_values.append(1/probe_time)
                    k_values_for_training.append(1/(probe_time))
                    
                    time = probe_time

            else:

                """
                # old version:
                path, order = probe_list[index_probe_list + jj]    
                index_path = reactions_dic[path] 
                """

                path, order_and_idx = probe_list[index_probe_list + jj]                    
                order , index_path = order_and_idx

                try:

                    probe_time = np.random.randint(np.ceil(time/2.5) , np.ceil(time*2.5))
                    probe_time = probe_time + round(np.random.uniform(0,1),1)

                except:

                    probe_time = np.random.randint(np.ceil(10*time/2.5), np.ceil(10*time*2.5))        
                    probe_time = probe_time + round(np.random.uniform(0,1),1)
                    probe_time = probe_time / 10
                    
                if order > 1:

                    if i == 0:

                        Con1 = Initial_Con[i]
                        Con2 = Initial_Con[index_path + 5]

                        k_adjusted = Calculate_adjusting_factor(probe_time, Con1, Con2)

                        k_values.append(k_adjusted)
                        k_values_for_training.append(1/(probe_time))

                    else:

                        adjust_factor = Initial_Con[index_path + 5]
                        
                        k_values.append(1/(probe_time*adjust_factor))                    
                        k_values_for_training.append(1/(probe_time))

                else:
                    
                    k_values.append(1/probe_time)                    
                    k_values_for_training.append(1/(probe_time))


        index_probe_list += probe

    return k_values, k_values_for_training


"""
//////////////////////////////////////////////////
/// Create kinetic traces from a kinetic model ////
//////////////////////////////////////////////////

"""

def Create_kinetc_signal(reaction_list, k_values, Initial, time):


    def Resolve_ODE(y, time, reaction_list, k_values):

        # Unpack species concentrations dynamically
        species_list1 = ["A", "B", "C", "D", "GS"]
        species_list2 = ["1", "2", "3", "4", "5","6","7","8","9","10"]

        species_list = species_list1 + species_list2

        species_dict = dict(zip(species_list, y))  # Link species list to concentrations

        # Initialize rate changes
        rate_changes = {species: 0.0 for species in species_list}

        # Loop using index i to access both reactions and k_values
        for i, (reactant, product) in enumerate(reaction_list):
            
            rate = k_values[i]  # Get corresponding rate from k_values
            order_and_idx = reaction_list[(reactant, product)]  # Get reaction order           
            order, index = order_and_idx # Get reaction order and index
            
            if order == 1:

                rate_changes[reactant] -= rate * species_dict[reactant]
                rate_changes[product] += rate * species_dict[reactant]

            if order == 2:

                letter = species_list[index + 5]
                rate_changes[reactant] -= rate * species_dict[reactant]*species_dict[letter]
                rate_changes[product] += rate * species_dict[reactant]*species_dict[letter]

                rate_changes[letter] -= rate * species_dict[reactant]*species_dict[letter]

        # Convert back to list format for odeint
        return [rate_changes[species] for species in species_list]
  

    z = odeint(Resolve_ODE, Initial, time, args=(reaction_list, k_values))
        
    return z


"""
//////////////////////////////////////////////////
/// Generate Spectra for each Species or component ////
//////////////////////////////////////////////////

"""

def Spectra_generator(wl, N_real_states, TA_spectra = False):

    N_Gaus = 8;
    wl_signal = np.zeros((len(wl), N_real_states))
    max_point = int(len(wl)/2)

    #//////// Generate the Ground state spectra (GS) ///////////

    if TA_spectra == True:

        GS_spectra =  np.zeros(len(wl))

        for j in range(np.random.randint(1,N_Gaus)):
            
            amp = np.random.randint(2,10)
            sigma = np.random.randint(3,25)
            w0 = 2*np.random.randint(1, max_point)

            GS_spectra = GS_spectra + amp*np.exp(-0.5*((wl-w0)/sigma)**2)  

    #//////// Generate the Excited state spectra (GS) ///////////

    for i in range (N_real_states - 1):
            
        for j in range(np.random.randint(1,N_Gaus)):
            
            if j == 0:
                amp = np.random.randint(4,10)
            
            else:
                amp = np.random.randint(2,10)

            sigma = np.random.randint(3,25)
            w0 = 2*np.random.randint(1, 128)
            wl_signal[:,i] = wl_signal[:,i] + amp*np.exp(-0.5*((wl-w0)/sigma)**2)                
        
        if TA_spectra == True:

            wl_signal[:,i] = wl_signal[:,i] - GS_spectra

        else:
            
            wl_signal[:,i] = wl_signal[:,i]

    return wl_signal / np.max(np.abs(wl_signal))


"""
//////////////////////////////////////////////////

/// From a list of kinetic pathways, the below function 
Generates the one-hot-reppresentation of a kinetic model ////

the final model looks like this:

columnn 0 = off path, column 1 = 1st order path, column 2 = 2nd order path

Model_one_hot = np.array([[0,0,1],
                           [1,0,0],
                           [1,0,0],
                           [0,1,0],
                           [0,1,0],
                           [1,0,0],
                           [1,0,0],
                           [1,0,0],
                           [0,1,0],
                           [1,0,0]])

//////////////////////////////////////////////////

"""

def Create_one_hot_model(reactions_paths, species_list1, reactions_list, order):

    Model_one_hot = np.zeros([len(reactions_paths), order + 1])
    Model_one_hot [:,0] = 1

    analysis_reaction = []
    reaction_order = []

    for reaction in reactions_list:

        reactants, product = reaction.split(" -> ")
        letters = reactants.split("+")

        # Find which species from species_list1 are in the reactants
        species_in_reactants = [
            species for species in species_list1 if any(species in reactant for reactant in letters)
        ]

        analysis_reaction.append((species_in_reactants[0], product))
        reaction_order.append(len(letters))

    for i in range(len(analysis_reaction)):

        index_x = reactions_paths.index(analysis_reaction[i])
        index_y = reaction_order[i]

        Model_one_hot[index_x, 0] = 0
        Model_one_hot[index_x, index_y] = 1


    return Model_one_hot


"""
//////////////////////////////////////////////////
/// Generate Initial condition values (between 0 and 100 values) ////
//////////////////////////////////////////////////

"""

def Generate_initial_concentrations(Concentration_Range, reaction_list):


    Initial_cond_1 = np.array([np.random.choice(Concentration_Range),0,0,0,0])
    Initial_cond_2 = np.zeros(10)

    roll_dice = np.random.randint(2)

    for (reactant, product) in reaction_list:

        order_and_index = reaction_list[(reactant, product)]
        order, index = order_and_index

        if roll_dice == 0:

            min_val = Initial_cond_1[0] #np.ceil(Initial_cond_1[0]*0.5)
            max_val = np.ceil(Initial_cond_1[0]*2)

        if roll_dice == 1:

            min_val = np.ceil(Initial_cond_1[0]*0.5)
            max_val = Initial_cond_1[0]

        Concentraion_range = np.linspace(min_val,max_val,20, dtype="int")

        if index >= 0:

            Initial_cond_2[index] = np.random.choice(Concentraion_range)

    Initial = np.concatenate((Initial_cond_1,Initial_cond_2), axis=0)

    return Initial


"""
//////////////////////////////////////////////////
/// Create the output for the tau training ////
//////////////////////////////////////////////////

"""

def Generate_tau_output(k_values, Model_one_hot):

    output_2_training = np.zeros(10)
    k_val_index = np.where(Model_one_hot[:,1:] > 0)[0]

    for i in range(len(k_val_index)):

        tau = 1/k_values[i]
        output_2_training[k_val_index[i]] = tau

    return output_2_training

