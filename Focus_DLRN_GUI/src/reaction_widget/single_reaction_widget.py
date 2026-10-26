import sys
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QGroupBox
from PySide6.QtCore import Signal, Slot

from reaction_widget.reaction_canvas import ReactionCanvas
from reaction_widget.reaction_chemical import Chemical, Plus
from reaction_widget.reaction_chemical_update import ChemicalUpdateWidget

class SingleReactionWidget(QWidget):
    canvas: ReactionCanvas
    placeholder_chemical: Chemical
    chemical_updater: ChemicalUpdateWidget
    chemicals: list[Chemical]

    signal_reaction_confirmed = Signal(list)

    def __init__(self,global_widget, parent=None):
        super().__init__(parent)
        self.chemicals = []
        self.global_widget = global_widget
        self.initUI()

    def initUI(self):
        # Place the canvas in a GroupBox
        group_box_canvas = QGroupBox("Reaction Canvas")
        group_box_canvas_layout = QVBoxLayout()
        self.canvas = ReactionCanvas()
        self.canvas.signal_selection_changed.connect(self.update_chemical_updater)
        group_box_canvas_layout.addWidget(self.canvas)
        group_box_canvas.setLayout(group_box_canvas_layout)

        # Place the placeholder Chemical in a GroupBox
        group_box_new = QGroupBox("Add new chemical")
        group_box_new_layout = QVBoxLayout()
        self.placeholder_chemical = Chemical("Placeholder")
        self.plus_chemical = Plus()
        group_box_new_layout.addWidget(self.placeholder_chemical, stretch=3)
        group_box_new_layout.addWidget(self.plus_chemical, stretch=1)
        group_box_new.setLayout(group_box_new_layout)

        # Place the chemical updater in a Groupbox 
        group_box_selected = QGroupBox("Edit selected chemical")
        group_box_selected_layout = QVBoxLayout()
        self.chemical_updater = ChemicalUpdateWidget(self.global_widget)
        self.chemical_updater.signal_remove_selected.connect(self.canvas.remove_chemical)
        group_box_selected_layout.addWidget(self.chemical_updater)
        group_box_selected.setLayout(group_box_selected_layout)

        # Sub-layout on the right of the widget 
        sub_layout = QVBoxLayout()
        sub_layout.addWidget(group_box_new)
        sub_layout.addWidget(group_box_selected)

        # Main layout of the widget
        layout = QHBoxLayout()
        layout.addWidget(group_box_canvas, stretch=3)
        layout.addLayout(sub_layout, stretch=1)

        self.setLayout(layout)

    @Slot(Chemical)
    def update_chemical_updater(self, selected: Chemical):
        self.chemical_updater.change_selected(selected)

    def extract_reaction(self): #changed
        reaction_data = self.canvas.extract_data()
        return reaction_data

    def clone(self):
        """
        Creates a shallow copy of this ReactionWidget instance.
        Returns a new ReactionWidget with the same chemical layout and connections.
        """
        new_widget = SingleReactionWidget(self.global_widget,self.parent())
        
        # First, add all chemicals in the same positions
        for chem_id, chemical in self.canvas.chemicals.items():
            pos = chemical.pos()
            new_chemical = Chemical(chemical.label, new_widget.canvas)
            new_chemical.move(pos)
            new_chemical.signal_clicked_left.connect(new_widget.canvas.update_selected)
            new_chemical.signal_clicked_right.connect(new_widget.canvas.start_connection)
            new_chemical.show()
            
            # Copy chemical properties
            new_chemical.concentration = chemical.concentration
            new_chemical.spectrum_path = chemical.spectrum_path
            new_chemical.is_active = chemical.is_active
            
            # Store in the new canvas
            new_widget.canvas.chemicals[new_chemical.node_id] = new_chemical
        
        # Add all plus signs in the same positions
        for plus_id, plus in self.canvas.pluses.items():
            pos = plus.pos()
            new_plus = Plus(new_widget.canvas)
            new_plus.move(pos)
            new_plus.signal_clicked_left.connect(new_widget.canvas.update_selected)
            new_plus.signal_clicked_right.connect(new_widget.canvas.start_connection)
            new_plus.show()
            
            # Store in the new canvas
            new_widget.canvas.pluses[new_plus.node_id] = new_plus
        
        # Create a mapping from old IDs to new IDs for proper connection copying
        old_to_new_id_map = {}
        
        # Map chemical IDs
        old_chem_ids = list(self.canvas.chemicals.keys())
        new_chem_ids = list(new_widget.canvas.chemicals.keys())
        for i in range(len(old_chem_ids)):
            old_to_new_id_map[old_chem_ids[i]] = new_chem_ids[i]
        
        # Map plus IDs
        old_plus_ids = list(self.canvas.pluses.keys())
        new_plus_ids = list(new_widget.canvas.pluses.keys())
        for i in range(len(old_plus_ids)):
            old_to_new_id_map[old_plus_ids[i]] = new_plus_ids[i]
        
        # Copy connections using the ID mapping
        for start_id, end_id in self.canvas.connections:
            if start_id in old_to_new_id_map and end_id in old_to_new_id_map:
                new_start_id = old_to_new_id_map[start_id]
                new_end_id = old_to_new_id_map[end_id]
                new_widget.canvas.connections.append((new_start_id, new_end_id))
        
        # Update the canvas to draw the connections
        new_widget.canvas.update()
        
        return new_widget