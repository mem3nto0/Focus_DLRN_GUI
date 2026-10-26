from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import Qt

class Progress_Report_Widget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(2)
        self.setLayout(self.layout)
        

    def update_widget(self, status: str):
        label = QLabel(status, self)
        label.setAlignment(Qt.AlignCenter)
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.layout.addWidget(label)
        