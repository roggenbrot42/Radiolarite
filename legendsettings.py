from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QLabel, QLineEdit, QFormLayout, QPushButton, QSpacerItem


class LegendSettingsDialog(QWidget):
    closed = pyqtSignal()
    columnsChanged = pyqtSignal(int)

    def __init__(self, parent):
        super(LegendSettingsDialog, self).__init__(parent=parent)
        self.setWindowTitle("Legend Settings")
        formlayout = QFormLayout()
        self.setLayout(formlayout)

        self.columnedit = QLineEdit("1")
        formlayout.addRow("Columns", self.columnedit)
        okbutton = QPushButton("Ok")
        formlayout.addRow("", okbutton)
        okbutton.clicked.connect(self.close)
        okbutton.clicked.connect(self.changed)

    def changed(self):
        try:
            columns = int(self.columnedit.text())
        except ValueError:
            columns = 1
        self.columnsChanged.emit(columns)

    def getValues(self):
        try:
            return int(self.columnedit.text())
        except ValueError:
            return 1