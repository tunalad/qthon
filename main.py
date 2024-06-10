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
from appdirs import user_data_dir
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
    QLineEdit,
    QWidget,
    QSpacerItem,
    QSizePolicy,
)

from RenameWindow import RenameWindow
from ResizeWindow import ResizeWindow
from AboutWindow import AboutWindow
from PreviewWindow import PreviewWindow
from WaterWindow import LiquidPreview
from PreferencesWindow import PreferencesWindow

import history, settings
from wad import unwad, wadup, flip_texture, import_texture, defullbright


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi("ui/main.ui", self)

        self.setAcceptDrops(True)

        self.wad_path = None
        self.texture_size = 128
        self.texture_spacing = 17
        self.undo_limit = 0  # 0 means no limit
        self.water_port = 9742
        self.history = None
        self.settings = settings.Config()
        self.temp_dir = None
        self.save_pos = None
        self.user_data_dir = user_data_dir("qthon")

        # make data dir & it's file if tey don't exist
        if not os.path.exists(self.user_data_dir):
            os.makedirs(self.user_data_dir)
        with open(os.path.join(self.user_data_dir, "recent_files"), "a") as file:
            pass

        self.load_config()
        self.history = history.History(self.undo_limit)

        self.new_wad()
        self.set_search()

        self.show()

        #####################################
        # disabling some actions (for now)
        self.disable_actions(
            [
                # self.action,
                # HELP
                self.actionHelp,
            ],
            True,
        )
        #####################################

        # TOGGLABLE ITEMS
        togglable_actions = [  # EXACTLY 1 selection
            self.actionRename,
            self.actionResize,
        ]

        togglable_actions_lto = [  # LESS than 1 item
            self.actionMirror,
            self.actionFlip,
            self.actionCut,
            self.actionCopy,
            self.actionDelete,
            self.actionDefullbright,
        ]

        # first, we disable them
        self.disable_actions(togglable_actions)
        self.disable_actions(togglable_actions_lto)

        # CONNECTIONS
        ## trigger
        self.actionAbout.triggered.connect(lambda: AboutWindow().exec_())
        self.actionPreferences.triggered.connect(lambda: self.preferences_handling())
        self.actionQuit.triggered.connect(lambda: self.close())

        self.actionOpen.triggered.connect(lambda: self.open_wad())
        self.actionImport.triggered.connect(lambda: self.import_wads_images())
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
        self.actionDefullbright.triggered.connect(lambda: self.defullbright_textures())

        self.action_Ascending.triggered.connect(lambda: self.sort_textures(False))
        self.action_Descending.triggered.connect(lambda: self.sort_textures(True))

        self.actionUndo.triggered.connect(lambda: self.undo_redo(False))
        self.actionRedo.triggered.connect(lambda: self.undo_redo(True))

        self.actionSave.triggered.connect(lambda: self.save_wad())
        self.actionSave_As.triggered.connect(lambda: self.save_wad(save_as=True))
        self.actionSave_Selections_As.triggered.connect(
            lambda: self.save_wad(save_as=True, selected_only=True)
        )

        self.actionView_Detailed.triggered.connect(lambda: self.preview_texture())
        self.actionView_Animated.triggered.connect(lambda: self.preview_texture(True))

        self.actionHide_toolbar.triggered.connect(
            lambda: self.update_cfg_item(
                ["hide_item", "toolbar"], self.actionHide_toolbar.isChecked()
            )
        )
        self.actionHide_sidebar.triggered.connect(
            lambda: self.update_cfg_item(
                ["hide_item", "sidebar"], self.actionHide_sidebar.isChecked()
            )
        )
        self.actionHide_statusbar.triggered.connect(
            lambda: self.update_cfg_item(
                ["hide_item", "statusbar"], self.actionHide_statusbar.isChecked()
            )
        )

        self.actionMovable_toolbar.triggered.connect(
            lambda: self.update_cfg_item(
                ["move_item", "toolbar"], self.actionMovable_toolbar.isChecked()
            )
        )
        self.actionMovable_sidebar.triggered.connect(
            lambda: self.update_cfg_item(
                ["move_item", "sidebar"], self.actionMovable_sidebar.isChecked()
            )
        )

        self.open_recent()

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

        self.history.position_callback = self.title_management

    # # # # # # # # # # # #
    # PROPERTIES
    # # # # # # # # # # # #

    @property
    def save_pos(self):
        """The save_pos property."""
        return self._save_pos

    @save_pos.setter
    def save_pos(self, value):
        self._save_pos = value
        self.title_management()

    # # # # # # # # # # # #
    # EVENTS
    # # # # # # # # # # # #

    def dragEnterEvent(self, event):
        try:
            if event.mimeData().hasUrls():
                event.accept()
                self.lw_textures.setStyleSheet("background-color: rgb(131, 131, 131);")
            else:
                event.ignore()
        except Exception as e:
            print(f"[dragEnterEvent] {e}")

    def dragLeaveEvent(self):
        try:
            self.lw_textures.setStyleSheet("background-color: rgb(171, 171, 171);")
        except Exception as e:
            print(f"[dragLeaveEvent] {e}")

    def dropEvent(self, event):
        try:
            files = [url.toLocalFile() for url in event.mimeData().urls()]
            self.import_wads_images(dropped_files=files)
            self.lw_textures.setStyleSheet("background-color: rgb(171, 171, 171);")
        except Exception as e:
            print(f"[dropEvent] {e}")

    def closeEvent(self, event):
        try:
            rmtree(self.temp_dir)
        except Exception as e:
            print(f"[closeEvent] {e}")
        finally:
            event.accept()

    # # # # # # # # # # # #
    # FUNCTIONS
    # # # # # # # # # # # #

    def preferences_handling(self):
        try:
            PreferencesWindow(settings=self.settings).exec_()
            self.load_config()
            self.bars_manager(self.statusbar, self.actionHide_statusbar)
            self.bars_manager(
                self.tb_options, self.actionHide_toolbar, self.actionMovable_toolbar
            )
            self.bars_manager(
                self.tb_editor, self.actionHide_sidebar, self.actionMovable_sidebar
            )
        except Exception as e:
            print(f"[preferences_handling] {e}")

    def load_config(self):
        try:
            cfg = self.settings.parsed_cfg

            self.texture_size = cfg["default_zoom"]
            self.undo_limit = cfg["undo_limit"]
            self.water_port = cfg["water_port"]

            self.actionHide_statusbar.setChecked(cfg["hide_item"]["statusbar"])
            self.actionHide_toolbar.setChecked(cfg["hide_item"]["toolbar"])
            self.actionHide_sidebar.setChecked(cfg["hide_item"]["sidebar"])

            self.actionMovable_toolbar.setChecked(cfg["move_item"]["toolbar"])
            self.actionMovable_sidebar.setChecked(cfg["move_item"]["sidebar"])
        except Exception as e:
            print(f"[load_config] {e}")

    def update_cfg_item(self, keys, value):
        try:
            config = self.settings.parsed_cfg
            for key in keys[:-1]:
                config = config[key]
            config[keys[-1]] = value
            self.settings.update_config(self.settings.parsed_cfg)
        except Exception as e:
            print(f"[update_cfg_item] {e}")

    def set_search(self):
        try:
            self.search_bar = QLineEdit(self.tb_options)
            self.search_bar.setPlaceholderText("Search...")
            self.search_bar.setMaximumWidth(250)
            self.search_bar.setMinimumWidth(30)

            self.search_bar.setClearButtonEnabled(True)

            spacer = QWidget(self.tb_options)
            spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

            self.tb_options.addWidget(spacer)
            self.tb_options.addWidget(self.search_bar)

            self.search_bar.textChanged.connect(self.fzf_textures)
        except Exception as e:
            print(f"[set_search] {e}")

    def fzf_textures(self):
        try:
            search_text = self.search_bar.text().lower()
            for index in range(self.lw_textures.count()):
                item = self.lw_textures.item(index)
                item_text = item.text().lower()
                item.setHidden(search_text not in item_text)
        except Exception as e:
            print(f"[fzf_textures] {e}")

    def title_management(self):
        try:
            if not self.wad_path:
                self.setWindowTitle("Untitled* - Qthon")
            elif self.wad_path and (self.save_pos != self.history.position):
                self.setWindowTitle(f"{os.path.basename(self.wad_path)}* - Qthon")
            else:
                self.setWindowTitle(f"{os.path.basename(self.wad_path)} - Qthon")
        except Exception as e:
            print(f"[title_management] {e}")

    def bars_manager(self, widget, action, movable_action=None):
        try:
            if action:
                widget.setVisible(not action.isChecked())
                action.triggered.connect(
                    lambda: widget.setVisible(not action.isChecked())
                )
            else:
                print(f"can't find action: {widget.objectName()}")

            if movable_action:
                widget.setMovable(movable_action.isChecked())
                movable_action.setChecked(widget.isMovable())
                movable_action.triggered.connect(
                    lambda: widget.setMovable(movable_action.isChecked())
                )
        except Exception as e:
            print(f"[bars_manager] {e}")

    def adjust_zoom(self, zoom_type):
        try:
            if zoom_type == "in" and self.texture_size < 128:
                self.texture_size += 16
            elif zoom_type == "out" and self.texture_size > 16:
                self.texture_size -= 16
            else:
                return

            self.lw_textures.setIconSize(
                QtCore.QSize(self.texture_size, self.texture_size)
            )
        except Exception as e:
            print(f"[adjust_zoom] {e}")

    def preview_texture(self, animation=False):
        try:
            selected_items = self.lw_textures.selectedItems()

            if len(selected_items) != 1:
                print("can't preview 0 or more than 1 textures")
                QMessageBox.warning(
                    self, "Qthon Error", "Can't preview multiple or no textures."
                )
                return

            item = {
                "title": selected_items[0].text(),
                "path": selected_items[0].data(QtCore.Qt.UserRole),
            }
            if os.path.basename(item["path"]).startswith("*") and animation:
                LiquidPreview(texture=item["path"], port=9742).exec()
            else:
                PreviewWindow(item["path"], 200, animation).exec_()
        except Exception as e:
            print(f"[preview_texture] {e}")

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

    def save_wad(self, save_as=False, selected_only=False):
        try:
            if not self.wad_path or save_as:
                self.wad_path, _ = QFileDialog.getSaveFileName(
                    self, "Save WAD file", "", "WAD Files (*.wad);;All Files (*)"
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

    def disable_actions(self, actions, not_implemented=False):
        try:
            for a in actions:
                tooltip = a.toolTip()

                if not_implemented:
                    tooltip += " [NOT IMPLEMENTED]"

                a.setToolTip(tooltip)
                a.setEnabled(False)
        except Exception as e:
            print(f"[disable_actions] {e}")

    def disable_previews(self):
        try:
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
        except Exception as e:
            print(f"[disable_previews] {e}")

    def sort_textures(self, descending=False):
        try:
            sort_order = QtCore.Qt.AscendingOrder

            if descending:
                sort_order = QtCore.Qt.DescendingOrder

            self.lw_textures.sortItems(sort_order)

            self.history.new_change(self.get_list_state())
        except Exception as e:
            print(f"[sort_textures] {e}")

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

    def de_select_all(self, toggle):
        try:
            for i in range(self.lw_textures.count()):
                self.lw_textures.item(i).setSelected(toggle)
        except Exception as e:
            print(f"[de_select_all] {e}")

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

    def cut_copy_item(self, is_cut):
        try:
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
        except Exception as e:
            print(f"[copy_item] {e}")

    def paste_item(self):
        try:
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

                    existing_textures = [
                        item["title"] for item in self.get_list_state()
                    ]

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
                            self.texture_size,
                            self.texture_size,
                            QtCore.Qt.KeepAspectRatio,
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
        except Exception as e:
            print(f"[paste_item] {e}")

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
        try:
            for a in actions:
                if not multi and len(self.lw_textures.selectedItems()) == 1:
                    a.setEnabled(True)
                elif multi and len(self.lw_textures.selectedItems()) > 0:
                    a.setEnabled(True)
                else:
                    a.setEnabled(False)
        except Exception as e:
            print(f"[active_on_selection] {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    UIWindow = MainWindow()
    app.exec_()
