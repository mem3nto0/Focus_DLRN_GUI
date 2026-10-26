import math
from uuid import UUID
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPoint, Signal, Slot
from PySide6.QtGui import (QMouseEvent, QPaintEvent, QPainter, 
                           QColor, QPen, QBrush, QPolygon, QCursor)

from reaction_widget.reaction_chemical import Chemical, Plus

def identify_educts(reac, chem_to_plus):
        plus_id  = reac[0]
        educts = []
        for c_to_p in chem_to_plus:
            if plus_id == c_to_p[1]:
                educts.append(c_to_p[0])
        return educts

class ReactionCanvas(QWidget):
    """
    A QWidget for visually arranging and connecting `Chemical` widgets.

    Attributes:
        chemicals (dict[UUID, Chemical]): Dictionary of chemicals currently on the canvas.
        currently_selected_id (UUID | None): UUID of the currently selected chemical.
                                             None if no chemical is selected
        connections (list[tuple[UUID, UUID]]): List of connections (arrows) between chemicals.
        signal_selection_changed (Signal): Emitted when a new chemical is selected or deselected.
                                           Used to communicate with the ChemicalUpdateWidget
    """
    # tracks the present chemicals
    chemicals: dict[UUID, Chemical]
    # tracks the present plus elements
    pluses: dict[UUID, Plus]

    default_labels: str = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    drag_start_position: QPoint

    currently_selected_id: UUID|None
    connections: list[tuple[UUID, UUID]]
    connection_start_id: UUID|None

    signal_selection_changed = Signal(Chemical)

    def __init__(self, parent: QWidget|None = None):
        super().__init__(parent)
        self.setMouseTracking(True)

        self.setAcceptDrops(True)
        self.setAutoFillBackground(True)

        self.chemicals = {}
        self.pluses = {}
        self.currently_selected_id = None

        self.connections = []
        self.connection_start_id = None


    # --- Drag-and-Drop Handling ---

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        pos = event.position().toPoint()
        widget = event.source()
        if type(widget) == Chemical and widget.node_id not in self.chemicals.keys():
            # If widget is coming from outside, create a new one
            self.add_node(pos, plus=False)
        elif type(widget) == Plus and widget.node_id not in self.pluses.keys():
            self.add_node(pos, plus=True)
        else:
            # If widget is already in our container, just move it
            widget.move(pos)
            
        event.acceptProposedAction()

        # Update the lines
        self.update()


    # --- Mouse Interaction ---

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handles deselection or connection removal on mouse click."""
        self.remove_selection()
        self.cancel_connection()

        if event.button() == Qt.MouseButton.RightButton:
            self.check_remove_connection(event.pos())

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Triggers repaint when drawing an arrow."""
        if self.connection_start_id:
            self.update()  # Trigger repaint to show the arrow being drawn


    # --- Paint and Drawing ---

    def paintEvent(self, event: QPaintEvent) -> None:
        """Draws arrows representing connections between chemicals."""
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # draw present arrows
        for start_id, end_id in self.connections:
            start_point = self.get_node_center(start_id)
            end_point = self.get_node_center(end_id)

            self.draw_connection(painter, start_point, end_point)

        # draw started arrow betweet start and mouse cursor
        if self.connection_start_id:
            start_point = self.get_node_center(self.connection_start_id)
            cursor_pos = self.mapFromGlobal(QCursor.pos())

            self.draw_connection(painter, start_point, cursor_pos)

    def draw_connection(self, painter: QPainter, start_point: QPoint, end_point: QPoint):
        """Draws a line and arrowheads between two points."""
        pen = QPen(QColor("#007bff"), 2)
        painter.setPen(pen)
        
        # draw the line of the arrow
        painter.drawLine(start_point, end_point)

        # draw arrow heads at the 30%, 55% and 80% length
        arrow_angle = math.atan2(end_point.y() - start_point.y(), end_point.x() - start_point.x())

        arrow_point_positions = self.get_arrow_point_positions(start_point, end_point)
        for point in arrow_point_positions:
            self.draw_arrow_head(painter, point, arrow_angle)

    def draw_arrow_head(self, painter: QPainter, head_point: QPoint, angle: float):
        """Draws an arrowhead at a specific point and angle."""
        arrow_size = 10
        arrow_p1 = QPoint(
            int(head_point.x() - arrow_size * math.cos(angle - math.pi/6)),
            int(head_point.y() - arrow_size * math.sin(angle - math.pi/6))
        )
        arrow_p2 = QPoint(
            int(head_point.x() - arrow_size * math.cos(angle + math.pi/6)),
            int(head_point.y() - arrow_size * math.sin(angle + math.pi/6))
        )

        arrow_head = QPolygon([head_point, arrow_p1, arrow_p2])
        painter.setBrush(QBrush(QColor("#007bff")))
        painter.drawPolygon(arrow_head)

    def get_arrow_point_positions(self, start_point: QPoint, end_point: QPoint) -> tuple[QPoint, QPoint, QPoint]:
        """Returns positions at 30%, 55%, and 80% of the line length between two points."""        
        # Calculate vector from start to end
        dx = end_point.x() - start_point.x()
        dy = end_point.y() - start_point.y()
        
        # Calculate points at 30%, 55%, and 80% along the line
        point_30 = QPoint(
            int(start_point.x() + 0.3 * dx),
            int(start_point.y() + 0.3 * dy)
        )
        
        point_55 = QPoint(
            int(start_point.x() + 0.55 * dx),
            int(start_point.y() + 0.55 * dy)
        )
        
        point_80 = QPoint(
            int(start_point.x() + 0.8 * dx),
            int(start_point.y() + 0.8 * dy)
        )
        
        return (point_30, point_55, point_80)

    def get_node_center(self, node_id: UUID) -> QPoint:
        """Returns the center point of a chemical widget."""
        node = self.chemicals[node_id] if node_id in self.chemicals.keys() else self.pluses[node_id]
        rect = node.geometry()
        return QPoint(rect.x() + rect.width() // 2, rect.y() + rect.height() // 2)


    # --- Widget Management ---

    def add_node(self, pos: QPoint, plus: bool):
        """
        Adds a node (chemical or plus) to the canvas
        """
        node = Plus(self) if plus else Chemical(self.get_placeholder_label(), self)
        node.signal_clicked_left.connect(self.update_selected)
        node.signal_clicked_right.connect(self.start_connection)
        node.move(pos)
        node.show()

        if plus:
            self.pluses[node.node_id] = node # type: ignore
        else:
            self.chemicals[node.node_id] = node # type: ignore

        self.update_selected(node.node_id)

    def get_placeholder_label(self) -> str:
        """Returns a label for the next chemical, using a fixed alphabet."""
        index = len(self.chemicals)
        return self.default_labels[index % len(self.default_labels)]
    
    @Slot(UUID)
    def remove_chemical(self, node_id: UUID):
        """Removes a chemical and its connections."""
        self.remove_connections_containing(node_id)
        self.currently_selected_id = None
        
        if self.connection_start_id:
            self.connection_start_id = None
        
        if node_id in self.chemicals.keys():
            self.chemicals[node_id].hide()
            del(self.chemicals[node_id])
        elif node_id in self.pluses.keys():
            self.pluses[node_id].hide()
            del(self.pluses[node_id])

        self.update()


    # --- Selection and Connection Logic ---

    @Slot(UUID)
    def update_selected(self, node_id: UUID):
        """
        Handles the selection of a Chemical and the reset of
        a selection. 
        
        If a Chemical is clicked, it becomes the
        selected Chemical. Then the information is sent to 
        the ChemicalUpdateWidget to allow for changes of the 
        Chemical by the user.

        In case of a de-selection the method is invoked from 
        self.mousePressEvent without a node_id. In this case
        the ChemicalUpdateWidget gets reset.
        """
        # connection_start_id == None -> The user wants to select the Chemical
        if not self.connection_start_id:
            # Reset the style of the previously selected Chemical
            if self.currently_selected_id:
                self.get_currently_selected().change_style(selected=False) # type: ignore if statement makes sure it exists

            self.currently_selected_id = node_id

            selected = self.get_currently_selected()
            selected.change_style(selected=True) # type: ignore
            self.signal_selection_changed.emit(selected)
        # connection_start_id not None -> The user wants to finish a connection
        else:
            self.finish_connection(node_id)

        self.update()

    def remove_selection(self):
        """Deselects the currently selected chemical."""
        if self.currently_selected_id:
            self.get_currently_selected().change_style(False) # type: ignore
            self.signal_selection_changed.emit(None)
            self.currently_selected_id = None

    def get_currently_selected(self) -> Chemical|Plus|None:
        """Returns the currently selected chemical widget."""
        if self.currently_selected_id:
            if self.currently_selected_id in self.chemicals.keys():
                return self.chemicals[self.currently_selected_id]
            if self.currently_selected_id in self.pluses.keys():
                return self.pluses[self.currently_selected_id]
        return None
    
    @Slot(UUID)
    def start_connection(self, start_id: UUID):
        """Starts a connection from a chemical."""
        self.connection_start_id = start_id

    def finish_connection(self, end_id: UUID):
        """Creates a connection between two chemicals."""
        # should always be the case when the method is called
        if self.connection_start_id:
            connection = (self.connection_start_id, end_id)
            if connection[0] in self.pluses.keys() and connection[1] in self.pluses.keys():
                raise Exception("Invalid connection - connection between two pluses not allowed!")
            elif connection not in self.connections:
                self.connections.append(connection)
            self.connection_start_id = None

    def cancel_connection(self):
        """Cancels a connection in progress."""
        if self.connection_start_id:
            self.connection_start_id = None
            self.update()

    def remove_connections_containing(self, chem_id: UUID):
        """Removes all connections involving the given chemical."""
        self.connections = [
            (start_id, end_id) 
            for (start_id, end_id) in self.connections 
            if start_id != chem_id and end_id != chem_id
        ]

    def check_remove_connection(self, click_position: QPoint, threshold: float = 10):
        """Removes a connection if the click is near one."""
        for start_id, end_id in self.connections:
            start_point = self.get_node_center(start_id)
            end_point = self.get_node_center(end_id)

            dist = self.calc_distance_to_point(
                click_position,
                start_point,
                end_point
            )
            if dist < threshold:
                self.connections.remove((start_id, end_id))
                self.update()
                return

    def calc_distance_to_point(self, point: QPoint, line_start: QPoint, line_end: QPoint) -> float:
        """Calculates perpendicular distance from a point to a line segment."""
        # Convert to vectors
        ax, ay = line_start.x(), line_start.y()
        bx, by = line_end.x(), line_end.y()
        px, py = point.x(), point.y()

        # Vector from a to b
        abx = bx - ax
        aby = by - ay

        # Vector from a to point
        apx = px - ax
        apy = py - ay

        # Cross product magnitude
        cross = abs(abx * apy - aby * apx)

        # Length of vector ab
        ab_length = math.hypot(abx, aby)

        # Distance from point to line
        if ab_length == 0:
            return math.hypot(apx, apy)  # a and b are the same point

        return cross / ab_length

    

    def extract_data(self): #changed
        """
        Converts the present connections to a vector representation of the current reaction
        """
        chem_to_plus = []
        plus_to_chem = []
        chem_to_chem = []
        reactions = []
        duplicate_chemicals ={}
        unique_chem =[]
        
        chemical_ids = self.chemicals.keys()
        plus_ids = self.pluses.keys()
  

        for connection in self.connections:
            if connection[0] in chemical_ids and connection[1] in plus_ids:
   
                chem_to_plus.append(connection)
                if self.chemicals[connection[0]].label in duplicate_chemicals.keys():

                    duplicate_chemicals[self.chemicals[connection[0]].label].append(connection[0])

                else:
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

                if self.chemicals[connection[0]].label in duplicate_chemicals.keys() and (not duplicate_chemicals or all(connection[0] not in v for v in duplicate_chemicals.values())):
                    duplicate_chemicals[self.chemicals[connection[0]].label].append(connection[0])

                if self.chemicals[connection[0]].label not in duplicate_chemicals.keys() and (not duplicate_chemicals or all(connection[0] not in v for v in duplicate_chemicals.values())):
                    duplicate_chemicals[self.chemicals[connection[0]].label] = [connection[0]]
                    unique_chem.append(connection[0])

                if self.chemicals[connection[1]].label in duplicate_chemicals.keys() and (not duplicate_chemicals or all(connection[1] not in v for v in duplicate_chemicals.values())):
                    duplicate_chemicals[self.chemicals[connection[1]].label].append(connection[1])

                if self.chemicals[connection[1]].label not in duplicate_chemicals.keys() and (not duplicate_chemicals or all(connection[1] not in v for v in duplicate_chemicals.values())):
                    unique_chem.append(connection[1])
                    duplicate_chemicals[self.chemicals[connection[1]].label] = [connection[1]]

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