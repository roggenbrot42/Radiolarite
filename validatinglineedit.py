from abc import ABC
from PyQt5 import QtGui, Qt
from PyQt5.QtWidgets import QWidget, QLineEdit, QCompleter
from PyQt5.QtGui import QRegularExpressionValidator, QColor, QPalette, QValidator
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QRegularExpression


def setupTimeRangeValidator():
    time_regex = QRegularExpression("[\-]?[0-9]+\.?[0-9]*(\s([fpnmµ]|mu)?s)?")
    time_validator: QRegularExpressionValidator = QRegularExpressionValidator(time_regex)
    return time_validator


def setupFrequencyRangeValidator():
    freq_regex = QRegularExpression("[0-9]+\.?[0-9]*( [kMGT]?Hz)?")
    freq_validator: QRegularExpressionValidator = QRegularExpressionValidator(freq_regex)
    return freq_validator


class Dimension:
    units = {}

    def __init__(self):
        self.unit = None
        self.num = None
        self.value = None

    def parseValue(self, number, unit):
        if unit not in self.units:
            raise ValueError
        if type(number) is not int and type(number) is not float:
            raise ValueError
        self.value = number * self.units[unit]
        self.num = number
        self.unit = unit

    def getValue(self):
        return self.value

    def getUnit(self):
        return self.unit

    def getNum(self):
        return self.num


class TimeValue(Dimension):
    units = {'fs': 1e-15, 'ps': 1e-12, 'ns': 1e-9, 'ms': 1e-6, 's': 1}

    def __init__(self, number, unit):
        self.parseValue(number, unit)

    @staticmethod
    def defaultUnit() -> str:
        return 'ns'


class FrequencyValue(Dimension):

    def __init__(self, number, unit):
        self.units = {'Hz': 1, 'kHz': 1e3, 'MHz': 1e6, 'GHz': 1e9, 'THz': 1e12}
        self.parseValue(number, unit)

    @staticmethod
    def defaultUnit() -> str:
        return 'GHz'


class ValidatingLineEdit(QLineEdit):
    colors = [Qt.red, Qt.yellow, Qt.green]

    def __init__(self, validate: QRegularExpressionValidator, text="", parent: QWidget = None, name=None):
        QLineEdit.__init__(self, parent, name)
        self.validate = validate
        self.textChanged.connect(self.changed)
        self.setValidator(validate)
        self.setInputMask('')
        self.color = None
        self.changed('')
        self.setText(text)

    def changed(self, new_text: str):
        index = 0
        color_index = self.validate.validate(new_text, index)  # for some reason, this returns a tuple
        if color_index is None:
            return
        color = QColor(self.colors[color_index[0]]).lighter(196)
        if color != self.color:
            palette = self.palette()
            palette.setColor(QPalette.Base, color)
            self.setPalette(palette)
            self.color = color


class ValidatingTimeEdit(ValidatingLineEdit):

    def __init__(self, text: str = "", parent: QWidget = None, name=None):
        super(ValidatingTimeEdit, self).__init__(setupTimeRangeValidator(), text, parent, name)

    def getValue(self) -> TimeValue:
        strs = self.text().split(' ')
        value = None
        if len(strs) == 0:
            raise ValueError
        elif len(strs) > 0:
            number = float(strs[0])
            unit = TimeValue.defaultUnit()
            if len(strs) > 1:
                unit = strs[1]
                if unit not in TimeValue.units.keys():
                    raise ValueError
            value = TimeValue(number, unit)
        return value


class ValidatingFrequencyEdit(ValidatingLineEdit):

    def __init__(self, text: str = "", parent: QWidget = None, name=None):
        super(ValidatingLineEdit, self).__init__(setupFrequencyRangeValidator(), text, parent, name)

    def getValue(self) -> FrequencyValue:
        strs = self.text().split(' ')
        value = None
        if len(strs) == 0:
            raise ValueError
        elif len(strs) > 0:
            number = float(strs[0])
            unit = FrequencyValue.defaultUnit()
            if len(strs) > 1:
                unit = strs[1]
                if unit not in FrequencyValue.units.keys():
                    raise ValueError
            value = FrequencyValue(number, unit)
        return value
