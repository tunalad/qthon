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
import assets.ui.resource_ui
from shutil import rmtree
from appdirs import user_data_dir
from PyQt5 import uic, QtGui, QtCore
from PyQt5.QtWidgets import (
    QMainWindow,
    QApplication,
    QListWidgetItem,
    QLineEdit,
    QWidget,
    QSizePolicy,
    QMenu,
)

from utils import history, settings
from utils.wad import (
    get_texture_size,
)
from menus.file import FileMixin
from menus.edit import EditMixin
from menus.view import ViewMixin

from AboutWindow import AboutWindow


class MainWindow(QMainWindow, FileMixin, EditMixin, ViewMixin):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi("assets/ui/main.ui", self)

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
        self.clipboard_temp_dir = tempfile.mkdtemp(prefix="tmp-qtwaditor-clipboard-")

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
                # self.actionHelp,
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
            self.actionRotate_Left,
            self.actionRotate_Right,
        ]

        # first, we disable them
        self.disable_actions(togglable_actions)
        self.disable_actions(togglable_actions_lto)

        # CONNECTIONS
        ## trigger
        self.actionAbout.triggered.connect(lambda: AboutWindow().exec_())
        self.actionHelp.triggered.connect(
            lambda: QtGui.QDesktopServices.openUrl(
                QtCore.QUrl("https://tunalad.github.io/projects/qthon/")
            )
        )
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
        self.actionRotate_Left.triggered.connect(
            lambda: self.rotate_texture(to_right=False)
        )
        self.actionRotate_Right.triggered.connect(
            lambda: self.rotate_texture(to_right=True)
        )

        self.action_Ascending.triggered.connect(lambda: self.sort_textures(False))
        self.action_Descending.triggered.connect(lambda: self.sort_textures(True))

        self.actionUndo.triggered.connect(lambda: self.undo_redo(False))
        self.actionRedo.triggered.connect(lambda: self.undo_redo(True))

        self.actionSave.triggered.connect(lambda: self.save_wad())
        self.actionSave_As.triggered.connect(lambda: self.save_wad(save_as=True))
        self.actionSave_Selections_As.triggered.connect(
            lambda: self.save_wad(save_as=True, selected_only=True)
        )
        self.actionExport_Images.triggered.connect(
            lambda: self.save_wad(export_images=True)
        )
        self.actionExport_Selected_Images.triggered.connect(
            lambda: self.save_wad(selected_only=True, export_images=True)
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

        self.lw_textures.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.lw_textures.customContextMenuRequested.connect(
            lambda pos: self.right_click_menu(pos)
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

        # toggle statusbar info
        self.lw_textures.itemSelectionChanged.connect(lambda: self.statusbar_text())

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
            rmtree(self.clipboard_temp_dir)
        except Exception as e:
            print(f"[closeEvent] {e}")
        finally:
            event.accept()

    # # # # # # # # # # # #
    # FUNCTIONS
    # # # # # # # # # # # #

    def right_click_menu(self, position):
        global_position = self.lw_textures.viewport().mapToGlobal(position)

        menu = self.findChild(QMenu, "menuEdit")

        if menu:
            menu.exec_(global_position)

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

    def statusbar_text(self):
        try:
            selected_items = self.lw_textures.selectedItems()

            if len(selected_items) < 1:
                self.statusbar.clearMessage()
                return

            if len(selected_items) > 1:
                self.statusbar.showMessage(
                    f"Selected items: {len(selected_items)}/{self.lw_textures.count()}"
                )
            else:
                texture = selected_items[0]
                self.statusbar.showMessage(
                    f"{texture.text()} | {get_texture_size(texture.data(QtCore.Qt.UserRole))}"
                )
        except Exception as e:
            print(f"[statusbar_text] {e}")

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
