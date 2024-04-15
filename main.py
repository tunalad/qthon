#!/usr/bin/env python

import sys
import ui.resource_ui
from PyQt5 import uic, QtGui
from PyQt5.QtWidgets import QMainWindow, QApplication, QDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi("ui/main.ui", self)
        self.show()

        # connections
        self.actionAbout.triggered.connect(lambda: AboutWindow().exec_())


class AboutWindow(QDialog):
    def __init__(self):
        super(AboutWindow, self).__init__()
        uic.loadUi("ui/about.ui", self)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    UIWindow = MainWindow()
    app.exec_()
