# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=redefined-outer-name
# pylint: disable=multiple-imports
# pylint: disable=missing-class-docstring
# pylint: disable=broad-exception-caught
# pylint: disable=too-few-public-methods
# pylint: disable=unnecessary-lambda

import os, tempfile
from shutil import rmtree, copyfile
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import (
    QListWidgetItem,
    QFileDialog,
    QMessageBox,
    QAction,
)

from utils.wad import (
    unwad,
    wadup,
    import_texture,
)


class FileMixin:
    def new_wad(self):
        try:
            if self.temp_dir:
                rmtree(self.temp_dir)
                self.lw_textures.clear()

            self.temp_dir = tempfile.mkdtemp(prefix="tmp-qtwaditor-")
            self.history.set_temp_dir(self.temp_dir)
            self.history.new_change(self.get_list_state())  # empty snap

            self.wad_path = None
        except Exception as e:
            print(f"[new_wad] {e}")

    def open_recent(self, new_path=None):
        try:
            recent_files = os.path.join(self.user_data_dir, "recent_files")

            self.menuOpen_Recent.clear()

            # remove line if it's already in the list
            with open(recent_files, "r+") as file:
                lines = file.readlines()
                file.seek(0)
                file.truncate()
                for line in lines:
                    if line.strip("\n") != new_path:
                        file.write(line)

            # add new path to list
            if new_path:
                with open(recent_files, "a") as file:
                    file.write(new_path + "\n")

            # create menu items
            if os.path.exists(recent_files):
                # trim so we don't have > 10
                with open(recent_files, "r+") as file:
                    lines = file.readlines()
                    if len(lines) > 10:
                        file.seek(0)
                        file.truncate()
                        file.writelines(lines[-10:])

                # create menu items
                with open(recent_files, "r") as file:
                    paths = reversed(file.readlines())

                    for p in paths:
                        p = p.strip()
                        if os.path.exists(p) and os.path.isfile(p):
                            action = QAction(p, self)
                            action.triggered.connect(
                                lambda checked, path=p: self.open_wad(path)
                            )
                            self.menuOpen_Recent.addAction(action)

                self.menuOpen_Recent.setEnabled(len(self.menuOpen_Recent.actions()) > 0)
        except Exception as e:
            print(f"[open_recent] {e}")

    def open_wad(self, wad_path=None):
        try:
            if not wad_path:
                self.wad_path, _ = QFileDialog.getOpenFileName(
                    self, "Select a WAD file", "", "WAD Files (*.wad);;All Files (*)"
                )
            else:
                self.wad_path = wad_path

            if not self.wad_path:
                return

            if self.temp_dir:
                rmtree(self.temp_dir)

            self.temp_dir = tempfile.mkdtemp(prefix="tmp-qtwaditor-")
            self.history.set_temp_dir(self.temp_dir)
            self.history.reset_state()

            self.lw_textures.clear()
            self.import_wad([self.wad_path])
            self.save_pos = self.history.position

            self.open_recent(self.wad_path)
        except Exception as e:
            print(f"[open_wad] {e}")

    def import_wad(self, wad_paths):
        try:
            if len(wad_paths) < 1:
                return

            for wad in wad_paths:
                self.unpack_wad(wad)

            self.history.new_change(self.get_list_state())
        except Exception as e:
            print(f"[import_wad] {e}")

    def import_image(self, images):
        try:
            textures = import_texture(images, self.temp_dir)
            # __import__('pprint').pprint(imported_textures)

            if len(textures) < 1:
                return

            for t in textures:
                scaled_pixmap = QtGui.QPixmap(t).scaled(
                    self.texture_size, self.texture_size, QtCore.Qt.KeepAspectRatio
                )

                scaled_icon = QtGui.QIcon(scaled_pixmap)
                item = QListWidgetItem(
                    scaled_icon, os.path.splitext(os.path.basename(t))[0]
                )

                item.setData(QtCore.Qt.UserRole, t)  # icon path

                self.lw_textures.addItem(item)

            self.history.new_change(self.get_list_state())
        except Exception as e:
            print(f"[import_image] {e}")

    def import_wads_images(self, dropped_files=None):
        try:
            if dropped_files:
                import_paths = dropped_files
            else:
                import_paths, _ = QFileDialog.getOpenFileNames(
                    self,
                    "Import file(s)",
                    "",
                    "WAD Files (*.wad);;Images (*.png *.jpg *.jpeg);;All files (*)",
                )

            wad_paths = []
            image_paths = []
            extra_paths = []

            for path in import_paths:
                if path.lower().endswith(".wad"):
                    wad_paths.append(path)
                elif path.lower().endswith((".png", ".jpg", ".jpeg")):
                    image_paths.append(path)
                else:
                    extra_paths.append(path)

            self.import_wad(wad_paths)
            self.import_image(image_paths)

            if len(extra_paths) > 0:
                QMessageBox.warning(
                    self,
                    "Qthon Warning",
                    f"Some files selected can't be imported:\n    - {'\n    - '.join(os.path.basename(p) for p in extra_paths)}",
                )
        except Exception as e:
            print(f"[import_wads_images] {e}")

    def save_wad(self, save_as=False, selected_only=False, export_images=False):
        try:
            export_path = None

            if not self.wad_path or save_as:
                self.wad_path, _ = QFileDialog.getSaveFileName(
                    self, "Save WAD file", "", "WAD Files (*.wad);;All Files (*)"
                )
            elif export_images:
                export_path = QFileDialog.getExistingDirectory(
                    self, "Select export directory"
                )

            if self.wad_path:
                # show items
                textures_list = []
                if selected_only:
                    for t in self.lw_textures.selectedItems():
                        textures_list.append(t.data(QtCore.Qt.UserRole))
                else:
                    for t in range(self.lw_textures.count()):
                        item = self.lw_textures.item(t)
                        textures_list.append(item.data(QtCore.Qt.UserRole))

                if export_images:
                    for t in textures_list:
                        file_name = os.path.basename(t)
                        destination_path = os.path.join(export_path, file_name)
                        copyfile(t, destination_path)
                else:
                    wadup(textures_list, self.wad_path)

                self.save_pos = self.history.position

        except Exception as e:
            print(f"[save_wad] {e}")

    def unpack_wad(self, path):
        try:
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
        except Exception as e:
            print(f"[unpack_wad] {e}")
