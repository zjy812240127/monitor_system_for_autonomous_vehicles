import sys
import os
from PyQt4 import QtGui, uic, QtCore


class car_trace_plot(object):
    def __init__(self):
        qtCreatorFile = os.path.join('car_trace.ui')
        self.ui = uic.loadUi(qtCreatorFile)
        self.data_init()

    def data_init(self):
        self.ui.webView.load(QtCore.QUrl("./BD_map.html"))

    def show(self):
        self.ui.show()


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    ui = car_trace_plot()
    ui.show()
    sys.exit(app.exec_())
