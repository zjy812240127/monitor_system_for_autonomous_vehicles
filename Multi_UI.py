# -*- coding: utf-8 -*-
'''
多窗口反复切换，只用PyQt5实现
'''
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton, QComboBox


# class FirstUi(QMainWindow):
class FirstUi(QWidget):
    def __init__(self):
        super(FirstUi, self).__init__()
        self.init_ui()

    def init_ui(self):
        self.resize(500, 350)
        self.setWindowTitle('First Ui')
        # self.btn = QPushButton('jump to FirstUI', self)
        # self.btn.setGeometry(50, 100, 100, 50)
        # self.btn.clicked.connect(self.slot_btn_function)

        self.cb = QComboBox(self)
        self.cb.move(20, 20)

        # 单个添加条目
        self.cb.addItem('1')
        self.cb.addItem('2')
        self.cb.addItem('3')
        # self.cb.addItem('Python')
        # 多个添加条目
        # self.cb.addItems(['Java', 'C#', 'PHP'])
        self.cb.currentIndexChanged[str].connect(self.print_value)  # 条目发生改变，发射信号，传递条目内容
        # self.cb.currentIndexChanged[int].connect(self.print_value)  # 条目发生改变，发射信号，传递条目索引
        # self.cb.highlighted[str].connect(self.print_value)  # 在下拉列表中，鼠标移动到某个条目时发出信号，传递条目内容
        # self.cb.highlighted[int].connect(self.print_value)  # 在下拉列表中，鼠标移动到某个条目时发出信号，传递条目索引

    def print_value(self, i):  ## 设置选中下拉列表的项的响应事件
        print(i,type(i))
        if int(i) == 2:  ## 传过来的是str型参数，转换成int型才可
            print("+++++++++++++++")
            self.hide()
            self.s = SecondUi()
            self.s.show()

        elif int(i) == 3:  ## 传过来的是str型参数，转换成int型才可
            self.hide()
            self.t = ThirdUi()
            self.t.show()





    # def slot_btn_function(self):
    #     self.hide()
    #     self.s = SecondUi()
    #     self.s.show()


class SecondUi(QWidget):
    def __init__(self):
        super(SecondUi, self).__init__()
        self.init_ui()

        self.cb = QComboBox(self)
        self.cb.move(20, 20)

        # 单个添加条目
        self.cb.addItem('1')
        self.cb.addItem('2')
        self.cb.addItem('3')
        # self.cb.addItem('Python')
        # 多个添加条目
        # self.cb.addItems(['Java', 'C#', 'PHP'])
        self.cb.currentIndexChanged[str].connect(self.print_value)  # 条目发生改变，发射信号，传递条目内容
        # self.cb.currentIndexChanged[int].connect(self.print_value)  # 条目发生改变，发射信号，传递条目索引
        # self.cb.highlighted[str].connect(self.print_value)  # 在下拉列表中，鼠标移动到某个条目时发出信号，传递条目内容
        # self.cb.highlighted[int].connect(self.print_value)  # 在下拉列表中，鼠标移动到某个条目时发出信号，传递条目索引

    def print_value(self, i):  ## 设置选中下拉列表的项的响应事件
        print(i)
        if int(i) == 1:  ## 传过来的是str型参数，转换成int型才可
            self.hide()
            self.f = FirstUi()
            self.f.show()

        elif int(i) ==3:  ## 传过来的是str型参数，转换成int型才可
            self.hide()
            self.t = ThirdUi()
            self.t.show()



    def init_ui(self):
        self.resize(500, 350)
        self.setWindowTitle('Second Ui')
        self.btn = QPushButton('jump to FirstUI', self)  # 用来返回到第一个界面
        self.btn.setGeometry(150, 150, 100, 50)
        self.btn.clicked.connect(self.slot_btn_function)

    def slot_btn_function(self):
        self.hide()
        self.f = FirstUi()
        self.f.show()


class ThirdUi(QWidget):
    def __init__(self):
        super(ThirdUi, self).__init__()
        self.init_ui()

        self.cb = QComboBox(self)
        self.cb.move(20, 20)

        # 单个添加条目
        self.cb.addItem('1')
        self.cb.addItem('2')
        self.cb.addItem('3')
        # self.cb.addItem('Python')
        # 多个添加条目
        # self.cb.addItems(['Java', 'C#', 'PHP'])
        self.cb.currentIndexChanged[str].connect(self.print_value)  # 条目发生改变，发射信号，传递条目内容
        # self.cb.currentIndexChanged[int].connect(self.print_value)  # 条目发生改变，发射信号，传递条目索引
        # self.cb.highlighted[str].connect(self.print_value)  # 在下拉列表中，鼠标移动到某个条目时发出信号，传递条目内容
        # self.cb.highlighted[int].connect(self.print_value)  # 在下拉列表中，鼠标移动到某个条目时发出信号，传递条目索引

    def print_value(self, i):  ## 设置选中下拉列表的项的响应事件
        print(i)
        if int(i) == 1:  ## 传过来的是str型参数，转换成int型才可
            self.hide()
            self.f = FirstUi()
            self.f.show()

        elif int(i) == 2:  ## 传过来的是str型参数，转换成int型才可
            self.hide()
            self.s = SecondUi()
            self.s.show()

    def init_ui(self):
        self.resize(500, 350)
        self.setWindowTitle('Third Ui')
        self.btn = QPushButton('jump to FirstUI', self)   # 用来返回到第一个界面
        self.btn.setGeometry(150, 150, 100, 50)
        self.btn.clicked.connect(self.slot_btn_function)

    def slot_btn_function(self):
        self.hide()
        self.f = FirstUi()
        self.f.show()


def main():
    app = QApplication(sys.argv)
    w = FirstUi()
    w.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()