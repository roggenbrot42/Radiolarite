from collections import OrderedDict

import matplotlib
import openpyxl.drawing.image
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from matplotlib import axes
from matplotlib.backend_bases import MouseButton
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from skrf.network2 import Network as SkNetwork
import skrf
from skrf.plotting import *

from networkitem import NetworkItem, ParamItem
from validatinglineedit import TimeValue

plotModes = OrderedDict((
    ('decibels', 'db'),
    ('smith', 'smith'),
    ('magnitude', 'mag'),
    ('phase (deg)', 'deg'),
    ('phase (rad)', 'rad'),
    ('real', 're'),
    ('imaginary', 'im'),
    ('time (dB)', 's_time'),
    ('Z(t)', 'z_time')
))


class MplCanvas(FigureCanvasQTAgg):
    line2leg: dict[Line2D, Line2D]
    selectionChange = pyqtSignal(int)

    def __init__(self, parent=None, width=8, height=4.5, dpi=120, gridMajor: bool=True, gridMinor: bool=True):
        fig = Figure(figsize=(width, height), dpi=dpi)
        super(MplCanvas, self).__init__(fig)
        fig.add_subplot(111)
        fig.canvas.mpl_connect('pick_event', self.on_pick)
        fig.canvas.mpl_connect('button_press_event', self.button_press_event)
        fig.canvas.mpl_connect('button_release_event', self.button_release_event)
        fig.canvas.mpl_connect('key_press_event', self.key_event)
        self.networkModel: QStandardItemModel = None
        self.selectionModel = None
        self.default_linewidth = 1.5  # don't change or it won't match with mpl default and glitch ---
        self.picked: matplotlib.lines.Line2D = None  # type: Line2D #always the line, never legend
        self.pickstate = 0
        self.line2leg = {}
        self.trace2param = {}
        self.plotMode = 'db'
        self.gridMajor = gridMajor
        self.gridMinor = gridMinor
        self.grid()
        self.figure.tight_layout()
        self._lines = []
        self.xlimits = ['', '']

    def axes(self):
        ax = self.figure.get_axes()
        if isinstance(ax,list):
            return ax[0]
        else:
            return ax

    def reset(self):
        for ax in self.figure.get_axes():
            ax.clear()
        self.figure.clf(keep_observers=False)
        self.figure.subplots()
        self.trace2param = {}
        self.pickstate = 0
        self._lines = []
        self.picked = None
        self.grid()
        self.draw_idle()

    def setModel(self, networkModel: QStandardItemModel):
        if isinstance(networkModel, QStandardItemModel):
            self.networkModel = networkModel
            self.networkModel.itemChanged.connect(self.redrawAll)
            self.networkModel.rowsInserted.connect(self.addTraces)
            self.networkModel.rowsAboutToBeRemoved.connect(self.removeTrace)
            self.networkModel.modelReset.connect(self.reset)
        else:
            raise Exception("Wrong type for Network Model")

    def setSelectionModel(self, selectionModel: QItemSelectionModel):
        if isinstance(selectionModel, QItemSelectionModel):
            self.selectionModel = selectionModel
            # self.selectionModel.selectionChanged.connect(self.selectionChanged)
        else:
            raise Exception("Wrong type for Selection Model")

    def addTraces(self, parent: QModelIndex, first: int, last: int):
        nwItem = self.networkModel.itemFromIndex(self.networkModel.index(first, 0))
        if isinstance(nwItem, NetworkItem):  # this contains a network
            nw = nwItem.network()
            parm = nwItem.enabledParams()
            for p in parm:
                ax = self.figure.axes[0]
                traces = self.plotNetwork(nw, p.toTuple())
                if traces and len(traces) > 0:
                    self.trace2param[traces[0]] = p
            self.generate_line_to_legend()
            self.draw_idle()

    def removeTrace(self, parent: QModelIndex, first: int, last: int):
        for row in range(first, last + 1):
            idx = self.networkModel.index(row, 0)
            item: NetworkItem = self.networkModel.itemFromIndex(idx)
            for p in item.params():
                pass
            self.generate_line_to_legend()
            self.draw_idle()

    def redrawAll(self):
        self.reset()
        if self.plotMode == 'smith':
            smith(ax=self.axes(), draw_labels=True, draw_vswr=True)
        else:
            self.grid()
        for i in range(self.networkModel.rowCount()):
            idx = self.networkModel.index(i, 0)
            ntwk: NetworkItem = self.networkModel.itemFromIndex(idx)
            if isinstance(ntwk, NetworkItem):
                for p in ntwk.enabledParams():
                    traces = self.plotNetwork(ntwk.network(), p.toTuple())
                    if traces and len(traces) > 0:
                        self.trace2param[traces[0]] = p
        if self.xlimits[1] != '' and self.plotMode in ['z_time', 's_time']:
            self.axes().set_xlim(float(self.xlimits[0]), float(self.xlimits[1]))
        self.figure.tight_layout()
        self.generate_line_to_legend()
        self.draw_idle()

    def plotNetwork(self, network: SkNetwork, param: tuple[int, int] = None):
        ax = self.axes()
        if isinstance(network, SkNetwork):
            pm = self.plotMode
            if pm == 's_time':
                prm = network.s_time
                if param is None:
                    lines = prm.db.plot(ax=self.axes(), picker=5)
                else:
                    lines = prm.db.plot(m=param[0], n=param[1], ax=self.axes(), picker=5)
            elif pm == 'z_time':
                nw1 = skrf.Network(s=network.s.val, f=network.frequency.f)
                nw1 = nw1.extrapolate_to_dc(kind='linear')
                lines = nw1.s11.plot_z_time_step(window='hamming', ax=self.axes(), picker=5, label=network.name)
            else:
                if self.xlimits[1] != '':
                    prm = network['{}-{}'.format(self.xlimits[0], self.xlimits[1])].s
                else:
                    prm = network.s
                if pm == 'smith':
                    rep = prm
                    val = prm.val[:, param[0], param[1]]
                    lines = self.axes().plot(npy.real(val), npy.imag(val),
                                             picker=5,
                                             label="{},S{}{}".format(
                                                 network.name, param[0]+1, param[1]+1)
                                             )
                elif hasattr(prm, pm):
                    rep = getattr(prm, pm)
                    if param is None:
                        lines = rep.plot(ax=ax, picker=5)
                    else:
                        lines = rep.plot(m=param[0], n=param[1], ax=ax, picker=5)
                else:
                    raise Exception("Unknown representation")

            if lines:
                self._lines.extend(lines)
            return lines

    def changePlotMode(self, index):
        self.plotMode = list(plotModes.values())[index]
        self.setXlimits('', '')
        self.redrawAll()

    def setXlimits(self, mini, maxi):
        self.xlimits = [mini, maxi]
        self.redrawAll()

    def selectionChanged(self, selected: QItemSelection, deselected: QItemSelection):
        for idx in selected.indexes():
            item = self.networkModel.itemFromIndex(idx)
            if isinstance(item, ParamItem):
                self.pickLine(item.getTrace())
        if len(selected) == 0:
            self.pickLine(None)
        pass

    def grid(self):
        self.toggleMajorGrid(self.gridMajor)
        self.toggleMinorGrid(self.gridMinor)

    def toggleMajorGrid(self, b: bool):
        self.axes().grid(visible=b, which='major')
        self.draw_idle()

    def toggleMinorGrid(self, b: bool):
        self.axes().grid(visible=b, which='minor', linestyle='--', linewidth=0.25 * self.default_linewidth)
        if b:
            self.axes().minorticks_on()
        else:
            self.axes().minorticks_off()
        self.draw_idle()

    def legendChange(self, columns: int):
        self.axes().legend(ncol = columns)
        self.draw_idle()

    def generate_line_to_legend(self):
        ax = self.axes()
        if len(self._lines) == 0:
            return
        legend = ax.legend()
        legend.set_draggable(True)
        self.line2leg = {}
        for legline, origline in zip(legend.get_lines(), self._lines):
            legline.set_picker(5)  # Enable picking on the legend line.
            self.line2leg[legline] = (origline, True)
            self.line2leg[origline] = (legline, False)

    def pickLine(self, trace: Line2D):
        if trace is not self.picked:
            if self.picked is not None:
                self.picked.set_linewidth(self.default_linewidth)
                self.line2leg[self.picked][0].set_linewidth(self.default_linewidth)

            if trace is not None:
                trace.set_linewidth(2 * self.default_linewidth)
                self.line2leg[trace][0].set_linewidth(2 * self.default_linewidth)
                if trace in self.line2leg:  # is an axis entry
                    self.picked = trace
                elif trace in self.line2leg.values():
                    self.picked = self.line2leg[trace]
                self.pickstate = 1
            else:
                self.pickstate = 0
                self.picked = None
            self.draw_idle()

    def on_pick(self, event: matplotlib.backend_bases.Event):
        if isinstance(event.artist, Line2D):
            if self.line2leg[event.artist][1]:
                trace = self.line2leg[event.artist][0]
            else:
                trace = event.artist
            if trace is not self.picked:
                self.pickLine(trace)
                item = self.trace2param[self.picked]
                self.selectionModel.select(self.networkModel.indexFromItem(item), QItemSelectionModel.ClearAndSelect)
                self.selectionChange.emit(self.pickstate)

    def button_release_event(self, event: matplotlib.backend_bases.Event):
        if event.button == MouseButton.LEFT:
            if self.picked is None:
                for line in self.line2leg:
                    self.line2leg[line][0].set_linewidth(self.default_linewidth)
                    line.set_linewidth(self.default_linewidth)
                self.pickstate = 0
                self.draw_idle()
            elif self.pickstate == 2:
                self.picked.set_linewidth(self.default_linewidth)
                self.line2leg[self.picked][0].set_linewidth(self.default_linewidth)
                self.picked = None
                self.selectionModel.clear()
                self.draw_idle()
            self.pickstate = 2

    def button_press_event(self, event):
        pass

    def key_event(self, event):
        if event.key == 'delete' and self.picked is not None:
            try:
                param = self.trace2param[self.picked]
                self.picked = None
                self.pickstate = 0
                param.setCheckState(Qt.Unchecked)
            except ValueError:
                print("picked error: {}".format(self.picked))
        elif event.key == 'f2' and self.picked is not None:
            h, l = self.axes.get_legend_handles_labels()
            index = self.figure.axes[0].lines.index(self.picked)
            (text, result) = QInputDialog.getText(self, 'Enter new Label', 'Label', text=l[index])
            if text:
                l[index] = text
                self.axes.legend(h, l)
                self.draw_idle()
