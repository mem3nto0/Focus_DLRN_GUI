import uuid
from uuid import UUID
from PySide6.QtWidgets import QApplication, QLabel
from PySide6.QtCore import Qt, QMimeData, Signal
from PySide6.QtGui import QDrag


class ReactionNode(QLabel):
    """
    A widget representing an element shown in the reaction canvas.

    Attributes:
        node_id (UUID): Unique identifier for the node.
        signal_clicked_left (Signal): Emitted when the node is left-clicked.
        signal_clicked_right (Signal): Emitted when the node is right-clicked.
    """
    node_id: UUID

    signal_clicked_left: Signal = Signal(UUID)
    signal_clicked_right: Signal = Signal(UUID)

    def __init__(self, parent = None):
        super().__init__(parent)

        self.setAutoFillBackground(True)
        self.setMinimumWidth(50)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.change_style(selected=False)

        self.node_id = uuid.uuid1()

    def change_style(self, selected: bool):
        """
        Changes the visual style of the node based on its selection state.

        Args:
            selected (bool): Whether the node is selected.
        """
        if selected:
            style = "background-color: #cce5ff; color: black; border: 2px solid #007bff; border-radius: 5px; padding: 5px;"
        else:
            style = "background-color: white; color: black; border: 1px solid black; border-radius: 5px; padding: 5px;"
        self.setStyleSheet(style)

    def mousePressEvent(self, event):
        """
        Handles mouse press events. Emits signals based on the button pressed.

        Args:
            event (QMouseEvent): The mouse event.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.pos()
            self.signal_clicked_left.emit(self.node_id)

        elif event.button() == Qt.MouseButton.RightButton:
            self.signal_clicked_right.emit(self.node_id)

    def mouseMoveEvent(self, event):
        """
        Initiates a drag operation if the mouse has moved sufficiently from the start position.

        Args:
            event (QMouseEvent): The mouse event.
        """
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
            
        # Check if the distance is far enough to start a drag
        if (event.pos() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return
            
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText("draggable")
        drag.setMimeData(mime_data)
        
        # Create a pixmap of the widget for visual feedback during drag
        pixmap = self.grab()
        drag.setPixmap(pixmap)
        drag.setHotSpot(event.pos())
        
        # Execute the drag
        drag.exec_(Qt.DropAction.MoveAction)


class Chemical(ReactionNode): 
    """
    A widget representing a chemical entity in the reaction canvas.

    Attributes:
        label (str): Label representing the chemical's name.
        spectrum_path (str | None): Path to the chemical's spectrum (optional).
    """
    label: str
    concentration: float
    spectrum_path: str|None
    is_active: bool

    def __init__(self, label, parent=None): 
        """
        Initializes the chemical widget with a label and default style.
        
        Args:
            label (str): The label for the chemical.
            parent (QWidget, optional): Parent widget. Defaults to None.
        """
        super().__init__(parent)

        self.update_label(label)
        self.concentration = 0
        self.spectrum_path = None
        self.is_active = True

    def update_label(self, label: str):
        """
        Updates the chemical's label and adjusts its size accordingly.

        Args:
            label (str): New label for the chemical.
        """
        self.label = label
        self.setText(label)
        self.adjustSize()

    def update_info(self, label: str|None, concentration: float|None, spectrum_path: str|None, is_active: bool):
        """
        Updates the chemical's label, its spectrum path and whether it is active.

        Args:
            label (str): New label for the chemical.
            spectrum_path (str): Path to the spectrum associated with the chemical.
        """
        if label:
            self.update_label(label)
        if concentration:
            self.concentration = concentration
        if spectrum_path:
            self.spectrum_path = spectrum_path

        self.is_active = is_active


class Plus(ReactionNode):
    """
    A widget representing a Plus entity in the reaction canvas.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText("+")

    