#%%

class Chemical(): 
    label: str
    concentration: float
    spectrum_path: str|None
    is_active: bool

    def __init__(self,label,conc,spec,active):
        self.label = label  
        self.concentration = conc
        self.spectrum_path = spec
        self.is_active = active

class ReactionCanvas():

    # tracks the present chemicals
    #dict[UUID, Chemical]
    chemicals: dict[str, Chemical]
    # tracks the present plus elements
    #id,"+"
    pluses: dict[str, str]

    connections: list[tuple[str, str]]

    def __init__(self):
        self.chemicals = {}
        self.pluses = {}
        self.connections = []
            
def identify_educts(reac, chem_to_plus):
    plus_id  = reac[0]
    educts = []
    for c_to_p in chem_to_plus:
        if plus_id == c_to_p[1]:
            educts.append(c_to_p[0])
    return educts

def extract_data(self): #changed
        """
        Converts the present connections to a vector representation of the current reaction
        """
        chem_to_plus = []
        plus_to_chem = []
        chem_to_chem = []
        reactions = []
        #chemical_names_to_plus = []
        duplicate_chemicals ={}
        unique_chem =[]
        
        chemical_ids = self.chemicals.keys()
        plus_ids = self.pluses.keys()
        #print(chemical_ids)

        for connection in self.connections:
            if connection[0] in chemical_ids and connection[1] in plus_ids:
                #check if multiple molecules of the same chemical react togather
                #if self.chemicals[connection[0]].label in chemical_names_to_plus:
                chem_to_plus.append(connection)
                if self.chemicals[connection[0]].label in duplicate_chemicals.keys():
                    #duplicate_chemicals[self.chemicals[connection[0]].label][0] += 1
                    duplicate_chemicals[self.chemicals[connection[0]].label].append(connection[0])
                    #else:
                        #print(self.chemicals[connection[0]])
                        #print(self.chemicals[connection[0]].label)
                        #duplicate_chemicals[self.chemicals[connection[0]].label] = (2,[connection[0]])
                else:
                    #print(connection)
                    #chemical_names_to_plus.append(self.chemicals[connection[0]].label)
                    unique_chem.append(connection[0])
                    duplicate_chemicals[self.chemicals[connection[0]].label] = [connection[0]]
                
            elif connection[0] in plus_ids and connection[1] in chemical_ids:
                plus_to_chem.append(connection)
                reactions.append(connection)
                if self.chemicals[connection[1]].label in duplicate_chemicals.keys() and (not duplicate_chemicals or all(connection[1] not in v for v in duplicate_chemicals.values())):
                    duplicate_chemicals[self.chemicals[connection[1]].label].append(connection[1])
                elif self.chemicals[connection[1]].label not in duplicate_chemicals.keys() and (not duplicate_chemicals or all(connection[1] not in v for v in duplicate_chemicals.values())):
                    unique_chem.append(connection[1])
                    duplicate_chemicals[self.chemicals[connection[1]].label] = [connection[1]]
  
            elif connection[0] in chemical_ids and connection[1] in chemical_ids:
                chem_to_chem.append(connection)
                reactions.append(connection)
                #print(connection[0],connection[1])
                #print(duplicate_chemicals)
                
                if self.chemicals[connection[0]].label in duplicate_chemicals.keys() and (not duplicate_chemicals or all(connection[0] not in v for v in duplicate_chemicals.values())):
                    duplicate_chemicals[self.chemicals[connection[0]].label].append(connection[0])
                    #print("1")
                if self.chemicals[connection[0]].label not in duplicate_chemicals.keys() and (not duplicate_chemicals or all(connection[0] not in v for v in duplicate_chemicals.values())):
                    duplicate_chemicals[self.chemicals[connection[0]].label] = [connection[0]]
                    unique_chem.append(connection[0])
                    #print("2")
                if self.chemicals[connection[1]].label in duplicate_chemicals.keys() and (not duplicate_chemicals or all(connection[1] not in v for v in duplicate_chemicals.values())):
                    duplicate_chemicals[self.chemicals[connection[1]].label].append(connection[1])
                    #print("3")
                if self.chemicals[connection[1]].label not in duplicate_chemicals.keys() and (not duplicate_chemicals or all(connection[1] not in v for v in duplicate_chemicals.values())):
                    unique_chem.append(connection[1])
                    duplicate_chemicals[self.chemicals[connection[1]].label] = [connection[1]]
                    #print("4")
                #unique_chem.append(connection[0])
                #unique_chem.append(connection[1])
            
        print("chem_to_plus:")
        print(chem_to_plus)

        print("\nplus_to_chem:")
        print(plus_to_chem)

        print("\nchem_to_chem:")
        print(chem_to_chem)

        print("\nreactions:")
        print(reactions)

        print("\nduplicate_chemicals:")
        print(duplicate_chemicals)

        print("\nunique_chem:")
        print(unique_chem)

       

        #print(unique_chem)        
        n_chemicals = len(unique_chem)
        #print(n_chemicals)
        

        full_reactions = []

        for reac in reactions:
            if reac[0] not in plus_ids:
                full_reactions.append({"educts":[reac[0]],"product":reac[1]})
            else:
                #identify which products are conncted by +
                educts = identify_educts(reac,chem_to_plus)
                full_reactions.append({"educts":educts,"product":reac[1]})

        #identifing non-formed chemicals
        #will be updated, chem gets  deleted  if being ever an product 
        initial_chem = unique_chem
        for reac in full_reactions:
            product = reac["product"]
            if product in initial_chem:
                initial_chem.remove(product)

        #identify starting reaction
        starting_reactions = []
        for reac in full_reactions:
            is_start = True
            for educt in reac["educts"]:
                if educt not in initial_chem:
                    is_start = False
                    break
            if is_start == True:
                starting_reactions.append(reac) 

        followup_reactions = [
                reaction for reaction in full_reactions
                if reaction not in starting_reactions
            ]
        #############fill reaction strings###########
        #G = Ground State
        main_chem_names = ["A","B","C","D","G"]
        side_chem_names = [f"{i+1}" for i in range(5)]
        chemical_dict = {}
        reaction_strings = []
        print(starting_reactions[0])
        #identify A 
        if len(starting_reactions)>1:
            chem_count_dict = {}
            for reac in starting_reactions:
                for e in reac["educts"]: 
                    if e not in chem_count_dict:
                        chem_count_dict[e] = 1
                    else:
                        chem_count_dict[e] += 1
            for e in chem_count_dict.keys():
                A_found = False
                if chem_count_dict[e] > 1:
                    chemical_dict[e] = main_chem_names[0]
                    main_chem_names.remove(main_chem_names[0])
                    #add site reac names and products
                    for reac in starting_reactions:
                        for educt in reac["educts"]:
                            if educt not in chemical_dict.keys():
                                chemical_dict[educt] = side_chem_names[0]
                                side_chem_names.remove(side_chem_names[0])
                        if reac["product"] not in chemical_dict.keys():
                            chemical_dict[reac["product"]] = main_chem_names[0]
                            main_chem_names.remove(main_chem_names[0])
                    A_found = True
                    break
            if A_found == False:
                #Two initial reactions occur
                chemical_dict[starting_reactions[0]["educts"][0]] = main_chem_names[0]
                main_chem_names.remove(main_chem_names[0])
                if len(starting_reactions[0]["educts"]) > 1:
                    chemical_dict[starting_reactions[0]["educts"][1]] = side_chem_names[0]
                    side_chem_names.remove(side_chem_names[0])

                chemical_dict[starting_reactions[1]["educts"][0]] = main_chem_names[0]
                main_chem_names.remove(main_chem_names[0])
                if len(starting_reactions[0]["educts"]) > 1:
                    chemical_dict[starting_reactions[1]["educts"][1]] = side_chem_names[0]
                    side_chem_names.remove(side_chem_names[0])
                chemical_dict[starting_reactions[0]["product"]] = main_chem_names[0]
                main_chem_names.remove(main_chem_names[0])
                if starting_reactions[1]["product"] not in chemical_dict.keys():
                    chemical_dict[starting_reactions[1]["product"]] = main_chem_names[0]
                    main_chem_names.remove(main_chem_names[0])
        else:
            chemical_dict[starting_reactions[0]["educts"][0]] = main_chem_names[0]
            main_chem_names.remove(main_chem_names[0])
            if len(starting_reactions[0]["educts"]) > 1:
                chemical_dict[starting_reactions[0]["educts"][1]] = side_chem_names[0]
                side_chem_names.remove(side_chem_names[0])
            chemical_dict[starting_reactions[0]["product"]] = main_chem_names[0]
            main_chem_names.remove(main_chem_names[0])

        #product naming
        for reac in followup_reactions:
            product = reac["product"]
            if product not in chemical_dict.keys():
                chemical_dict[product] = main_chem_names[0]
                main_chem_names.remove(main_chem_names[0])

        #Site educt naming
        for reac in followup_reactions:
            educts = reac["educts"]
            for e in educts:
                if e not in chemical_dict.keys():
                    chemical_dict[e] = side_chem_names[0]
                    side_chem_names.remove(side_chem_names[0])

        #create strings
        for reac in full_reactions:
            if len(reac["educts"])>1:
                reaction_strings.append(f"{chemical_dict[reac['educts'][0]]} + {chemical_dict[reac['educts'][1]]} -> {chemical_dict[reac['product']]}")
            else:
                reaction_strings.append(f"{chemical_dict[reac['educts'][0]]} -> {chemical_dict[reac['product']]}")

        known_spectra = {}
        concentrations = {}
        active_states = {}
        chem_name_to_label ={}

        for chemical_id in chemical_dict.keys():
            label = self.chemicals[chemical_id].label
            chem_name_to_label[chemical_dict[chemical_id]] = label
            concentrations[chemical_dict[chemical_id]] = self.chemicals[chemical_id].concentration
            known_spectra[chemical_dict[chemical_id]] = self.chemicals[chemical_id].spectrum_path
            active_states[chemical_dict[chemical_id]] = self.chemicals[chemical_id].is_active
        print(chem_name_to_label)
        print(reaction_strings)
        print(concentrations)
        print(known_spectra)
        print(active_states)

        return chem_name_to_label, reaction_strings, concentrations, known_spectra, active_states






            
                

      
