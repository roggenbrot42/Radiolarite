import sys
import platform

import matplotlib
from PyQt5.QtWidgets import *


import ctypes

from mainwindow import DragDropEventHandler, MainWindow

myappid = u'roggenbrot42.radiolarite'  # arbitrary string

if platform.system() == 'Windows':
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid) #group in taskbar

matplotlib.use('Qt5Agg')

def window():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    if len(sys.argv) > 1:
        filelist = sys.argv[1:]
        win.readFiles(filelist)
    sys.exit(app.exec_())


if __name__ == '__main__':
    window()
