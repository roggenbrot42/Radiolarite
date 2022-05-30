import typing

import matplotlib.lines
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from skrf.network2 import Network as SkNetwork


class NetworkItem(QStandardItem):

    _type = 1516

    def __init__(self, network : SkNetwork):
        self._network: SkNetwork = network
        self._parameters: dict[tuple[int, int], 'ParamItem'] = {}
        super(QStandardItem, self).__init__()
        self._makeChildren()
        self.setData(network.name, Qt.DisplayRole)
        self.setSelectable(False)

    def type(self) -> int:
        return self._type

    def setData(self, value: typing.Any, role: int = ...) -> None:
        if role == Qt.EditRole:
            self._network.name = value
        super().setData(value, role)

    def network(self) -> SkNetwork:
        return self._network

    def __str__(self):
        return self._network.__str__()

    def enabledParams(self) -> list['ParamItem']:
        prm = []
        for p in self._parameters.values():
            if p.checkState():
                prm.append(p)
        return prm

    def enabledParamsTuple(self) -> list[tuple[int,int]]:
        prm = []
        for p in self._parameters.values():
            if p.checkState():
                prm.append((p.m,p.n))
        return prm

    def params(self):
        return list(self._parameters.values())

    def _makeChildren(self):
        rows = len(self._network.port_tuples)
        for p in self._network.port_tuples:
            self._parameters[p] = ParamItem(parent=self, m=p[0], n=p[1])
        self.appendRows(self._parameters.values())

class ParamItem(QStandardItem):
    _type = 1517

    def __init__(self, parent, m, n):
        super().__init__(parent)
        self._parent: NetworkItem = parent
        self.m = m
        self.n = n
        self._trace: matplotlib.lines.Line2D = None
        self.setEditable(False)
        self.setCheckable(True)
        self.setCheckState(Qt.Checked)
        self.setData("S{}{}".format(m+1,n+1),Qt.DisplayRole)

    def __str__(self):
        return self.data(Qt.DisplayRole)

    def getTrace(self):
        return self._trace

    def toTuple(self):
        return (self.m,self.n)