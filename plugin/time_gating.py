import skrf
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QWidget, QLabel, QLineEdit, QVBoxLayout, QPushButton, QMessageBox, QGroupBox, \
    QFormLayout, QComboBox
from PyQt5.QtGui import QRegularExpressionValidator

import validatinglineedit as validedit
from validatinglineedit import ValidatingLineEdit

class TimeGatingDialog(QWidget):
    closed = pyqtSignal()
    resultChanged = pyqtSignal(object)



    def __init__(self, parent):
        super(TimeGatingDialog, self).__init__(parent=parent)
        self.setWindowTitle("Time Domain Gating Settings")
        formlayout = QFormLayout()
        self.setLayout(formlayout)

        self.windowselect = QComboBox(self)
        self.windowselect.addItems(['Kaiser', 'Hamming', 'Boxcar', 'Hann', 'BlackmanHarris'])
        formlayout.addRow("Window", self.windowselect)
        self.centerTimeEdit = validedit.ValidatingTimeEdit("0")
        formlayout.addRow("Center", self.centerTimeEdit)
        self.spanTimeEdit = validedit.ValidatingTimeEdit("1")
        formlayout.addRow("Span", self.spanTimeEdit)

        okButton = QPushButton("Ok")
        formlayout.addRow("", okButton)
        okButton.clicked.connect(self.changed)

    def changed(self):
        try:
            center = self.centerTimeEdit.getValue()
            span = self.spanTimeEdit.getValue()
            window = self.windowselect.currentText()
            self.resultChanged.emit({'center': center, 'span': span, 'window': window})
            self.close()
        except ValueError:
            QMessageBox.critical(self, "Error", "No valid values given.")


def plugin_main():
    print("TDR module loaded")
