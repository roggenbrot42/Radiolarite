from PyQt5 import QtCore, QtWidgets, uic, QtGui
from PyQt5.QtWidgets import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as Navi
import tikzplotlib
from mplcanvas import MplCanvas, DragDropEventHandler, DataReader
from skrf.network import Network as Network1
from skrf.network2 import Network

class MainWindow(QMainWindow):
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
        plt.style.use('bmh')

    def reset(self):
        self.networks = []
        self.Title = None
        self.verticalLayout.removeWidget(self.canvas)

    def Update(self):
        plt.clf()

        if not self.toolbar:
            self.toolbar = Navi(self.canvas, self.centralwidget)
        self.canvas.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.canvas.setFocus()
        self.canvas.setAcceptDrops(True)

        ax = self.canvas.axes
        for network in self.canvas.networks:
            lines = network.s.db.plot(ax=self.canvas.axes, picker=5)

        self.canvas.generate_line_to_legend()

        ax.set_xlabel('Frequency ()')
        ax.set_ylabel('Magnitude (dB)')
        self.canvas.draw()

        self.horizontalLayout.addWidget(self.toolbar)
        self.verticalLayout.addWidget(self.canvas)

    def getFile(self):
        filename = QFileDialog.getOpenFileName(filter="Touchstone Files (*.s1p *.s2p *.s3p)")[0]
        if filename:
            filenames = list()
            filenames.append(filename)
            self.readData(filenames)

    def exportFigure(self):
        if not self.canvas:
            return
        filename = QFileDialog.getSaveFileName(filter="LaTex Files (*.tex)")[0]
        if filename:
            tikzplotlib.clean_figure(self.canvas.figure) # crops invisible points and elements, not reversible maybe copy
            code = tikzplotlib.get_tikz_code(figure=self.canvas.figure, filepath=filename, standalone=True)
            f = open(filename, "w", encoding='utf8')
            f.write(code)
            f.close()

    def readData(self, strings):
        import os
        try:
            for filename in strings:
                base_name = os.path.basename(filename)
                self.Title = os.path.splitext(base_name)[0]
                print('FILE', self.Title)

                network1 = Network1(filename)  # load from file
                network = Network.from_ntwkv1(network1)  # convert to Network2 type

                self.canvas.networks.append(network)
            self.Update()
        except Exception as e:
            print(e)
            QtWidgets.QMessageBox().critical(self, "Critical Error", str(e))

    def dragEnterEvent(self, e):
        DragDropEventHandler.dragEnterEvent(e)

    def dragMoveEvent(self, e):
        DragDropEventHandler.dragMoveEvent(e)

    def dropEvent(self, e):
        strings = DragDropEventHandler.dropEvent(e)
        self.readData(strings)