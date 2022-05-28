from collections import OrderedDict

from PyQt5 import QtCore, QtWidgets, uic, QtGui
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as Navi
import tikzplotlib
from mplcanvas import MplCanvas, DragDropEventHandler, DataReader
from skrf.network import Network as Network1
from skrf.network2 import Network


class MainWindow(QMainWindow):
    plotModes = OrderedDict((
            ('decibels', 'db'),
            ('smith', 'smith'),
            ('magnitude', 'mag'),
            ('phase (deg)', 'deg'),
            ('phase unwrapped (deg)', 'deg_unwrap'),
            ('phase (rad)', 'rad'),
            ('phase unwrapped (rad)', 'rad_unwrap'),
            ('real', 're'),
            ('imaginary', 'im'),
            ('group delay', 'group_delay'),
            ('vswr', 'vswr')
        ))

    def __init__(self):
        super().__init__()
        uic.loadUi('mainwindow.ui', self)
        self.setWindowIcon(QtGui.QIcon('Q.png'))
        self.actionNew.triggered.connect(self.reset)
        self.actionOpenTouchstoneFile.triggered.connect(self.getFile)
        self.actionExportFigure.triggered.connect(self.exportFigure)
        self.filename = ''

        self.canvas = MplCanvas()
        self.Title = None
        self.filename = None
        self.toolbar = None
        if not self.toolbar:
            self.toolbar = Navi(self.canvas, self.centralwidget)
        self.canvas.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.canvas.setFocus()
        self.canvas.setAcceptDrops(True)
        self.horizontalLayout.addWidget(self.toolbar)
        self.horizontalLayout_2.addWidget(self.canvas)
        self.initPlotSelectorBox()
        self.canvas.selectionChanged.connect(self.selectionChanged)
        self.plotSelectorBox.currentIndexChanged.connect(self.Update)

        self.networkModel = QtGui.QStandardItemModel()
        self.treeView.setModel(self.networkModel)
        self.treeView.activated.connect(self.treeViewItemSelected)

        self.networkModel.setHorizontalHeaderLabels(["Name", "Plot"])
        self.networkModel.itemChanged.connect(self.itemChanged)
        self.networkModel.rowsInserted.connect(self.Update)


    def initPlotSelectorBox(self):
        keys = list(self.plotModes.keys())
        for item in keys:
            self.plotSelectorBox.addItem(item)

    def selectionChanged(self,number: int):
        pass

    def treeViewItemSelected(self, index : QModelIndex):
        print("Selected index: row {} col {}".format(index.row(),index.column()))

    def reset(self):
        self.canvas.reset()
        self.Title = None
        rowc = self.networkModel.rowCount()
        self.networkModel.invisibleRootItem().removeRows(0,rowc)
        self.Update()

    def itemChanged(self,item : QStandardItem):
        if item.parent() == None: #Contains network
            network = item.data(QtCore.Qt.UserRole+1)
            network.name = item.data(QtCore.Qt.DisplayRole)
        self.Update()

    def Update(self):
        mode = self.plotModes[self.plotSelectorBox.currentText()]
        self.canvas.plot(mode)
        self.canvas.generate_line_to_legend()
        self.canvas.draw()

    def getFile(self):
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

    def readFile(self, filename):
        import os
        baseName = os.path.basename(filename)
        self.Title = os.path.splitext(baseName)[0]
        print('FILE', self.Title)

        nw = Network.from_ntwkv1(Network1(filename))
        self.canvas.addNetwork(nw)
        root = self.networkModel.invisibleRootItem()
        nwItem = QtGui.QStandardItem()
        nwItem.setData(nw.name, QtCore.Qt.DisplayRole)
        nwItem.setData(nw)  # UserRole + 1
        self.networkModel.appendRow(nwItem)

        for it in nw.port_tuples:
            sName = "S{}{}".format(it[0] + 1, it[1] + 1)
            sItem = QtGui.QStandardItem()
            sItem.setText(sName)
            sItem.setEditable(False)
            checkItem = QtGui.QStandardItem()
            checkItem.setCheckable(True)
            checkItem.setCheckState(True)
            checkItem.setEditable(False)
            nwItem.appendRow([sItem, checkItem])

        self.treeView.expandAll()

    def readFiles(self, strings):
        try:
            for filename in strings:
                networks = self.readFile(filename)
                return networks
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
