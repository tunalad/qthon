# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=redefined-outer-name
# pylint: disable=multiple-imports
# pylint: disable=missing-class-docstring
# pylint: disable=broad-exception-caught
# pylint: disable=too-few-public-methods
# pylint: disable=unnecessary-lambda
import os
from shutil import rmtree, copyfile
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import (
    QApplication,
    QListWidgetItem,
    QMessageBox,
)

from utils.wad import (
    flip_texture,
    rotate_texture,
    defullbright,
)


class EditMixin:
    def undo_redo(self, redo=False):
        try:
            if redo:
                self.history.redo()
            else:
                self.history.undo()

            self.set_list_state()
        except Exception as e:
            print(f"[undo_redo] {e}")

    def cut_copy_item(self, is_cut):
        try:
            clipboard = QApplication.clipboard()
            mime_data = QtCore.QMimeData()
            image_paths = []

            selected_items = self.lw_textures.selectedItems()

            rmtree(self.clipboard_temp_dir)
            os.makedirs(self.clipboard_temp_dir, exist_ok=True)

            for item in selected_items:
                image_paths.append(item.data(QtCore.Qt.UserRole))

            if image_paths:
                # Initialize an empty list to hold all URLs
                urls_to_copy = []
                for image_path in image_paths:
                    # Move the image to the clipboard folder
                    new_path = os.path.join(
                        self.clipboard_temp_dir, os.path.basename(image_path)
                    )
                    copyfile(image_path, new_path)

                    # Add the new path as a URL to the urls_to_copy list
                    urls_to_copy.append(QtCore.QUrl.fromLocalFile(new_path))

                # Set all collected URLs to the clipboard at once
                mime_data.setUrls(urls_to_copy)
                clipboard.setMimeData(mime_data)

                if is_cut:
                    for item in selected_items:
                        self.lw_textures.takeItem(self.lw_textures.row(item))
                        os.remove(item.data(QtCore.Qt.UserRole))

                    self.history.new_change(self.get_list_state())

        except Exception as e:
            print(f"[cut_copy_item] {e}")

    def paste_item(self):
        try:
            clipboard = QApplication.clipboard()
            mime_data = clipboard.mimeData()

            # paste those images where you just copy directly from a page or whatever
            if mime_data.hasImage():
                image_data = mime_data.data("image/png")

                pixmap = QtGui.QPixmap()
                pixmap.loadFromData(image_data, "PNG")

                pasted_dir = os.path.join(self.temp_dir, "pasted")
                os.makedirs(pasted_dir, exist_ok=True)
                temp_file_path = os.path.join(pasted_dir, "pasted_image.png")
                pixmap.save(temp_file_path, "PNG")

                self.import_image([temp_file_path])

            # paste local images
            elif mime_data.hasUrls():
                file_paths = [url.toLocalFile() for url in mime_data.urls()]

                image_paths = [
                    path
                    for path in file_paths
                    if path.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp"))
                ]

                self.import_image(image_paths)

        except Exception as e:
            print(f"[paste_item] Error: {e}")

    def delete_textures(self):
        try:
            print("we deleting stuff")
            textures = self.lw_textures.selectedItems()
            for t in textures:
                self.lw_textures.takeItem(self.lw_textures.row(t))
                os.remove(t.data(QtCore.Qt.UserRole))

            self.history.new_change(self.get_list_state())
        except Exception as e:
            print(f"[delete_textures] {e}")

    def de_select_all(self, toggle):
        try:
            for i in range(self.lw_textures.count()):
                self.lw_textures.item(i).setSelected(toggle)
        except Exception as e:
            print(f"[de_select_all] {e}")

    def sort_textures(self, descending=False):
        try:
            sort_order = QtCore.Qt.AscendingOrder

            if descending:
                sort_order = QtCore.Qt.DescendingOrder

            self.lw_textures.sortItems(sort_order)

            self.history.new_change(self.get_list_state())
        except Exception as e:
            print(f"[sort_textures] {e}")

    def rotate_texture(self, to_right):
        try:
            selected_items = self.lw_textures.selectedItems()

            if len(selected_items) < 1:
                print("nothing is selected buckoo")
                return

            for item in selected_items:
                icon_path = item.data(QtCore.Qt.UserRole)

                if to_right:  # rotate to right
                    rotate_texture(icon_path, True)
                else:  # to left
                    rotate_texture(icon_path, False)

                original_pixmap = QtGui.QPixmap(icon_path)
                scaled_pixmap = original_pixmap.scaled(
                    self.texture_size, self.texture_size, QtCore.Qt.KeepAspectRatio
                )

                item.setIcon(QtGui.QIcon(scaled_pixmap))
                item.setData(QtCore.Qt.UserRole, icon_path)

            self.history.new_change(self.get_list_state())
        except Exception as e:
            print(f"[rotate_texture] {e}")

    def defullbright_textures(self):

        try:
            textures = []

            for i in self.lw_textures.selectedItems():
                textures.append(i.data(QtCore.Qt.UserRole))

            dfb_textures = defullbright(textures)

            for t in dfb_textures:
                filename = os.path.splitext(os.path.basename(t))[0]

                scaled_pixmap = QtGui.QPixmap(t).scaled(
                    self.texture_size, self.texture_size, QtCore.Qt.KeepAspectRatio
                )

                scaled_icon = QtGui.QIcon(scaled_pixmap)
                item = QListWidgetItem(scaled_icon, filename)

                item.setData(QtCore.Qt.UserRole, t)  # icon path

                self.lw_textures.addItem(item)

            self.history.new_change(self.get_list_state())
        except Exception as e:
            print(f"[defullbright_textures] {e}")

    def rename_texture(self):
        try:
            selected_items = self.lw_textures.selectedItems()

            if len(selected_items) != 1:
                print("can't rename 0 or more than 1 files")
                QMessageBox.warning(
                    self, "Qthon Error", "Can't rename multiple or no textures."
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
                        self, "Qthon Error", "Texture with this name already exists."
                    )
                    return

                os.rename(item["path"], f"{self.temp_dir}/{new_name}.png")

                selected_items[0].setText(new_name)
                selected_items[0].setData(
                    QtCore.Qt.UserRole, f"{self.temp_dir}/{new_name}.png"
                )
                self.history.new_change(self.get_list_state())
        except Exception as e:
            print(f"[rename_texture] {e}")

    def resize_texture(self):
        try:
            selected_items = self.lw_textures.selectedItems()
            textures = []

            if len(selected_items) < 1:
                print("can't resize 0 files")
                QMessageBox.warning(
                    self, "Qthon Error", "No textures selected for resizing"
                )
                return

            for i in selected_items:
                textures.append({"title": i.text(), "path": i.data(QtCore.Qt.UserRole)})

            resize_win = ResizeWindow(textures)

            if resize_win.exec_():
                print("do sth post texture(s) resizing idk")
                self.history.new_change(self.get_list_state())
                self.set_list_state()
        except Exception as e:
            print(f"[resize_texture] {e}")

    def flip_texture(self, mirror=False):
        try:
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
        except Exception as e:
            print(f"[flip_texture] {e}")
