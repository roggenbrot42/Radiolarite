from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QLabel, QLineEdit, QFormLayout, QPushButton, QSpacerItem


class SubnetworkDialog(QWidget):
    closed = pyqtSignal()
    portsChanged = pyqtSignal(list)

    def __init__(self, parent):
        super(SubnetworkDialog, self).__init__(parent=parent)
        self.setWindowTitle("Select Subnetwork")
        formlayout = QFormLayout()
        self.setLayout(formlayout)

        self.portEdit = QLineEdit("1")
        formlayout.addRow("Ports", self.portEdit)
        okbutton = QPushButton("Ok")
        formlayout.addRow("", okbutton)
        okbutton.clicked.connect(self.close)
        okbutton.clicked.connect(self.changed)

    def changed(self):
        try:
            ports = [int(x)-1 for x in self.portEdit.text().split(',')]
        except ValueError:
            ports = 1
        self.portsChanged.emit(ports)

    def getValues(self):
        try:
            return int(self.portEdit.text())
        except ValueError:
            return 1