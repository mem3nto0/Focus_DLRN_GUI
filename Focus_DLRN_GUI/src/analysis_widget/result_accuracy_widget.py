from PySide6.QtWidgets import QWidget, QVBoxLayout, QLCDNumber

class ResultAccuracyWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout()

        self.digit_widget = QLCDNumber()
        self.digit_widget.setSegmentStyle(QLCDNumber.Flat)
        self.digit_widget.setDigitCount(4)  # Ensure enough digits including decimal
        self.digit_widget.setSmallDecimalPoint(True)
        #self.update_widget(0.0)
        layout.addWidget(self.digit_widget)
        self.setLayout(layout)

    def update_widget(self, num: float):
        self.digit_widget.display(f"{num:.3f}")
