from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QTextBrowser, QPushButton, QTabWidget
from .single_reaction_widget import SingleReactionWidget
import os
import numpy as np

class ReactionWidget(QWidget):
    reaction_widgets: list[SingleReactionWidget]
    stochio_matrix_list: list[list[list[int]]]


    def __init__(self,global_widget, parent=None):
        super().__init__(parent)
        self.reaction_widgets = []
        self.reaction_strings_list = []
        self.known_spectra_list = []
        self.concentration_list = []
        self.chem_name_to_label_dict_list= []
        self.active_states_list = []
        self.dark_state = False
        self.global_widget = global_widget

        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()
        self.reaction_tabs = QTabWidget()
        self.add_new_reaction()

        main_layout.addWidget(self.reaction_tabs, stretch=5)

        reaction_buttons_layout = QHBoxLayout()

        self.add_reaction_button = QPushButton("Add Model")
        self.add_reaction_button.pressed.connect(self.add_new_reaction)
        reaction_buttons_layout.addWidget(self.add_reaction_button)
    
        self.clone_reaction_button = QPushButton("Clone Model")
        self.clone_reaction_button.pressed.connect(self.clone_focussed_reaction)
        reaction_buttons_layout.addWidget(self.clone_reaction_button)
    
        self.remove_focussed_reaction_button = QPushButton("Remove Model")
        self.remove_focussed_reaction_button.pressed.connect(self.remove_focussed_reaction)
        reaction_buttons_layout.addWidget(self.remove_focussed_reaction_button)

        self.reaction_help_button = QPushButton("Help")
        self.reaction_help_button.pressed.connect(self.open_reaction_help)
        reaction_buttons_layout.addWidget(self.reaction_help_button)

        main_layout.addLayout(reaction_buttons_layout, stretch=1)
        self.setLayout(main_layout)

    def open_reaction_help(self):
        self.reaction_help_window = ReactionHelpWindow()
        self.reaction_help_window.show()

    def add_new_reaction(self):
        self.add_reaction_widget(SingleReactionWidget(self.global_widget))

    def clone_focussed_reaction(self):
        focussed_idx = self.reaction_tabs.currentIndex()
        focussed_reaction_widget = self.reaction_widgets[focussed_idx]
        self.add_reaction_widget(focussed_reaction_widget.clone())

    def add_reaction_widget(self, reaction_widet: SingleReactionWidget):
        n_reactions = len(self.reaction_widgets)
        if n_reactions < 5:
            self.reaction_widgets.append(reaction_widet)
            #self.reaction_matrix.append([])
            reaction_idx = n_reactions
            
            latest_tab_idx = self.reaction_tabs.addTab(self.reaction_widgets[reaction_idx], f"System Model {n_reactions+1}")

            self.reaction_tabs.setCurrentIndex(latest_tab_idx)

    def remove_focussed_reaction(self):
        if self.reaction_tabs.count() > 1:
            current_idx = self.reaction_tabs.currentIndex()
            self.reaction_tabs.removeTab(current_idx)
            self.reaction_widgets.pop(current_idx)
            #self.reaction_matrix.pop(current_idx)

            for i in range(self.reaction_tabs.count()):
                self.reaction_tabs.setTabText(i, f"System Model {i+1}")

    def collect_inputs(self):
        for i, reaction_widget in enumerate(self.reaction_widgets):
            #print("collecting input")
            #self.reaction_matrix[i] = reaction_widget.extract_reaction()
            chem_name_to_label, reaction_strings, concentrations, known_spectra, active_states = reaction_widget.extract_reaction()

            #get is A darkstate or not; only works if one inital A not multiple.... 
            #change !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            if "1" in active_states.keys():
                if active_states["A"] == False and active_states["1"] == False:
                    self.dark_state = True
                else:
                    self.dark_state = False
            else:
                if active_states["A"] == False:
                    self.dark_state = True
                else:
                    self.dark_state = False
             
         
            spectra_dict = {}
            for key in known_spectra.keys():
                if known_spectra[key] != None:
                    ext = os.path.splitext(known_spectra[key])[1]
                    if ext == '.csv':
                        spectra_dict[key] = np.loadtxt(known_spectra[key], delimiter=';')
                    elif ext in ['.txt', '.dat']:
                        spectra_dict[key] = np.loadtxt(known_spectra[key])
                    #else:
                        #raise ValueError(f"Unsupported file extension: {ext}")
            self.reaction_strings_list.append(reaction_strings)
            self.known_spectra_list.append(spectra_dict)
            self.concentration_list.append(concentrations)
            self.chem_name_to_label_dict_list.append(chem_name_to_label)
            self.active_states_list.append(active_states)

    def forget_inputs(self):
        #self.reaction_widgets = []
        self.reaction_strings_list = []
        self.known_spectra_list = []
        self.concentration_list = []
        self.chem_name_to_label_dict_list = []
        self.active_states_list = []
       
    
    #def start_training(self):
     #   pass

class ReactionHelpWindow(QWidget):

    HELPTEXT = """
    <h2>Add Chemical</h2>
    Drag from the placeholder onto the canvas.
    <h2>Edit Chemical</h2>
    Left click on chemical, edit in the fields above & press update
    <h2>Remove Chemical</h2>
    Left click on chemical & press remove above
    <h2>Add reaction</h2>
    Right click on reactant, then left click on product
    <h2>Remove reaction</h2>
    Right click on the arrow to remove it.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        # Place the help text in a Groupbox 
        help_text = QTextBrowser()
        help_text.insertHtml(self.HELPTEXT)
        layout.addWidget(help_text)
        self.setLayout(layout)
        self.setWindowTitle("Reaction help")
        self.setMinimumHeight(450)
