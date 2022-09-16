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

import legendsettings
import validatinglineedit
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
        self.plotSelectorBox.currentIndexChanged.connect(self.changePlotMode)
        self.actionGridMajor.toggled.connect(self.canvas.toggleMajorGrid)
        self.actionGridMinor.toggled.connect(self.canvas.toggleMinorGrid)
        self.actionCopy_to_clipboard.triggered.connect(self.copyToClipboard)
        self.actionZeroReflection.triggered.connect(self.zeroReflection)
        self.actionTime_Domain_Gating.triggered.connect(self.triggerTDGating)
        self.actionLegend.triggered.connect(self.legend_dialog.show)
        self.legend_dialog.columnsChanged.connect(self.canvas.legendChange)
        self.tdr_dialog.resultChanged.connect(self.tdrGateNetwork)

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
        self.startFrequencyEdit.setText("")
        self.stopFrequencyEdit.setText("")
        if self.getPlotModeType() == 'time':
            validator = validatinglineedit.setupTimeRangeValidator()
            self.startFrequencyEdit.setValidator(validator)
            self.stopFrequencyEdit.setValidator(validator)
        else:
            validator = validatinglineedit.setupFrequencyRangeValidator()
            self.startFrequencyEdit.setValidator(validator)
            self.stopFrequencyEdit.setValidator(validator)

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
            units = {'fs': 1e-15, 'ps': 1e-12, 'ns': 1e-9, 'ms': 1e-6, 's': 1}

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
        return self.getCurrentNetworkItem().network()

    def zeroReflection(self):
        network_item = self.getCurrentNetworkItem()

        if network_item:
            network = network_item.network()
            (l, m, n) = network_item.n.s.val.shape
            if m > 1:
                s11 = network.s.val[:, 0, 0]
                network.s.val[:, 1, 0] = network.s.val[:, 1, 0] + s11
                s11.fill(1e-20)
                network_item.params()[0].setCheckState(Qt.Unchecked)
                self.canvas.redrawAll()

    def triggerTDGating(self):
        network_item = self.getCurrentNetworkItem()
        if network_item is None:
            QMessageBox().critical(self, "Error", "No Network selected")
            return
        #self.tdr_dialog.resize(480, 320)
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
        combined_network = skrf.network.n_oneports_2_nport(nwl, name=nw.name+' (gated)')
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