# chemicals = {
#     "A_": Chemical(
#         label="Start",
#         conc=1.0,
#         spec=None,
#         active=False
#     ),
#     "1_": Chemical(
#         label="Start_left",
#         conc=0.5,
#         spec=None,
#         active=False
#     ),
#     "2_": Chemical(
#         label="Start_right",
#         conc=0.5,
#         spec=None,
#         active=False
#     ),
#     "B_": Chemical(
#         label="Middle_left",
#         conc=0,
#         spec=None,
#         active=True
#     ),
#     "C_": Chemical(
#         label="Middle_right",
#         conc=0,
#         spec=None,
#         active=True
#     ),
#     "3_": Chemical(
#         label="end_reac",
#         conc=0.5,
#         spec=None,
#         active=False
#     ),
#     "D_": Chemical(
#         label="output",
#         conc=0,
#         spec=None,
#         active=True
#     ),
# }

# # Create a reaction canvas
# canvas = ReactionCanvas()

# # Add chemicals
# canvas.chemicals=chemicals

# # Add plus signs
# canvas.pluses = {
#     "plus_1": "+",
#     "plus_2": "+",
#     "plus_3": "+",
#     "plus_4": "+"
# }

# # Define connections between elements
# canvas.connections = [
#     ("A_", "plus_1"),
#     ("A_", "plus_2"),
#     ("1_", "plus_1"),
#     ("2_", "plus_2"),
#     ("plus_1","B_"),
#     ("plus_2","C_"),
#     ("B_", "plus_3"),
#     ("3_", "plus_3"),
#     ("C_", "plus_4"),
#     ("3_", "plus_4"),
#     ("plus_3","D_"),
#     ("plus_4","D_")]   

