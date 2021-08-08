import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtWebEngineWidgets import *
class Map_load2(QMainWindow):
    def __init__(self):
        super(Map_load2, self).__init__()
        self.setWindowTitle('百度')  #窗口标题
        self.setGeometry(5,30,1355,730)  #窗口的大小和位置设置
        self.browser=QWebEngineView()
        #加载外部的web界面
        # self.browser.load(QUrl('file:///E:/pycharm_project/TCP/track.html'))


        # self.browser.load(QUrl('file:///E:/pycharm_project/TCP%2010%2025/BD_map.html'))  # 载入.html代码
        self.browser.load(QUrl(QFileInfo("BD_map.html").absoluteFilePath()))
        self.setCentralWidget(self.browser)
if __name__ == '__main__':
    app=QApplication(sys.argv)
    win=Map_load2()
    win.show()
    app.exit(app.exec_())

