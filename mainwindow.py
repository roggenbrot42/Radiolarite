from PyQt5 import QtCore, QtWidgets, uic, QtGui
from PyQt5.QtWidgets import *
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
        if not self.toolbar:
            self.toolbar = Navi(self.canvas, self.centralwidget)
        self.canvas.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.canvas.setFocus()
        self.canvas.setAcceptDrops(True)
        self.horizontalLayout.addWidget(self.toolbar)
        self.verticalLayout.addWidget(self.canvas)

    def reset(self):
        self.canvas.reset()
        self.Title = None
        self.Update()

    def Update(self):
        self.canvas.plot()
        self.canvas.generate_line_to_legend()
        self.canvas.draw()

    def getFile(self):
        filename = QFileDialog.getOpenFileName(filter="Touchstone Files (*.s1p *.s2p *.s3p)")[0]
        if filename:
            filenames = list()
            filenames.append(filename)
            self.readFile(filename)
            self.Update()

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

    def readFile(self, filename):
        import os
        base_name = os.path.basename(filename)
        self.Title = os.path.splitext(base_name)[0]
        print('FILE', self.Title)

        nw = Network.from_ntwkv1(Network1(filename))
        self.canvas.addNetwork(nw)
        self.Update()

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