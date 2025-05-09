# pylint: disable=missing-module-docstring
# pylint: disable=multiple-imports

from logging import error

from PyQt5 import QtCore
from PyQt5.QtWidgets import (
    QMessageBox,
)


from windows.PreviewWindow import PreviewWindow
from windows.WaterWindow import LiquidPreview
from windows.PreferencesWindow import PreferencesWindow


class ViewMixin:
    """
    Mixin class providing visual/view-related functionality for the application.
    """

    def bars_manager(self, widget, action, movable_action=None):
        """
        Manages visibility and movability of toolbar widgets.

        Args:
            widget: Widget to manage (toolbar, statusbar, etc.).
            action: Action that toggles widget visibility.
            movable_action (optional): Action that toggles widget movability.
        """
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
            error(f"[bars_manager] {e}")

    def preview_texture(self, animation=False):
        """
        Opens preview window for selected texture.

        Args:
            animation (bool): If True, enables animation preview for liquid textures.
        """
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
            error(f"[preview_texture] {e}")

    def preferences_handling(self):
        """
        Opens preferences window and applies changes to UI configuration.
        """
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
            error(f"[preferences_handling] {e}")
