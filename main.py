import sys

from PyQt5 import QtCore
from PyQt5.QtWidgets import *
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backend_bases import MouseButton
from matplotlib.lines import Line2D
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as Navi
from matplotlib.figure import Figure
from skrf import Network

matplotlib.use('Qt5Agg')


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
            e.setDropAction(QtCore.Qt.CopyAction)
            e.accept()
            for url in e.mimeData().urls():
                strings.append(str(url.toLocalFile()))
            print("GOT ADDRESSES:", strings)
        else:
            e.ignore()  # just like above functions

        return strings


class MplCanvas(FigureCanvasQTAgg):
    linemap: dict[Line2D, Line2D]

    def __init__(self, parent=None, width=8, height=4.5, dpi=120):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        fig.canvas.mpl_connect('pick_event', self.on_pick)
        fig.canvas.mpl_connect('button_press_event', self.button_press_event)
        fig.canvas.mpl_connect('button_release_event', self.button_release_event)
        fig.canvas.mpl_connect('key_press_event', self.delete_event)
        self.default_linewidth = 2.0
        self.picked = None  # type: Line2D #always the line, never legend
        self.pickstate = 0
        self.linemap = {}
        super(MplCanvas, self).__init__(fig)

    def on_pick(self, event: matplotlib.backend_bases.Event):
        if event.mouseevent.button != MouseButton.LEFT:
            return
        if isinstance(event.artist, Line2D):
            if event.artist is not self.picked:
                event.artist.set_linewidth(2 * self.default_linewidth)
                self.linemap[event.artist].set_linewidth(2 * self.default_linewidth)

                if self.picked is not None:
                    self.picked.set_linewidth(self.default_linewidth)
                    self.linemap[self.picked].set_linewidth(self.default_linewidth)

                if event.artist in self.linemap:  # is an axis entry
                    self.picked = event.artist
                else:
                    self.picked = self.linemap[event.artist]
                self.pickstate = 1

        self.draw_idle()

    def button_release_event(self, event: matplotlib.backend_bases.Event):
        if event.button == MouseButton.LEFT:
            if self.picked is None:
                for line in self.linemap:
                    self.linemap[line].set_linewidth(self.default_linewidth)
                    line.set_linewidth(self.default_linewidth)
                self.pickstate = 0
                self.draw_idle()
            elif self.pickstate == 2:
                self.picked.set_linewidth(self.default_linewidth)
                self.linemap[self.picked].set_linewidth(self.default_linewidth)
                self.picked = None
                self.draw_idle()
            self.pickstate = 2

    def button_press_event(self, event):
        pass

    def delete_event(self, event):
        if event.key == 'delete' and self.picked is not None:
            try:
                self.picked.remove()
                value = self.linemap.pop(self.picked)
                self.linemap.pop(value)
                self.axes.legend()
            except ValueError:
                print(self.picked)
            self.picked = None
            self.draw_idle()
            self.pickstate = 0

    def dragEnterEvent(self, e):
        DragDropEventHandler.dragEnterEvent(e)

    def dragMoveEvent(self, e):
        DragDropEventHandler.dragMoveEvent(e)

    def dropEvent(self, e):
        strings = DragDropEventHandler.dropEvent(e)
        for filename in strings:
            DataReader.readData(filename, "", self)
        self.draw()


class DataReader:
    @staticmethod
    def readData(filename: str, title: str, canvas: MplCanvas) -> Network:
        if canvas is None:
            canvas = MplCanvas()
        network = Network(filename)
        ax = canvas.axes
        lines = network.plot_s_db(ax=canvas.axes, picker=5)

        network.frequency.unit = 'ghz'

        legend = ax.legend()
        legend.set_draggable(True)

        canvas.linemap = {}

        for legline, origline in zip(legend.get_lines(), ax.lines):
            legline.set_picker(5)  # Enable picking on the legend line.
            canvas.linemap[legline] = origline
            canvas.linemap[origline] = legline

        ax.set_xlabel('Frequency (Hz)')
        ax.set_ylabel('Magnitude (dB)')
        ax.set_title(title)

        return network, canvas


