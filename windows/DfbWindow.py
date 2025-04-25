# pylint: disable=invalid-name
# pylint: disable=too-few-public-methods
# pylint: disable=missing-class-docstring
# pylint: disable=missing-module-docstring
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog

from utils import path, settings


class DfbWindow(QDialog):
    def __init__(self):
        super().__init__()

        uic.loadUi(path("assets", "ui", "dfb-prompt.ui"), self)

        self.cfg = settings.Config().parsed_cfg

        self.cb_ask.setChecked(self.cfg["defullbright"]["show_prompt"])
        self.rb_replace.setChecked(self.cfg["defullbright"]["overwrite"])
        self.rb_duplicate.setChecked(not self.cfg["defullbright"]["overwrite"])

        self.buttonBox.accepted.connect(lambda: self.ok_clicked())
        self.buttonBox.rejected.connect(lambda: self.reject())

    def ok_clicked(self):
        self.cfg["defullbright"]["show_prompt"] = self.cb_ask.isChecked()
        self.cfg["defullbright"]["overwrite"] = self.rb_replace.isChecked()

        settings.Config().update_config(self.cfg)
        settings.Config().load_config(settings.Config().config_path)

        self.accept()
