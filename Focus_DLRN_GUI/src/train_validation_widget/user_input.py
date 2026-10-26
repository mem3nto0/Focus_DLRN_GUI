import pandas as pd

class TrainingInput:
    model_name:str
    output_path:str
    data: pd.DataFrame
    reaction_strings_lists: list[str]
    min_conc:float
    max_conc:float
    tau_lists:list[list]|None
    N_train_batch:int
    batch_size:int
    workers:int
    dark_state:bool
    full_spec_gen:bool

    TA: bool
    known_spectra: object
    GPU:str 
    active_states_list:list[dict]

    def __init__(self, output_path: str, data: pd.DataFrame, reaction_strings_list: list[str],active_states_list: list[dict],dark_state: object,  TA: bool, known_spectra: object, model_name: str|None=None, min_conc: float|None=None, max_conc: float|None=None, tau_lists: list[list] | None =None, N_train_batch: int|None=None, batch_size: int|None=None, workers: int|None=None, full_spec_gen: bool|None=None, GPU: str|None=None) -> None:
        self.model_name = model_name
        self.output_path = output_path
        self.data = data
        self.reaction_strings_list = reaction_strings_list
        self.active_states_list = active_states_list
        self.min_conc = min_conc
        self.max_conc = max_conc
        self.tau_lists = tau_lists
        self.N_train_batch = N_train_batch
        self.batch_size = batch_size
        self.workers = workers
        self.dark_state = dark_state
        self.full_spec_gen = full_spec_gen
        #functionality  nedds to be added
        self.TA = TA
        self.known_spectra = known_spectra
        self.GPU = GPU

class AnalysisInput:
    model_name:str
    output_path:str
    data: pd.DataFrame
    reaction_strings_list = list[str]
    known_spectra_list = object
    concentration_list = list[dict]
    chem_name_to_label_dict_list= list[dict]
    active_states_list = list[dict]
  
    tau_lists:list[list]|None
    workers:int
    GPU:str

    def __init__(self,  output_path: str, data: pd.DataFrame, reaction_strings_list: list[str], concentration_list: list[dict], chem_name_to_label_dict_list: list[dict], active_states_list: list[dict], TA: bool, known_spectra: object, model_name: str|None=None, workers: int|None=None, GPU: str|None=None) -> None:
        self.model_name = model_name
        self.output_path = output_path
        self.data = data
        self.reaction_strings_list = reaction_strings_list
        self.concentration_list = concentration_list
        self.chem_name_to_label_dict_list = chem_name_to_label_dict_list
        self.active_states_list = active_states_list
        self.workers = workers
      
        #functionality  nedds to be added
        self.TA = TA
        self.known_spectra = known_spectra
        self.GPU = GPU