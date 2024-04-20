#!/usr/bin/env python
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=redefined-outer-name
# pylint: disable=multiple-imports
# pylint: disable=missing-class-docstring
# pylint: disable=broad-exception-caught
# pylint: disable=too-few-public-methods
# pylint: disable=unnecessary-lambda

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
    QMessageBox,
    QAction,
)

from RenameWindow import RenameWindow
from AboutWindow import AboutWindow

import history
from wad import unwad


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi("ui/main.ui", self)

        self.wad_path = None
        self.texture_size = 128
        self.texture_spacing = 17
        self.history = history.History()

        self.show()

        # disabling some actions (for now)
        self.disable_actions(
            [
                # self.action,
                # FILE
                self.actionNew,
                self.actionSave,
                self.actionSave_As,
                self.actionImport,
                self.actionExport,
                # EDIT
                # self.actionUndo,
                # self.actionRedo,
                self.actionNew_Item,
                self.actionLoad,
                self.menu_Sort_Items,
                # self.actionRename,
                self.actionResize,
                # VIEW
                # self.menuToolbar,
                # self.menuSidebar,
                # self.menuStatus_Bar,
                self.actionPreferences,
                # HELP
                self.actionHelp,
            ]
        )
        # removing some actions (for now)
        self.remove_actions(
            [
                self.actionView_Animated,
                self.actionView_Detailed,
                # separator in the sidebar
                next(
                    (i for i in self.tb_editor.actions() if i.isSeparator()),
                    None,
                ),
            ]
        )

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
        self.actionRename.triggered.connect(lambda: self.rename_texture())

        self.bars_manager(self.statusbar, self.actionHide_statusbar)
        self.bars_manager(
            self.tb_options, self.actionHide_toolbar, self.actionMovable_toolbar
        )
        self.bars_manager(
            self.tb_editor, self.actionHide_sidebar, self.actionMovable_sidebar
        )

        self.actionUndo.triggered.connect(lambda: self.undo_state())
        self.actionRedo.triggered.connect(lambda: self.redo_state())

        if not self.wad_path:
            self.setWindowTitle("Untitled - Qt WADitor")

    def bars_manager(self, widget, action, movable_action=None):
        if action:
            widget.setVisible(not action.isChecked())
            action.triggered.connect(lambda: widget.setVisible(not action.isChecked()))
        else:
            print(f"can't find action: {widget.objectName()}")

        if movable_action:
            movable_action.setChecked(widget.isMovable())
            movable_action.triggered.connect(
                lambda: widget.setMovable(movable_action.isChecked())
            )

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

        # self.history.reset_state()
        self.history.new_change(self.get_list_state())

    def disable_actions(self, actions):
        for a in actions:
            tooltip = a.toolTip() + " [DISABLED]"
            a.setToolTip(tooltip)
            a.setEnabled(False)

    def remove_actions(self, actions):
        for a in actions:
            a.setVisible(False)

    def delete_textures(self):
        print("we deleting stuff")
        textures = self.lw_textures.selectedItems()
        for t in textures:
            self.lw_textures.takeItem(self.lw_textures.row(t))

        self.history.new_change(self.get_list_state())

    def select_all(self):
        for i in range(self.lw_textures.count()):
            self.lw_textures.item(i).setSelected(True)

    def deselect_all(self):
        for i in range(self.lw_textures.count()):
            self.lw_textures.item(i).setSelected(False)

    def rename_texture(self):
        selected_items = self.lw_textures.selectedItems()

        if len(selected_items) != 1:
            print("can't rename 0 or more than 1 files")
            QMessageBox.warning(
                self, "QtWADitor Error", "Can't rename multiple or no textures."
            )
            return

        item = {
            "title": selected_items[0].text(),
            "path": selected_items[0].data(QtCore.Qt.UserRole),
        }

        rename_win = RenameWindow(item["title"], item["path"])

        if rename_win.exec_():
            new_name = rename_win.get_new_name()
            existing_items = self.lw_textures.findItems(
                new_name, QtCore.Qt.MatchExactly
            )

            if existing_items and existing_items[0] != selected_items[0]:
                print("item already exists bucko")
                QMessageBox.warning(
                    self, "QtWADitor Error", "Texture with this name already exists."
                )
                return

            selected_items[0].setText(new_name)
            self.history.new_change(self.get_list_state())

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

        self.history.new_change(self.get_list_state())

    def get_list_state(self):
        try:
            textures = self.lw_textures
            state = []
            for i in range(textures.count()):
                item = textures.item(i)
                state.append(
                    {"title": item.text(), "path": item.data(QtCore.Qt.UserRole)}
                )
            return state
        except Exception as e:
            print(f"[get_list_state] {e}")
            return e

    def set_list_state(self):
        try:
            # clear list
            self.lw_textures.clear()
            # append items based on state
            textures = self.history.state[self.history.position - 1]["list-state"]
            for t in textures:
                scaled_pixmap = QtGui.QPixmap(f"{t['path']}").scaled(
                    self.texture_size, self.texture_size, QtCore.Qt.KeepAspectRatio
                )

                scaled_icon = QtGui.QIcon(scaled_pixmap)
                item = QListWidgetItem(scaled_icon, str(t["title"]))

                self.lw_textures.addItem(item)
        except Exception as e:
            print(f"[set_list_state] {e}")

    def undo_state(self):
        self.history.undo()
        self.set_list_state()

    def redo_state(self):
        self.history.redo()
        self.set_list_state()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    UIWindow = MainWindow()
    app.exec_()
