#%%
import numpy as np
from .Data_creation_DLRN_focus import Generate_training_data_DLRN_focus
import tensorflow as tf
from .DLRN_2out_embended import get_focused_DRLN
import time
from keras.callbacks import LearningRateScheduler
from .Load_data_from_directory import Load_data_generator_DLRN
import os
import random
import re
import time



"""
# general list to remember the external input numbers 
    reactions_paths = [
        ("A", "B"), # 0
        ("A", "C"), # 1
        ("A", "D"), # 2
        ("A", "GS"), # 3
        ("B", "C"), # 4
        ("B", "D"), # 5
        ("B", "GS"), # 6
        ("C", "D"), # 7
        ("C", "GS"), # 8
        ("D", "GS"), # 9
    ]
  
"""
 

def tau_Personalized_loss(y_true, y_pred):

    mask = tf.cast(tf.not_equal(y_true, 0.0), tf.float32)
    epsilon = tf.keras.backend.epsilon()
    n = tf.maximum(tf.reduce_sum(mask), epsilon)

    mape = tf.abs(y_true - y_pred) / (tf.abs(y_true) + epsilon)
    mape_loss = tf.reduce_sum(mape * mask) / n

    #MSE = tf.keras.losses.mean_squared_error(y_true, y_pred)
    MSE = tf.keras.losses.MeanSquaredError()(y_true, y_pred)

    return mape_loss + MSE*0.0025



def get_lr_callback(initial_lr, min_lr=1.25e-5, decay_factor=0.5, decay_every=2):
    
    def scheduler(epoch):
        # pure formula — no side effects, no closure on optimizer
    
        new_lr = initial_lr * (decay_factor ** (epoch // decay_every))
    
        return max(new_lr, min_lr)

    return scheduler



def training(model_storage_path:str,reactions_list:list[str],training_data_folder:str,min_conc:int, max_con:int, tau_lists:list[list]|None,N_train_batch:int|None=None,batch_size:int|None=None,dark_state:bool=False,full_spec_gen:bool=True,workers:int|None=None,GPU:int|None=None):
    gpus = tf.config.experimental.list_physical_devices('GPU')
    if GPU == None:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
    else:
        tf.config.set_visible_devices(gpus[GPU], "GPU")
        print(f"Using GPU {GPU}: {gpus[GPU]}")

    if workers == None:
        workers = 6

    if batch_size == None:
        batch_size = 32

    if N_train_batch == None:
        #N_train_batch = batch_size*(512) #512
        N_train_batch = batch_size

    start = time.time()

    N_model = len(reactions_list)
    model = get_focused_DRLN(N_model) # fix number of tau in the model

    # losses has to be a dictionary

    losses = {"output_1": tf.keras.losses.categorical_crossentropy, 
            "output_2": tau_Personalized_loss}

    weights = {"output_1": 10.0, 
            "output_2": 1}

    metrics = {"output_1": ["accuracy"], 
            "output_2": ["mse"]} 

    #/// save path. create a folder for it ////
    os.makedirs(training_data_folder, exist_ok= True)

    epochs = 0
    optimizer = tf.keras.optimizers.Adam(learning_rate=0.0001)

    #Collect unique letters
    unique_letters = set()

    for reaction_group in reactions_list:
        for reaction in reaction_group:
            letters = re.findall(r'[A-Za-z]', reaction)
            unique_letters.update(letters)

    #####!!!!!!!!!!!!!!!1 WHY ?  Ask nikoabnout epochs so only 3 but no accuracy ???
    while epochs < 3: # and Final_accuracy < 0.9

        lr_value = max(0.0001 - 0.000025*epochs, 1.25e-5)  # fixed reference point

        lr_schedule_fn = get_lr_callback(
            initial_lr = lr_value,
            min_lr=1.25e-5
        )

        lr_callback = tf.keras.callbacks.LearningRateScheduler(lr_schedule_fn)

        # To change a bit the data generation. too slow

        for i in range (N_model):

            select_model = reactions_list[i]

            Concentraion_range = np.linspace(min_conc,max_con,10, dtype="int")

            # vector of time constants that eack model can pick

            if tau_lists == None:
                tau_lists = [np.arange(0.4, 2, 0.2),np.arange(2,20,1),np.arange(20,30,2)]
            
            time_const_range = np.concatenate(tau_lists, axis= 0)

            # if epochs != 0:
            Generate_training_data_DLRN_focus(select_model, 
                                                N_train_batch,
                                                training_data_folder,
                                                N_model,
                                                Concentraion_range,
                                                time_const_range,
                                                i,
                                                dark_state,
                                                full_spec_gen,
                                                len(unique_letters)
                                                )

        list_data = os.listdir(training_data_folder)       
        random.shuffle(list_data)    

        training_generator =  Load_data_generator_DLRN(batch_size, 
                                                        len(list_data) // batch_size, 
                                                        training_data_folder,
                                                        list_data
                                                        )

        # Compile with different losses
        model.compile(
            optimizer = optimizer,
            loss= losses,  # Different loss functions
            loss_weights = weights,
            metrics= metrics # Optional metrics
        )

        model.fit(training_generator,
                                    epochs=5,
                                    callbacks= [lr_callback])
        #workers= workers,
        #max_queue_size=128,
    
        #Final_accuracy = model_history.history["accuracy"][-1]
        epochs = epochs + 1

    # highMW = gigh model weight

    

    model.save(model_storage_path)

    end = time.time()

    print(end - start)
    print(model_storage_path)

    return model_storage_path



# Save_path = "AC_AB_model_new/DLRN_2models.h5"
# reactions_list = [

# [
#     "A + 1 -> B"    
# ],

# [
#     "A -> B"   
# ]

# ]

# #taus
# time_range00 = np.arange(0.4, 2, 0.2)       
# time_range0 = np.arange(2,20,1)
# time_range1 = np.arange(20,30,2)


# batch_size = 32
# N_train_batch = batch_size*(512) #512

# full_spectra_generation = True