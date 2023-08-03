from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtWidgets import QWidget, QPushButton, QMessageBox, QFormLayout, QVBoxLayout, QListView, QHBoxLayout, \
    QTreeView, QAbstractItemView, QLabel


class DeembeddingDialog(QWidget):
    closed = pyqtSignal()
    resultChanged = pyqtSignal(list)

    def __init__(self, parent, networkModel: QStandardItemModel):
        super(DeembeddingDialog, self).__init__(parent=parent)
        self.setWindowTitle("Deembedding")
        self.networkModel = networkModel
        outer_layout = QVBoxLayout(self)
        self.setLayout(outer_layout)

        viewbox = QHBoxLayout()

        self.fromList = QListView()
        self.fromList.setModel(self.networkModel)
        self.fromList.setSelectionMode(QAbstractItemView.SingleSelection)
        self.thruList = QListView()
        self.thruList.setModel(self.networkModel)
        self.thruList.setSelectionMode(QAbstractItemView.SingleSelection)
        viewbox.addWidget(QLabel("FDF"))
        viewbox.addWidget(self.fromList)
        viewbox.addStretch(10)
        viewbox.addWidget(QLabel("FF"))
        viewbox.addWidget(self.thruList)
        outer_layout.addLayout(viewbox)

        okButton = QPushButton("Ok")
        outer_layout.addWidget(okButton)
        okButton.clicked.connect(self.changed)

    def changed(self):
        try:
            fromselect = self.fromList.selectedIndexes()
            thruselect = self.thruList.selectedIndexes()
            fromItem = self.networkModel.itemFromIndex(fromselect[0]).network()
            thruItem = self.networkModel.itemFromIndex(thruselect[0]).network()
            self.resultChanged.emit([fromItem,thruItem])
            self.close()
        except ValueError:
            QMessageBox.critical(self, "Error", "No valid values given.")

def plugin_main():
    print("Deembedding module loaded")
