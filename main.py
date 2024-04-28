#!/usr/bin/env python
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=redefined-outer-name
# pylint: disable=multiple-imports
# pylint: disable=missing-class-docstring
# pylint: disable=broad-exception-caught
# pylint: disable=too-few-public-methods
# pylint: disable=unnecessary-lambda

import sys, os, tempfile
import ui.resource_ui
from shutil import rmtree, copyfile
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
from ResizeWindow import ResizeWindow
from AboutWindow import AboutWindow
from PreviewWindow import PreviewWindow

import history
from wad import unwad, wadup, flip_texture


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi("ui/main.ui", self)

        self.wad_path = None
        self.texture_size = 128
        self.texture_spacing = 17
        self.history = history.History()
        self.temp_dir = None

        self.new_wad()

        self.show()

        # togglable items when we selected EXACTLY 1 item
        togglable_actions = [self.actionRename, self.actionResize]

        # togglable items when we selected LESS than 1 item
        togglable_actions_lto = [
            self.actionMirror,
            self.actionFlip,
            self.actionCut,
            self.actionCopy,
            self.actionDelete,
        ]

        # first, we disable them
        self.disable_actions(togglable_actions)
        self.disable_actions(togglable_actions_lto)

        # disabling some actions (for now)
        self.disable_actions(
            [
                # self.action,
                # EDIT
                self.actionNew_Item,
                self.actionLoad,
                self.menu_Sort_Items,
                # VIEW
                self.actionPreferences,
                # HELP
                self.actionHelp,
            ]
        )

        # CONNECTIONS
        ## trigger
        self.actionAbout.triggered.connect(lambda: AboutWindow().exec_())
        self.actionQuit.triggered.connect(lambda: self.close())

        self.actionOpen.triggered.connect(lambda: self.open_wad())
        self.actionImport.triggered.connect(lambda: self.import_wad())
        self.actionNew.triggered.connect(lambda: self.new_wad())

        self.actionZoom_In.triggered.connect(lambda: self.adjust_zoom("in"))
        self.actionZoom_Out.triggered.connect(lambda: self.adjust_zoom("out"))
        self.actionDelete.triggered.connect(lambda: self.delete_textures())
        self.actionSelect_All.triggered.connect(lambda: self.de_select_all(True))
        self.actionDeselect_All.triggered.connect(lambda: self.de_select_all(False))
        self.actionCopy.triggered.connect(lambda: self.cut_copy_item(is_cut=False))
        self.actionCut.triggered.connect(lambda: self.cut_copy_item(is_cut=True))
        self.actionPaste.triggered.connect(lambda: self.paste_item())
        self.actionRename.triggered.connect(lambda: self.rename_texture())
        self.actionResize.triggered.connect(lambda: self.resize_texture())
        self.actionFlip.triggered.connect(lambda: self.flip_texture(mirror=False))
        self.actionMirror.triggered.connect(lambda: self.flip_texture(mirror=True))

        self.actionUndo.triggered.connect(lambda: self.undo_redo(False))
        self.actionRedo.triggered.connect(lambda: self.undo_redo(True))

        self.actionSave.triggered.connect(lambda: self.save_wad())
        self.actionSave_As.triggered.connect(lambda: self.save_wad(save_as=True))

        self.actionView_Detailed.triggered.connect(lambda: self.preview_texture())
        self.actionView_Animated.triggered.connect(lambda: self.preview_texture(True))

        ## item selection
        ### statusbar preview
        self.lw_textures.itemSelectionChanged.connect(
            lambda: self.statusbar.showMessage(
                f'{self.history.state[self.history.position -1]["list-state"][self.lw_textures.currentRow()]}'
            )
        )

        ### togglable items when we selected EXACTLY 1 item
        self.lw_textures.itemSelectionChanged.connect(
            lambda: self.active_on_selection(togglable_actions, False)
        )

        ### togglable items when we selected LESS than 1 item
        self.lw_textures.itemSelectionChanged.connect(
            lambda: self.active_on_selection(togglable_actions_lto, True)
        )

        ### disable detailed & animation preview
        self.disable_previews()
        self.lw_textures.itemSelectionChanged.connect(lambda: self.disable_previews())

        # TOGGLING BARS
        self.bars_manager(self.statusbar, self.actionHide_statusbar)
        self.bars_manager(
            self.tb_options, self.actionHide_toolbar, self.actionMovable_toolbar
        )
        self.bars_manager(
            self.tb_editor, self.actionHide_sidebar, self.actionMovable_sidebar
        )

        # WINDOW TITLE

        if not self.wad_path:
            self.setWindowTitle("Untitled - Qt WADitor")

    def closeEvent(self, event):
        try:
            rmtree(self.temp_dir)
        except Exception as e:
            print(f"[closeEvent] {e}")
        finally:
            event.accept()

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

    def preview_texture(self, animation=False):
        selected_items = self.lw_textures.selectedItems()

        if len(selected_items) != 1:
            print("can't preview 0 or more than 1 textures")
            QMessageBox.warning(
                self, "QtWADitor Error", "Can't preview multiple or no textures."
            )
            return

        item = {
            "title": selected_items[0].text(),
            "path": selected_items[0].data(QtCore.Qt.UserRole),
        }
        if os.path.basename(item["path"]).startswith("*") and animation:
            QMessageBox.warning(
                self, "QtWADitor Error", "No water animations implemented yet :("
            )
        else:
            PreviewWindow(item["path"], 3, animation).exec_()

    def new_wad(self):
        try:
            if self.temp_dir:
                rmtree(self.temp_dir)
                self.lw_textures.clear()

            self.temp_dir = tempfile.mkdtemp(prefix="tmp-qtwaditor-")
            self.history.set_temp_dir(self.temp_dir)
            self.history.new_change(self.get_list_state())  # empty snap

            self.setWindowTitle(f"Untitled - Qt WADitor")
        except Exception as e:
            print(f"[new_wad] {e}")

    def open_wad(self):
        try:
            self.wad_path, _ = QFileDialog.getOpenFileName(
                self, "Select a WAD file", "", "WAD Files (*.wad);;All Files (*)"
            )

            if not self.wad_path:
                return

            if self.temp_dir:
                rmtree(self.temp_dir)

            self.temp_dir = tempfile.mkdtemp(prefix="tmp-qtwaditor-")
            self.history.set_temp_dir(self.temp_dir)

            self.lw_textures.clear()
            self.unpack_wad(self.wad_path)
            self.setWindowTitle(f"{os.path.basename(self.wad_path)} - Qt WADitor")
        except Exception as e:
            print(f"[open_wad] {e}")

    def import_wad(self):
        try:
            wad_path, _ = QFileDialog.getOpenFileName(
                self, "Select a WAD file", "", "WAD Files (*.wad);;All Files (*)"
            )

            if wad_path:
                self.unpack_wad(wad_path)
        except Exception as e:
            print(f"[import_wad] {e}")

    def save_wad(self, save_as=False):
        try:
            if not self.wad_path or save_as:
                self.wad_path, _ = QFileDialog.getSaveFileName(
                    self, "Save WAD file", "", "WAD Files (*.wad);;All Files (*)"
                )

            if self.wad_path:
                wadup(self.temp_dir, self.wad_path)

        except Exception as e:
            print(f"[save_wad] {e}")

    def unpack_wad(self, path):
        unwadded = unwad(path, self.temp_dir)
        temp_dir = unwadded[0]
        textures = unwadded[1]

        for t in textures:
            scaled_pixmap = QtGui.QPixmap(f"{temp_dir}/{t}").scaled(
                self.texture_size, self.texture_size, QtCore.Qt.KeepAspectRatio
            )

            scaled_icon = QtGui.QIcon(scaled_pixmap)
            item = QListWidgetItem(scaled_icon, str(t))

            item.setData(QtCore.Qt.UserRole, f"{temp_dir}/{t}.png")  # icon path

            self.lw_textures.addItem(item)

        self.history.new_change(self.get_list_state())

    def disable_actions(self, actions, not_implemented=True):
        for a in actions:
            tooltip = a.toolTip()

            if not_implemented:
                tooltip += " [NOT IMPLEMENTED]"

            a.setToolTip(tooltip)
            a.setEnabled(False)

    def disable_previews(self):
        selected_items = self.lw_textures.selectedItems()

        # disable detailed
        if len(selected_items) != 1:
            self.actionView_Detailed.setEnabled(False)
        else:
            self.actionView_Detailed.setEnabled(True)

        # disable animation
        if len(selected_items) != 1 or not (
            selected_items[0].text().startswith("+")
            or selected_items[0].text().startswith("*")
        ):
            self.actionView_Animated.setEnabled(False)
        else:
            self.actionView_Animated.setEnabled(True)

    def delete_textures(self):
        print("we deleting stuff")
        textures = self.lw_textures.selectedItems()
        for t in textures:
            self.lw_textures.takeItem(self.lw_textures.row(t))
            os.remove(t.data(QtCore.Qt.UserRole))

        self.history.new_change(self.get_list_state())

    def flip_texture(self, mirror=False):
        selected_items = self.lw_textures.selectedItems()

        if len(selected_items) < 1:
            print("nothing is selected buckoo")
            return

        for item in selected_items:
            icon_path = item.data(QtCore.Qt.UserRole)

            if mirror:  # horizontally (mirrored)
                flip_texture(icon_path, True)
            else:  # vertically (flipped)
                flip_texture(icon_path, False)

            original_pixmap = QtGui.QPixmap(icon_path)
            scaled_pixmap = original_pixmap.scaled(
                self.texture_size, self.texture_size, QtCore.Qt.KeepAspectRatio
            )

            item.setIcon(QtGui.QIcon(scaled_pixmap))
            item.setData(QtCore.Qt.UserRole, icon_path)

        self.history.new_change(self.get_list_state())

    def de_select_all(self, toggle):
        try:
            for i in range(self.lw_textures.count()):
                self.lw_textures.item(i).setSelected(toggle)
        except Exception as e:
            print(f"[de_select_all] {e}")

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

            os.rename(item["path"], f"{self.temp_dir}/{new_name}.png")

            selected_items[0].setText(new_name)
            selected_items[0].setData(
                QtCore.Qt.UserRole, f"{self.temp_dir}/{new_name}.png"
            )
            self.history.new_change(self.get_list_state())

    def resize_texture(self):
        selected_items = self.lw_textures.selectedItems()
        textures = []

        if len(selected_items) < 1:
            print("can't resize 0 files")
            QMessageBox.warning(
                self, "QtWADitor Error", "No textures selected for resizing"
            )
            return

        for i in selected_items:
            textures.append({"title": i.text(), "path": i.data(QtCore.Qt.UserRole)})

        resize_win = ResizeWindow(textures)

        if resize_win.exec_():
            print("do sth post texture(s) resizing idk")
            self.history.new_change(self.get_list_state())
            self.set_list_state()

    def cut_copy_item(self, is_cut):
        clipboard = QApplication.clipboard()
        mime_data = QtCore.QMimeData()

        clipboard.clear()  # clear the clipboard

        # get selected items
        selected_items = self.lw_textures.selectedItems()
        textures_list = []
        texture_paths = []
        flip_list = []
        mirror_list = []

        # extract data from items
        for item in selected_items:
            textures_list.append(item.text())
            # texture_paths.append(item.data(QtCore.Qt.UserRole))
            texture_paths.append(
                f"{self.temp_dir}/snapshots/{(self.history.state[self.history.position - 1]['time'])}/{item.text()}.png"
            )
            flip_list.append(item.data(QtCore.Qt.UserRole + 1))
            mirror_list.append(item.data(QtCore.Qt.UserRole + 2))
            if is_cut:
                self.lw_textures.takeItem(self.lw_textures.row(item))
                print(
                    f"{self.temp_dir}/snapshots/{(self.history.state[self.history.position - 1]['time'])}/{item.text()}.png"
                )
                os.remove(item.data(QtCore.Qt.UserRole))

        # make MIME item (for clipboard)
        text = "\n".join(textures_list)
        mime_data.setText(text)

        mime_data.setData("texture_paths", bytes("\n".join(texture_paths), "utf-8"))
        mime_data.setData(
            "flip_list", bytes("\n".join(str(flip) for flip in flip_list), "utf-8")
        )
        mime_data.setData(
            "mirror_list",
            bytes("\n".join(str(mirror) for mirror in mirror_list), "utf-8"),
        )

        # finally, put that thing to clipboard
        clipboard.setMimeData(mime_data)

        if is_cut:
            self.history.new_change(self.get_list_state())

    def paste_item(self):
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()

        if mime_data.hasText():
            texture = mime_data.text()
            texture_paths = mime_data.data("texture_paths")
            flip_list = mime_data.data("flip_list")
            mirror_list = mime_data.data("mirror_list")

            if texture_paths:
                texture_paths = texture_paths.data().decode("utf-8").split("\n")
                textures_list = mime_data.text().split("\n")
                flip_list = flip_list.data().decode("utf-8").split("\n")
                mirror_list = mirror_list.data().decode("utf-8").split("\n")

                existing_textures = [item["title"] for item in self.get_list_state()]

                # create list items and add them to the list widget
                for i in range(len(texture_paths)):
                    texture = textures_list[i]
                    icon_path = texture_paths[i]
                    original_path = icon_path

                    if texture in existing_textures:
                        count = 1
                        # slap suffix
                        while f"{texture} ({count})" in existing_textures:
                            count += 1
                        texture = f"{texture} ({count})"
                        # to the file name too
                        icon_path, ext = os.path.splitext(icon_path)
                        icon_path = f"{icon_path} ({count}){ext}"

                    # copy the actual file to the new path
                    copy_path = os.path.join(
                        self.temp_dir, f"{os.path.basename(icon_path)}"
                    )

                    copyfile(original_path, copy_path)

                    # create the item
                    scaled_pixmap = QtGui.QPixmap(copy_path).scaled(
                        self.texture_size, self.texture_size, QtCore.Qt.KeepAspectRatio
                    )
                    scaled_icon = QtGui.QIcon(scaled_pixmap)

                    item = QListWidgetItem(scaled_icon, texture)
                    item.setData(QtCore.Qt.UserRole, copy_path)
                    item.setData(QtCore.Qt.UserRole + 1, flip_list[i] == "True")
                    item.setData(QtCore.Qt.UserRole + 2, mirror_list[i] == "True")

                    # apply the mirroring
                    transform = QtGui.QTransform()
                    transform.scale(
                        -1 if mirror_list[i] == "True" else 1,
                        -1 if flip_list[i] == "True" else 1,
                    )
                    pixmap = scaled_pixmap.transformed(transform)
                    item.setIcon(QtGui.QIcon(pixmap))

                    self.lw_textures.addItem(item)

        self.history.new_change(self.get_list_state())

    def get_list_state(self):
        try:
            textures = self.lw_textures
            state = []
            for i in range(textures.count()):
                item = textures.item(i)
                state.append(
                    {
                        "title": item.text(),
                        "path": item.data(QtCore.Qt.UserRole),
                    }
                )

            return state
        except Exception as e:
            print(f"[get_list_state] {e}")
            return e

    def set_list_state(self):
        try:
            # clear list
            self.lw_textures.clear()
            self.history.load_snapshot(
                str(self.history.state[self.history.position - 1]["time"])
            )
            # append items based on state
            textures = self.history.state[self.history.position - 1]["list-state"]
            for t in textures:
                scaled_pixmap = QtGui.QPixmap(f"{t['path']}").scaled(
                    self.texture_size, self.texture_size, QtCore.Qt.KeepAspectRatio
                )

                scaled_icon = QtGui.QIcon(scaled_pixmap)
                item = QListWidgetItem(scaled_icon, t["title"])

                item.setData(QtCore.Qt.UserRole, t["path"])
                item.setIcon(QtGui.QIcon(scaled_pixmap))

                self.lw_textures.addItem(item)
        except Exception as e:
            print(f"[set_list_state] {e}")

    def undo_redo(self, redo=False):
        try:
            if redo:
                self.history.redo()
            else:
                self.history.undo()

            self.set_list_state()
        except Exception as e:
            print(f"[undo_redo] {e}")

    def active_on_selection(self, actions, multi=False):
        for a in actions:
            if not multi and len(self.lw_textures.selectedItems()) == 1:
                a.setEnabled(True)
            elif multi and len(self.lw_textures.selectedItems()) > 0:
                a.setEnabled(True)
            else:
                a.setEnabled(False)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    UIWindow = MainWindow()
    app.exec_()
