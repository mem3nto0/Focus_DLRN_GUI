from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import Qt
import numpy as np

class ResultReactionConstantsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)


    def stochiomatrix_to_dict(self,stochiomatrix,species_names):
        stochiomatrix = np.asarray(stochiomatrix)
        n_species, n_reactions = stochiomatrix.shape
        reaction_dicts = []

        # Extract basic reaction info and build maps
        for j in range(n_reactions):
            reactants = []
            product = ""

            for i in range(n_species):
                coeff = stochiomatrix[i, j]
                sp = species_names[i]
                if coeff < 0:
                    if coeff < -1:
                        reactants.append(str(abs(coeff))+sp)
                    else:
                        reactants.append(sp)
                elif coeff > 0:
                    product = sp
                    
            reaction_dicts.append({
                "reactants": reactants,
                "product": product   
            })
        return reaction_dicts

    def update_widget(self,stoch_matrix,species_names,rate_constants):
        reaction_dicts = self.stochiomatrix_to_dict(stoch_matrix,species_names)
        for reaction in reaction_dicts:
            for i,component in enumerate(reaction["reactants"]):
                if i == 0:
                    text = component 
                else:
                    text = "+ " + component
            text = text + " --> " + reaction["product"] + ": " + str(1/rate_constants[i])

            label = QLabel(text, self)
            label.setAlignment(Qt.AlignCenter)
            label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.layout.addWidget(label)

        # Add stretch to evenly distribute space
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)

