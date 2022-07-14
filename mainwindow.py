import tikzplotlib
from PyQt5 import QtCore, QtWidgets, uic, QtGui
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as Navi
from skrf.network import Network as Network1
from skrf.network2 import Network

from mplcanvas import MplCanvas, plotModes
from networkitem import NetworkItem, ParamItem
from validatinglineedit import ValidatingLineEdit


class DragDropEventHandler:
    @staticmethod
    def dragEnterEvent(e):
        if e.mimeData().hasUrls:
            e.accept()
        else:
            e.ignore()

    @staticmethod
    def dragMoveEvent(e):
        if e.mimeData().hasUrls:
            e.accept()
        else:
            e.ignore()

    @staticmethod
    def dropEvent(e):
        strings = list()
        if e.mimeData().hasUrls:
            e.setDropAction(Qt.CopyAction)
            e.accept()
            for url in e.mimeData().urls():
                strings.append(str(url.toLocalFile()))
            print("GOT ADDRESSES:", strings)
        else:
            e.ignore()  # just like above functions
        return strings


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.canvas: MplCanvas = None
        self.title = None
        self.toolbar = None
        self.networkModel = None
        self.selectionModel: QItemSelectionModel = None

        self.setupUI()
        self.setupModels()
        self.setupViews()

        self.actionNew.triggered.connect(self.reset)
        self.actionOpenTouchstoneFile.triggered.connect(self.openFileDialog)
        self.actionExportFigure.triggered.connect(self.exportFigure)
        self.plotSelectorBox.currentIndexChanged.connect(self.canvas.changePlotMode)
        self.actionGridMajor.toggled.connect(self.canvas.toggleMajorGrid)
        self.actionGridMinor.toggled.connect(self.canvas.toggleMinorGrid)
        self.actionCopy_to_clipboard.triggered.connect(self.copyToClipboard)

    def setupUI(self):
        uic.loadUi('mainwindow.ui', self)
        self.setWindowIcon(QtGui.QIcon('Q.png'))
        self.canvas = MplCanvas(parent=self,
                                gridMajor=self.actionGridMajor.isChecked(),
                                gridMinor=self.actionGridMinor.isChecked())
        self.toolbar = Navi(self.canvas, self.centralwidget)
        self.canvas.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.canvas.setFocus()
        self.horizontalLayout.addWidget(self.toolbar)
        self.horizontalLayout_2.addWidget(self.canvas)
        self.setupPlotSelectorBox()
        self.setupFrequencyEdits()

    def setupModels(self):
        self.networkModel = QtGui.QStandardItemModel()
        self.networkModel.setHorizontalHeaderLabels(["Name"])
        self.selectionModel = QItemSelectionModel(self.networkModel)

    def setupViews(self):
        self.canvas.setModel(self.networkModel)
        self.canvas.setSelectionModel(self.selectionModel)
        self.treeView.setModel(self.networkModel)
        self.treeView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.treeView.setSelectionMode(QAbstractItemView.SingleSelection)
        self.treeView.setSelectionModel(self.selectionModel)
        self.treeView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.treeView.setAnimated(True)

    def setupPlotSelectorBox(self):
        keys = list(plotModes.keys())
        for item in keys:
            self.plotSelectorBox.addItem(item)

    def setupFrequencyEdits(self):
        regex = QRegularExpression("[0-9]+\.?[0-9]*( [kMGT]?Hz)?")
        validator = QRegularExpressionValidator(regex)
        startEdit = ValidatingLineEdit(validate=validator)
        stopEdit = ValidatingLineEdit(validate=validator)
        self.horizontalLayout.replaceWidget(self.startFrequencyEdit,
                                            startEdit)
        self.horizontalLayout.replaceWidget(self.stopFrequencyEdit,
                                            stopEdit)
        self.startFrequencyEdit.setVisible(False)
        self.stopFrequencyEdit.setVisible(False)
        self.startFrequencyEdit = startEdit
        self.stopFrequencyEdit = stopEdit
        self.startFrequencyEdit.editingFinished.connect(self.frequencyRangeChanged)
        self.stopFrequencyEdit.editingFinished.connect(self.frequencyRangeChanged)

    def reset(self):
        self.title = None
        rowc = self.networkModel.rowCount()
        self.networkModel.invisibleRootItem().removeRows(0, rowc)
        self.canvas.reset()

    def frequencyRangeChanged(self):
        freq_str = list()
        freq_str.append(self.startFrequencyEdit.text())
        freq_str.append(self.stopFrequencyEdit.text())

        units = {'Hz': 1e-9, 'kHz': 1e-6, 'MHz': 1e-3, 'GHz': 1, 'THz': 1e3}

        frequencies = list()
        unitl = list()

        for string in freq_str:
            if string == '':
                self.canvas.setXlimits('','')
                return
            unit = 'GHz'  # default unit
            tok = string.split(" ")
            if len(tok) > 1:
                if tok[1]:
                    unit = tok[1]
            frequencies.append(tok[0])
            unitl.append(units[unit])

        if float(frequencies[0])*unitl[0] > float(frequencies[1])*unitl[1]:
            tmp = frequencies[1]
            frequencies[1] = frequencies[0]
            frequencies[0] = tmp
            tmp = unitl[1]
            unitl[1] = unitl[0]
            unitl[0] = tmp
            self.startFrequencyEdit.setText(frequencies[0])
            self.stopFrequencyEdit.setText(frequencies[1])

        self.canvas.setXlimits(frequencies[0], frequencies[1]+unit.lower())

    def openFileDialog(self):
        filename = QFileDialog.getOpenFileName(filter="Touchstone Files (*.s1p *.s2p *.s3p)")[0]
        if filename:
            filenames = list()
            filenames.append(filename)
            self.readFile(filename)

    def exportFigure(self):
        if not self.canvas:
            return
        filename = QFileDialog.getSaveFileName(filter="LaTex Files (*.tex)")[0]
        if filename:
            tikzplotlib.clean_figure(
                self.canvas.figure)  # crops invisible points and elements, not reversible maybe copy
            code = tikzplotlib.get_tikz_code(figure=self.canvas.figure, filepath=filename, standalone=True)
            f = open(filename, "w", encoding='utf8')
            f.write(code)
            f.close()

    def copyToClipboard(self):
        pixmap = self.canvas.grab()
        qApp.clipboard().setPixmap(pixmap)

    def readFile(self, filename):
        import os
        baseName = os.path.basename(filename)
        self.title = os.path.splitext(baseName)[0]
        print('FILE', self.title)

        nw = Network.from_ntwkv1(Network1(filename))
        nw.frequency.unit = 'ghz'  # fix for https://github.com/scikit-rf/scikit-rf/issues/293
        root = self.networkModel.invisibleRootItem()
        nwItem = NetworkItem(nw)
        root.appendRow(nwItem)
        self.treeView.expandAll()

    def readFiles(self, strings):
        try:
            for filename in strings:
                self.readFile(filename)
        except Exception as e:
            print(e)
            QtWidgets.QMessageBox().critical(self, "Critical Error", str(e))

    def dragEnterEvent(self, e):
        DragDropEventHandler.dragEnterEvent(e)

    def dragMoveEvent(self, e):
        DragDropEventHandler.dragMoveEvent(e)

    def dropEvent(self, e):
        strings = DragDropEventHandler.dropEvent(e)
        self.readFiles(strings)
