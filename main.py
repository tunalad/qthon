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
    QListView,
)

from wad import unwad


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi("ui/main.ui", self)

        self.wad_path = None
        self.texture_size = 128
        self.texture_spacing = 17

        self.show()

        # disabling some actions (for now)
        self.disable_actions([self.actionView_Animated, self.actionView_Detailed])

        # connections
        self.actionAbout.triggered.connect(lambda: AboutWindow().exec_())
        self.actionOpen.triggered.connect(lambda: self.open_wad())
        self.actionZoom_In.triggered.connect(lambda: self.adjust_zoom("in"))
        self.actionZoom_Out.triggered.connect(lambda: self.adjust_zoom("out"))
        self.actionDelete.triggered.connect(lambda: self.delete_textures())
        self.actionSelect_All.triggered.connect(lambda: self.select_all())
        self.actionDeselect_All.triggered.connect(lambda: self.deselect_all())
        self.actionCopy.triggered.connect(lambda: self.cut_copy_item(is_cut=False))
        self.actionCut.triggered.connect(lambda: self.cut_copy_item(is_cut=True))
        self.actionPaste.triggered.connect(lambda: self.paste_item())

        if not self.wad_path:
            self.setWindowTitle("Untitled - Qt WADitor")

    def adjust_zoom(self, zoom_type):
        if zoom_type == "in" and self.texture_size < 128:
            self.texture_size += 16
        elif zoom_type == "out" and self.texture_size > 16:
            self.texture_size -= 16
        else:
            return

        self.lw_textures.setIconSize(QtCore.QSize(self.texture_size, self.texture_size))

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

        self.lw_textures.clear()
        for t in textures:
            scaled_pixmap = QtGui.QPixmap(f"{temp_dir}/{t}").scaled(
                self.texture_size, self.texture_size, QtCore.Qt.KeepAspectRatio
            )

            scaled_icon = QtGui.QIcon(scaled_pixmap)

            item = QListWidgetItem(scaled_icon, str(t))
            item.setData(QtCore.Qt.UserRole, f"{temp_dir}/{t}")
            self.lw_textures.addItem(item)

    def disable_actions(self, actions):
        self.actionView_Animated.setEnabled(False)
        self.actionView_Detailed.setEnabled(False)

        for a in actions:
            if not a.isEnabled():
                tooltip = a.toolTip() + " [DISABLED]"
                a.setToolTip(tooltip)

    def delete_textures(self):
        print("we deleting stuff")
        textures = self.lw_textures.selectedItems()
        for t in textures:
            self.lw_textures.takeItem(self.lw_textures.row(t))
            # print(t.text())
            # print(t.data(QtCore.Qt.UserRole))

    def select_all(self):
        for i in range(self.lw_textures.count()):
            self.lw_textures.item(i).setSelected(True)

    def deselect_all(self):
        for i in range(self.lw_textures.count()):
            self.lw_textures.item(i).setSelected(False)

    def cut_copy_item(self, is_cut):
        clipboard = QApplication.clipboard()
        mime_data = QtCore.QMimeData()

        clipboard.clear()  # clear the clipboard

        # get selected items
        selected_items = self.lw_textures.selectedItems()
        textures_list = []
        texture_paths = []

        # extract data from items
        for item in selected_items:
            textures_list.append(item.text())
            texture_paths.append(item.data(QtCore.Qt.UserRole))
            if is_cut:
                self.lw_textures.takeItem(self.lw_textures.row(item))

        # make MIME item (for clipboard)
        text = "\n".join(textures_list)
        mime_data.setText(text)

        mime_data.setData("texture_paths", bytes("\n".join(texture_paths), "utf-8"))

        # finally, put that thing to clipboard
        clipboard.setMimeData(mime_data)

    def paste_item(self):
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()

        if mime_data.hasText():
            texture = mime_data.text()
            texture_paths = mime_data.data("texture_paths")

            if texture_paths:
                texture_paths = texture_paths.data().decode("utf-8").split("\n")
                textures_list = mime_data.text().split("\n")

                # Create list items and add them to the list widget
                for i in range(len(texture_paths)):
                    texture = textures_list[i]
                    icon_path = texture_paths[i]

                    scaled_pixmap = QtGui.QPixmap(icon_path).scaled(
                        self.texture_size, self.texture_size, QtCore.Qt.KeepAspectRatio
                    )
                    scaled_icon = QtGui.QIcon(scaled_pixmap)

                    item = QListWidgetItem(scaled_icon, texture)
                    item.setData(QtCore.Qt.UserRole, icon_path)

                    self.lw_textures.addItem(item)


class AboutWindow(QDialog):
    def __init__(self):
        super(AboutWindow, self).__init__()
        uic.loadUi("ui/about.ui", self)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    UIWindow = MainWindow()
    app.exec_()