class MainWindowUI(object):
    def __init__(self):
        self.Title = None
        self.filename = None
        self.network = None
        self.toolbar = None
        self.actionExit = None
        self.statusbar = None
        self.menuFile = None
        self.menubar = None
        self.verticalLayout = None
        self.horizontalLayout = None
        self.gridLayout = None
        self.central_widget = None
        self.actionOpen_touchstone_file = None
        self.canvas = None

    def setupUi(self, mainwindow):
        mainwindow.setObjectName("MainWindow")
        window_width = 1440
        window_height = 1024
        screen = QApplication.desktop().screenGeometry()
        self.setGeometry(int((screen.width() - window_width) / 2), int((screen.height() - window_height) / 2),
                         window_width,
                         window_height)
        self.central_widget = QWidget(mainwindow)
        self.central_widget.setObjectName("centralwidget")
        self.gridLayout = QGridLayout(self.central_widget)
        self.gridLayout.setObjectName("gridLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.horizontalLayout.addStretch(1)
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)
        self.gridLayout.addLayout(self.horizontalLayout, 1, 0, 1, 1)

        mainwindow.setCentralWidget(self.central_widget)
        self.menubar = QMenuBar(mainwindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 22))
        self.menubar.setObjectName("menubar")
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        mainwindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(mainwindow)
        self.statusbar.setObjectName("statusbar")
        mainwindow.setStatusBar(self.statusbar)
        self.actionOpen_touchstone_file = QAction(mainwindow)
        self.actionOpen_touchstone_file.setObjectName("actionOpen_touchstone_file")
        self.actionExit = QAction(mainwindow)
        self.actionExit.setObjectName("actionExit")
        self.menuFile.addAction(self.actionOpen_touchstone_file)
        self.menuFile.addAction(self.actionExit)
        self.menubar.addAction(self.menuFile.menuAction())

        self.retranslateUi(mainwindow)
        QtCore.QMetaObject.connectSlotsByName(mainwindow)

        self.filename = ''

        self.canvas = None
        plt.style.use('bmh')

        self.actionExit.triggered.connect(mainwindow.close)
        self.actionOpen_touchstone_file.triggered.connect(self.getFile)

    def Update(self):
        plt.clf()

        self.toolbar = Navi(self.canvas, self.central_widget)
        self.canvas.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.canvas.setFocus()
        self.canvas.setAcceptDrops(True)
        self.canvas.draw()

        self.horizontalLayout.addWidget(self.toolbar)
        self.verticalLayout.addWidget(self.canvas)

    def getFile(self):
        self.filename = QFileDialog.getOpenFileName(filter="Touchstone Files (*.s1p *.s2p *.s3p)")[0]
        self.readData()

    def readData(self, strings):
        import os
        for filename in strings:
            base_name = os.path.basename(filename)
            self.Title = os.path.splitext(base_name)[0]
            print('FILE', self.Title)
            network, canvas = DataReader.readData(filename, self.Title, None)
            canvas.setParent(self)
            self.canvas = canvas
        self.Update()

    def retranslateUi(self, mainwindow):
        _translate = QtCore.QCoreApplication.translate
        mainwindow.setWindowTitle(_translate("MainWindow", "Touchstone Plot"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.actionOpen_touchstone_file.setText(_translate("MainWindow", "Open Touchstone file"))
        self.actionExit.setText(_translate("MainWindow", "Exit"))


class MainWindow(QMainWindow, MainWindowUI):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, e):
        DragDropEventHandler.dragEnterEvent(e)

    def dragMoveEvent(self, e):
        DragDropEventHandler.dragMoveEvent(e)

    def dropEvent(self, e):
        strings = DragDropEventHandler.dropEvent(e)
        self.readData(strings)


def window():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    window()
