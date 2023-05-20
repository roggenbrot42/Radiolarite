from fileinput import filename

import skrf.network2
import tikzplotlib
from PyQt5 import QtCore, QtWidgets, uic, QtGui
from PyQt5.QtCore import *
from PyQt5.QtGui import QRegularExpressionValidator
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as Navi
from skrf.network import Network as Network1
from skrf.network2 import Network
import pandas as pd

import csv

import legendsettings
import validatinglineedit
from networkview import NetworkView
from mplcanvas import MplCanvas, plotModes
from networkitem import NetworkItem, ParamItem
from validatinglineedit import ValidatingLineEdit, TimeValue, FrequencyValue
from plugin.time_gating import TimeGatingDialog


def network2to1(network2: skrf.network2.Network) -> skrf.Network:
    return skrf.Network(s=network2.s.val, f=network2.frequency.f)


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
        self.tdr_dialog = None
        self.legend_dialog = None
        self.networkView = None
        self.canvas: MplCanvas = None
        self.title = None
        self.toolbar = None
        self.networkModel = None
        self.selectionModel: QItemSelectionModel = None
        self.setupUI()
        self.setupModels()
        self.setupViews()
        self.setupMenus()

    def setupUI(self):
        uic.loadUi('mainwindow.ui', self)
        self.setWindowIcon(QtGui.QIcon('Q.png'))
        self.networkView = NetworkView()
        self.networkView.setSizePolicy(QSizePolicy(QSizePolicy.Preferred,QSizePolicy.Preferred))
        self.canvas = MplCanvas(parent=self,
                                gridMajor=self.actionGridMajor.isChecked(),
                                gridMinor=self.actionGridMinor.isChecked())
        self.canvas.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding,QSizePolicy.Preferred))
        self.toolbar = Navi(self.canvas, self.centralwidget)
        self.canvas.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.canvas.setFocus()
        self.horizontalLayout.addWidget(self.toolbar)
        self.horizontalLayout_2.addWidget(self.networkView)
        self.horizontalLayout_2.addWidget(self.canvas)
        self.setupPlotSelectorBox()
        self.setupRangeEdits()
        self.legend_dialog = legendsettings.LegendSettingsDialog(None)
        self.tdr_dialog = TimeGatingDialog(parent=None)

    def setupModels(self):
        self.networkModel = QtGui.QStandardItemModel()
        self.networkModel.setHorizontalHeaderLabels(["Name"])
        self.selectionModel = QItemSelectionModel(self.networkModel)

    def setupViews(self):
        self.canvas.setModel(self.networkModel)
        self.canvas.setSelectionModel(self.selectionModel)
        self.networkView.setModel(self.networkModel)
        self.networkView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.networkView.setSelectionMode(QAbstractItemView.SingleSelection)
        self.networkView.setSelectionModel(self.selectionModel)
        #self.networkView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.networkView.setAnimated(True)

    def setupMenus(self):
        self.actionNew.triggered.connect(self.reset)
        self.actionOpenTouchstoneFile.triggered.connect(self.openFileDialog)
        self.actionExportFigure.triggered.connect(self.exportFigure)
        self.actionExportCSV.triggered.connect(self.exportCSV)
        self.plotSelectorBox.currentIndexChanged.connect(self.canvas.changePlotMode)
        self.plotSelectorBox.currentIndexChanged.connect(self.changePlotMode)
        self.actionGridMajor.toggled.connect(self.canvas.toggleMajorGrid)
        self.actionGridMinor.toggled.connect(self.canvas.toggleMinorGrid)
        self.actionCopy_to_clipboard.triggered.connect(self.copyToClipboard)
        self.actionTime_Domain_Gating.triggered.connect(self.triggerTDGating)
        self.actionLegend.triggered.connect(self.legend_dialog.show)
        self.legend_dialog.columnsChanged.connect(self.canvas.legendChange)
        self.tdr_dialog.resultChanged.connect(self.tdrGateNetwork)

    def setupPlotSelectorBox(self):
        keys = list(plotModes.keys())
        for item in keys:
            self.plotSelectorBox.addItem(item)

    def setupRangeEdits(self):
        freq_validator = validatinglineedit.setupFrequencyRangeValidator()
        start_edit = ValidatingLineEdit(validate=freq_validator)
        stop_edit = ValidatingLineEdit(validate=freq_validator)
        self.horizontalLayout.replaceWidget(self.startFrequencyEdit,
                                            start_edit)
        self.horizontalLayout.replaceWidget(self.stopFrequencyEdit,
                                            stop_edit)
        self.startFrequencyEdit.setVisible(False)
        self.stopFrequencyEdit.setVisible(False)
        self.startFrequencyEdit = start_edit
        self.stopFrequencyEdit = stop_edit
        self.startFrequencyEdit.editingFinished.connect(self.rangeChanged)
        self.stopFrequencyEdit.editingFinished.connect(self.rangeChanged)

    def reset(self):
        self.title = None
        row_count = self.networkModel.rowCount()
        self.networkModel.invisibleRootItem().removeRows(0, row_count)
        self.canvas.reset()

    def getPlotModeType(self):
        index = self.plotSelectorBox.currentIndex()
        plot_mode = list(plotModes.values())[index]
        if plot_mode == 's_time' or plot_mode == 'z_time':
            return 'time'
        else:
            return 'frequency'

    def changePlotMode(self, index):
        oldstart = self.startFrequencyEdit.text()
        oldstop = self.stopFrequencyEdit.text()
        if self.getPlotModeType() == 'time':
            validator = validatinglineedit.setupTimeRangeValidator()
            self.startFrequencyEdit.setValidator(validator)
            self.stopFrequencyEdit.setValidator(validator)
        else:
            validator = validatinglineedit.setupFrequencyRangeValidator()
            self.startFrequencyEdit.setValidator(validator)
            self.stopFrequencyEdit.setValidator(validator)

        pos = 0
        if validator.validate(oldstart,pos) == QValidator.Acceptable and validator.validate(oldstop,pos) == QValidator.Acceptable:
            self.startFrequencyEdit.setText(oldstart)
            self.stopFrequencyEdit.setText(oldstop)
        else:
            self.startFrequencyEdit.setText('')
            self.stopFrequencyEdit.setText('')

    def rangeChanged(self):
        range_strs = list()
        range_strs.append(self.startFrequencyEdit.text())
        range_strs.append(self.stopFrequencyEdit.text())

        ranges = list()
        unitl = list()

        if self.getPlotModeType() == 'frequency':
            units = {'Hz': 1e-9, 'kHz': 1e-6, 'MHz': 1e-3, 'GHz': 1, 'THz': 1e3}

            for string in range_strs:
                if string == '':
                    self.canvas.setXlimits('', '')
                    return
                unit = 'GHz'  # default unit
                tok = string.split(" ")
                if len(tok) > 1:
                    if tok[1]:
                        unit = tok[1]
                ranges.append(tok[0])
                unitl.append(units[unit])
        else:
            units = {'fs': 1e-6, 'ps': 1e-3, 'ns': 1, 'µs': 1e3, 'mus': 1e3, 'ms': 1e6, 's': 1e9}

            for string in range_strs:
                if string == '':
                    self.canvas.setXlimits('', '')
                    return
                unit = 'ns'  # default unit
                tok = string.split(" ")
                if len(tok) > 1:
                    if tok[1]:
                        unit = tok[1]
                ranges.append(tok[0])
                unitl.append(units[unit])

        if float(ranges[0]) * unitl[0] > float(ranges[1]) * unitl[1]:
            tmp = ranges[1]
            ranges[1] = ranges[0]
            ranges[0] = tmp
            tmp = unitl[1]
            unitl[1] = unitl[0]
            unitl[0] = tmp
            self.startFrequencyEdit.setText(ranges[0])
            self.stopFrequencyEdit.setText(ranges[1])

        if self.getPlotModeType() == 'frequency':
            self.canvas.setXlimits(ranges[0], ranges[1] + unit.lower())
        else:
            self.canvas.setXlimits(float(ranges[0]) * unitl[0], float(ranges[1]) * unitl[1])

    def openFileDialog(self):
        filename = QFileDialog.getOpenFileName(filter="Touchstone Files (*.s1p *.s2p *.s3p *.s4p)")[0]
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

    def exportCSV(self):
        if not self.canvas:
            return
        currentNetwork = self.getCurrentNetwork()
        if currentNetwork:
            filenames = QFileDialog.getSaveFileName(caption="Save to CSV", directory=currentNetwork.name,
                                                    filter="CSV files (*.csv)")
            if not filenames or len(filenames) < 2 or filenames[0] == '':
                return
            nw1 = skrf.Network(name=currentNetwork.name, s=currentNetwork.s.val, f=currentNetwork.frequency.f_scaled,
                               f_unit=currentNetwork.frequency.unit)
            index = self.plotSelectorBox.currentIndex()
            plot_mode = list(plotModes.values())[index]
            attr = "s_{}".format(plot_mode)
            try:
                dataframe = nw1.to_dataframe(attrs=[attr])
            except AttributeError as e:
                QMessageBox().critical(self, "Error", "Attribute Error {}.".format(e))
                return
            dataframe.index.name = 'Frequency ({})'.format(currentNetwork.frequency.unit)
            try:
                dataframe.to_csv(filenames[0], sep=' ')  # quoting=csv.QUOTE_NONE, escapechar="\\")
            except ValueError as e:
                print(e)
        else:
            QMessageBox().critical(self, "Error", "No Network selected")

    def copyToClipboard(self):
        pixmap = self.canvas.grab()
        qApp.clipboard().setPixmap(pixmap)

    def getCurrentNetworkItem(self) -> NetworkItem:
        index_list = self.selectionModel.selectedIndexes()
        network = None
        network_item = None
        if len(index_list) > 0:
            index = index_list[0]
            item = self.networkModel.itemFromIndex(index)

            if isinstance(item, ParamItem):
                network_item = item.parent()
                network = network_item.network()
            elif isinstance(item, NetworkItem):
                network_item = item
                network = network_item.network()
        return network_item

    def getCurrentNetwork(self) -> Network:
        nwIt = self.getCurrentNetworkItem()
        if nwIt:
            return nwIt.network()
        else:
            return None

    def triggerTDGating(self):
        network_item = self.getCurrentNetworkItem()
        if network_item is None:
            QMessageBox().critical(self, "Error", "No Network selected")
            return
        # self.tdr_dialog.resize(480, 320)
        self.tdr_dialog.show()

    def tdrGateNetwork(self, tmp: dict):
        t_center = tmp['center']
        t_span = tmp['span']
        window = tmp['window'].lower()
        nw = self.getCurrentNetworkItem().network()
        nwl = list()
        for pt in nw.port_tuples:
            network = skrf.Network(s=nw.s[:, pt[0], pt[1]], f=nw.frequency.f_scaled)
            try:
                gated_network = network.s11.time_gate(center=t_center.num, span=t_span.num, window=window)
            except ValueError:
                QMessageBox().critical(self, "Window not supported", "Window not yet supported, pick another one.")
                return

            gated_network.name = nw.name + ' (gated)'
            nwl.append(gated_network)
        combined_network = skrf.network.n_oneports_2_nport(nwl, name=nw.name + ' (gated)')
        nw2 = Network.from_ntwkv1(combined_network)
        nw2.frequency.unit = 'GHz'
        nwItem = NetworkItem(nw2)
        self.networkModel.invisibleRootItem().appendRow(nwItem)

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
        self.networkView.expandAll()

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
