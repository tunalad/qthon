#!/usr/bin/env python

import sys
import ui.resource_ui
from PyQt5 import uic, QtGui
from PyQt5.QtWidgets import QMainWindow, QApplication, QDialog, QListWidgetItem

from wad import unwad


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi("ui/main.ui", self)
        self.show()

        # disabling some actions (for now)
        self.disable_actions([self.actionView_Animated, self.actionView_Detailed])

        # connections
        self.actionAbout.triggered.connect(lambda: AboutWindow().exec_())

        self.open_wad("./catacomb.wad")

    def open_wad(self, path):
        unwadded = unwad(path)
        temp_dir = unwadded[0]
        textures = unwadded[1]

        self.lw_textures.clear()
        for t in textures:
            pic = QtGui.QIcon(f"{temp_dir}/{t}")
            item = QListWidgetItem(pic, str(t))
            self.lw_textures.addItem(item)

    def disable_actions(self, actions):
        self.actionView_Animated.setEnabled(False)
        self.actionView_Detailed.setEnabled(False)

        for a in actions:
            if not a.isEnabled():
                tooltip = a.toolTip() + " [DISABLED]"
                a.setToolTip(tooltip)


class AboutWindow(QDialog):
    def __init__(self):
        super(AboutWindow, self).__init__()
        uic.loadUi("ui/about.ui", self)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    UIWindow = MainWindow()
    app.exec_()
