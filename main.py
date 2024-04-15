#!/usr/bin/env python

import sys, os
import ui.resource_ui
from PyQt5 import uic, QtGui, QtCore
from PyQt5.QtWidgets import (
    QMainWindow,
    QApplication,
    QDialog,
    QListWidgetItem,
    QFileDialog,
)

from wad import unwad


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi("ui/main.ui", self)

        self.wad_path = None

        self.show()

        # disabling some actions (for now)
        self.disable_actions([self.actionView_Animated, self.actionView_Detailed])

        # connections
        self.actionAbout.triggered.connect(lambda: AboutWindow().exec_())
        self.actionOpen.triggered.connect(lambda: self.open_wad())

        if not self.wad_path:
            self.setWindowTitle("Untitled - Qt WADitor")

    def open_wad(self):
        try:
            self.wad_path, _ = QFileDialog.getOpenFileName(
                self, "Select a WAD file", "", "WAD Files (*.wad);;All Files (*)"
            )

            self.unpack_wad(self.wad_path)
            self.setWindowTitle(f"{os.path.basename(self.wad_path)} - Qt WADitor")

        except Exception as e:
            print(f"[open_wad] {e}")

    def unpack_wad(self, path):
        unwadded = unwad(path)
        temp_dir = unwadded[0]
        textures = unwadded[1]
        texture_size = 128
        texture_spacing = 16

        self.lw_textures.clear()
        for t in textures:
            scaled_pixmap = QtGui.QPixmap(f"{temp_dir}/{t}").scaled(
                texture_size, texture_size, QtCore.Qt.KeepAspectRatio
            )

            scaled_icon = QtGui.QIcon(scaled_pixmap)

            item = QListWidgetItem(scaled_icon, str(t))
            self.lw_textures.addItem(item)

        self.lw_textures.setIconSize(QtCore.QSize(texture_size, texture_size))
        self.lw_textures.setSpacing(texture_spacing)

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