# chemicals = {
#     "A_": Chemical(
#         label="Start",
#         conc=1.0,
#         spec=None,
#         active=False
#     ),

#     "B_": Chemical(
#         label="Middle_left",
#         conc=0,
#         spec=None,
#         active=True
#     ),

# }

# # Create a reaction canvas
# canvas = ReactionCanvas()

# # Add chemicals
# canvas.chemicals=chemicals

# # Add plus signs
# canvas.pluses = {
# }

# # Define connections between elements
# canvas.connections = [
#     ("A_", "B_"),
#     ]   


# #print(canvas.connections)

# extract_data(canvas)

chemicals = {
    "A_": Chemical(
        label="Start",
        conc=1.0,
        spec=None,
        active=False
    ),

    "B_": Chemical(
        label="Start_help",
        conc=2,
        spec=None,
        active=True
    ),
    "C_": Chemical(
            label="Product",
            conc=0,
            spec=None,
            active=True
        ),
}

pluses = {
     "plus_1": "+",
 }


# Create a reaction canvas
canvas = ReactionCanvas()

# Add chemicals
canvas.chemicals=chemicals

# Add plus signs
canvas.pluses = pluses

# Define connections between elements
canvas.connections = [
    ("A_", "plus_1"),
    ("B_", "plus_1"),
    ("plus_1", "C_"),
    ]   


#print(canvas.connections)

extract_data(canvas)
      