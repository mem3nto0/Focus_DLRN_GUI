from PySide6.QtCore import QObject, Signal, Slot
from .user_input import TrainingInput
from DNN_pipeline.pipeline_DLRN_training import training

class TrainingWorker(QObject):
    """
    Worker class for handling model training in a separate thread.
    
    This class performs the training process asynchronously in a background thread,
    emitting signals to indicate progress updates and completion status.
    
    Signals:
        process_updated (int): Emitted to report training progress as a percentage.
        training_finished (object): Emitted when training completes successfully, passes the trained model.
        training_error (str): Emitted when training encounters an error, passes the error message.
    """
    training_input: TrainingInput

    process_updated = Signal(int)
    training_finished = Signal(object)
    training_error = Signal(str)

    def __init__(self, training_input: TrainingInput, parent = None) -> None:
        """
        Initialize the TrainingWorker.
        
        Args:
            parent (QObject, optional): The parent QObject. Defaults to None.
        """
        super().__init__(parent)
        self.training_input = training_input

    @Slot()
    def train(self):
        """
        Perform the model training process.
        
        This method is designed to be executed in a separate thread. It:
        1. Executes the training logic
        2. Reports progress via the process_updated signal
        3. Emits the trained model via training_finished signal on success
        4. Emits error messages via training_error signal on failure
        
        Note: 
            The current implementation is a placeholder with a simulated training process.
            Actual training logic should be implemented where the TODO comment is located.
        """
        try:
            model_name = self.training_input.model_name
            output_path = self.training_input.output_path
            data = self.training_input.data
            reaction_strings_list = self.training_input.reaction_strings_list
            active_states_list = self.training_input.active_states_list
            min_conc = self.training_input.min_conc
            max_conc = self.training_input.max_conc
            tau_lists = self.training_input.tau_lists
            N_train_batch = self.training_input.N_train_batch
            batch_size = self.training_input.batch_size
            workers = self.training_input.workers
            dark_state = self.training_input.dark_state
            full_spec_gen = self.training_input.full_spec_gen
            TA = self.training_input.TA
            known_spectra = self.training_input.known_spectra
            GPU = self.training_input.GPU

            self.trained_model_path = training(output_path+"/"+model_name+".h5",reaction_strings_list,output_path+"/training_data",min_conc,max_conc,tau_lists,N_train_batch,batch_size,dark_state,full_spec_gen,workers,GPU)
            
            #self.model.save(self.training_input.output_path + "/trained_DNN_model.keras")

            #for i in range(101):
            #    time.sleep(0.05)
            #    self.process_updated.emit(i)

            #model = Model(inputs=[], outputs=[])
            self.training_finished.emit(self.trained_model_path)

        except Exception as e:
            self.training_error.emit(str(e))


