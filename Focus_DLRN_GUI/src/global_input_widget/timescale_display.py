from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView
from PySide6.QtCore import Qt

class TimescaleWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMaximumHeight(120)
        layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setRowCount(1)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)

        self.clear_table()

        layout.addWidget(self.table)
        self.setLayout(layout)

    def update_table(self, data: list[float]):
        self.table.clear()
        self.table.setColumnCount(len(data))
        self.table.setRowCount(1)
        for i, el in enumerate(data):
            item = QTableWidgetItem(f"{el:.6g}")
            self.table.setItem(0, i, item)

    def clear_table(self):
        self.table.clear()
        self.table.setColumnCount(1)
        self.table.setRowCount(1)
        self.table.setItem(0, 0, QTableWidgetItem(""))
