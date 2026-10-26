#%%

from tensorflow import keras
import numpy as np
import os

class Load_data_generator_DLRN(keras.utils.Sequence):

    """generate data in sequence mode for training the neural network"""

    def __init__(self, batch_size, N_batches, path, list_data):

        """
        batch_size (int) = number of sample per single epoche
        epoche_size (int) = number of epoche and training step to do. 
        """

        """/// read external output from init ///"""

        self.dirs = path
        self.list_data = list_data

        """/// probe the initial file for dimentionality of the data"""

        with np.load(self.dirs + "/" + self.list_data[0]) as data:

            probe_inp1 = data["train"]
            probe_inp2 = data["input_2"]

            probe_out1 =  data["label1"]
            probe_out2 = data["label2"]

        """/// generate the variable for training ///"""

        self.batch_size = batch_size
        self.N_batches = N_batches
        
        self.X_train = np.zeros([self.batch_size,probe_inp1.shape[0],probe_inp1.shape[1],1])
        self.Y_tau_value = np.zeros([self.batch_size,len(probe_out2)])
        self.Y_model = np.zeros([self.batch_size,len(probe_out1)])
        self.Input_2 = np.zeros([self.batch_size,len(probe_inp2)])


        """/// This will garantee shuffled data ///"""

        self.ind_rand = np.arange(0,self.N_batches,1)
        np.random.shuffle(self.ind_rand)

    def __len__(self):
        '''
        Denotes the number of batches per epoch
        '''
        return int(self.N_batches)
    
    def __getitem__(self, index):

        selected_ind = self.ind_rand[index]

        for i in range( self.batch_size):

            with np.load(self.dirs + "/" + self.list_data[selected_ind*self.batch_size + i]) as data:

                self.X_train[i,:,:,0] = data["train"]
                self.Input_2[i] = data["input_2"]

                self.Y_model[i] =  data["label1"]
                self.Y_tau_value[i] = data["label2"]

        """/// Generate the double output"""

        Total_Input = {"input_1": self.X_train, "input_2": self.Input_2}
        Total_output = {"output_1": self.Y_model, "output_2": self.Y_tau_value}

        """/// Depending on the Analysis type, decide the output"""

        return self.X_train, Total_output    


    def on_epoch_end(self):
        # //// shuffle indices ////
        np.random.shuffle(self.ind_rand)
      