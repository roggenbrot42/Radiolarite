from PyQt5 import QtCore
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import matplotlib
from matplotlib.backend_bases import MouseButton
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as Navi
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from skrf.network import Network as SkNetwork1
from skrf.network2 import Network as SkNetwork
import seaborn as sns

class NetworkItem:
    def __init__(self,network: SkNetwork, attributes = None):
        self.nw = network
        self.attr = attributes

class MplCanvas(FigureCanvasQTAgg):
    line2leg: dict[Line2D, Line2D]

    def __init__(self, parent=None, width=8, height=4.5, dpi=120):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        fig.canvas.mpl_connect('pick_event', self.on_pick)
        fig.canvas.mpl_connect('button_press_event', self.button_press_event)
        fig.canvas.mpl_connect('button_release_event', self.button_release_event)
        fig.canvas.mpl_connect('key_press_event', self.key_event)
        self.networks = []
        self.default_linewidth = 2.0
        self.picked = None  # type: Line2D #always the line, never legend
        self.pickstate = 0
        self.line2leg = {}
        super(MplCanvas, self).__init__(fig)

    selectionChanged = pyqtSignal(int)

    def generate_line_to_legend(self):
        ax = self.axes
        legend = ax.legend()
        legend.set_draggable(True)
        self.line2leg = {}
        for legline, origline in zip(legend.get_lines(), ax.lines):
            legline.set_picker(5)  # Enable picking on the legend line.
            self.line2leg[legline] = origline
            self.line2leg[origline] = legline

    def on_pick(self, event: matplotlib.backend_bases.Event):
        if isinstance(event.artist, Line2D):
            if event.artist is not self.picked:
                event.artist.set_linewidth(2 * self.default_linewidth)
                self.line2leg[event.artist].set_linewidth(2 * self.default_linewidth)

                if self.picked is not None:
                    self.picked.set_linewidth(self.default_linewidth)
                    self.line2leg[self.picked].set_linewidth(self.default_linewidth)

                if event.artist in self.line2leg:  # is an axis entry
                    self.picked = event.artist
                else:
                    self.picked = self.line2leg[event.artist]
                self.pickstate = 1

                self.selectionChanged.emit(self.pickstate)

        self.draw_idle()

    def button_release_event(self, event: matplotlib.backend_bases.Event):
        if event.button == MouseButton.LEFT:
            if self.picked is None:
                for line in self.line2leg:
                    self.line2leg[line].set_linewidth(self.default_linewidth)
                    line.set_linewidth(self.default_linewidth)
                self.pickstate = 0
                self.draw_idle()
            elif self.pickstate == 2:
                self.picked.set_linewidth(self.default_linewidth)
                self.line2leg[self.picked].set_linewidth(self.default_linewidth)
                self.picked = None
                self.draw_idle()
            self.pickstate = 2

            self.selectionChanged.emit(self.pickstate)

    def button_press_event(self, event):
        pass

    def key_event(self, event):
        if event.key == 'delete' and self.picked is not None:
            try:
                self.picked.remove()
                value = self.line2leg.pop(self.picked)
                self.line2leg.pop(value)
                self.axes.legend()
            except ValueError:
                print("picked error: {}".format(self.picked))
            self.picked = None
            self.draw_idle()
            self.pickstate = 0
            self.generate_line_to_legend()
        elif event.key == 'f2' and self.picked is not None:
            h, l = self.axes.get_legend_handles_labels()
            index = self.figure.axes[0].lines.index(self.picked)
            (text,result) = QInputDialog.getText(self,'Enter new Label','Label',text=l[index])
            if text:
                l[index] = text
                self.axes.legend(h, l)
                self.draw_idle()

    def dragEnterEvent(self, e):
        DragDropEventHandler.dragEnterEvent(e)

    def dragMoveEvent(self, e):
        DragDropEventHandler.dragMoveEvent(e)

    def dropEvent(self, e):
        strings = DragDropEventHandler.dropEvent(e)
        for filename in strings:
            DataReader.readData(filename, "", self)
        self.draw()

    def reset(self):
        self.networks = []
        self.figure.axes[0].clear()

    def addNetwork(self, network: SkNetwork):
        if not network:
            return
        if(isinstance(network, SkNetwork)):
            network.frequency.unit = 'ghz'  # fix for https://github.com/scikit-rf/scikit-rf/issues/293
            self.networks.append(network)
        else:
            raise Exception("Wrong class type {}, expected Network".format(type(network)))

    def plot(self,mode = 'db'):
        ax = self.axes
        self.figure.axes[0].clear()

        for nw in self.networks:
            if mode == 'db':
                lines = nw.s.db.plot(ax=ax, picker=5)
                print("Plotted line: {}".format(lines))
            elif mode == 'mag':
                lines = nw.s.mag.plot(ax=ax, picker=5)
            elif mode == 'smith':
                lines = nw.s.plot(ax=ax, picker=5)
            else:
                raise Exception("Mode not implemented!")

    def getNetworks(self):
        return self.networks

class DataReader:
    @staticmethod
    def readData(filename: str, title: str, canvas: MplCanvas) -> SkNetwork:

        network1 = SkNetwork1(filename) #load from file
        network = SkNetwork.from_ntwkv1(network1) #convert to Network2 type
        sns.color_palette() #don't know if this works
        #ax = canvas.axes
        #lines = network.s.db.plot(ax=canvas.axes, picker=5)
        return network

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