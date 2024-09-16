# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=unnecessary-lambda
# pylint: disable=invalid-name
import toml

from PyQt5 import uic
from PyQt5.QtWidgets import (
    QDialog,
)

from utils import path


class PreferencesWindow(QDialog):
    def __init__(self, settings):
        super().__init__()
        uic.loadUi(path("assets", "ui", "preferences.ui"), self)

        self.settings = settings
        self.cfg = self.settings.parsed_cfg

        self.load_settings(self.cfg)

        self.buttonBox.accepted.connect(lambda: self.ok_clicked())
        self.buttonBox.rejected.connect(lambda: self.reject())

    def apply_settings(self, cfg):
        cfg["default_zoom"] = self.sb_zoom.value()
        cfg["water_port"] = self.sb_waterPort.value()
        cfg["undo_limit"] = self.sb_undoStack.value()

        cfg["hide_item"]["toolbar"] = self.cb_hide_toolbar.isChecked()
        cfg["hide_item"]["sidebar"] = self.cb_hide_sidebar.isChecked()
        cfg["hide_item"]["statusbar"] = self.cb_hide_statusbar.isChecked()

        cfg["move_item"]["toolbar"] = self.cb_move_toolbar.isChecked()
        cfg["move_item"]["sidebar"] = self.cb_move_sidebar.isChecked()

        with open(self.settings.config_path, "w") as f:
            toml.dump(self.cfg, f)

    def load_settings(self, cfg):
        self.sb_zoom.setValue(cfg["default_zoom"])
        self.sb_waterPort.setValue(cfg["water_port"])
        self.sb_undoStack.setValue(cfg["undo_limit"])

        self.cb_hide_sidebar.setChecked(cfg["hide_item"]["sidebar"])
        self.cb_hide_toolbar.setChecked(cfg["hide_item"]["toolbar"])
        self.cb_hide_statusbar.setChecked(cfg["hide_item"]["statusbar"])

        self.cb_move_toolbar.setChecked(cfg["move_item"]["toolbar"])
        self.cb_move_sidebar.setChecked(cfg["move_item"]["sidebar"])

    def ok_clicked(self):
        self.apply_settings(self.cfg)
        self.accept()
