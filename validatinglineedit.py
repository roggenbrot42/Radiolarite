from PyQt5 import QtGui, Qt
from PyQt5.QtWidgets import QWidget, QLineEdit, QCompleter
from PyQt5.QtGui import QRegularExpressionValidator, QColor, QPalette, QValidator
from PyQt5.QtCore import Qt

class ValidatingLineEdit(QLineEdit):
    colors = [Qt.red, Qt.yellow, Qt.green]

    def __init__(self, validate: QRegularExpressionValidator, parent: QWidget = None, name=None):
        QLineEdit.__init__(self, parent, name)
        self.validate = validate
        self.textChanged.connect(self.changed)
        self.setValidator(validate)
        self.setInputMask('')
        self.color = None
        self.changed('')

    def changed(self, new_text: str):
        index = 0
        color_index = self.validate.validate(new_text, index) #for some reason, this returns a tuple
        if color_index is None:
            return
        color = QColor(self.colors[color_index[0]]).lighter(196)
        if color != self.color:
            palette = self.palette()
            palette.setColor(QPalette.Base,color)
            self.setPalette(palette)
            self.color = color
