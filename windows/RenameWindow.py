# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=unnecessary-lambda
# pylint: disable=invalid-name
from PyQt5 import uic
from PyQt5.QtWidgets import (
    QDialog,
)

from utils import path


class RenameWindow(QDialog):
    def __init__(self, texture_title, texture_path):
        super(RenameWindow, self).__init__()
        uic.loadUi(path("assets", "ui", "rename.ui"), self)
        # yes, I'd rather create a whole .ui file than code out 2 items widget

        self.title = texture_title
        self.path = texture_path

        self.lineEdit.setText(self.title)

        self.buttonBox.accepted.connect(lambda: self.ok_clicked())
        self.buttonBox.rejected.connect(lambda: self.reject())

    def ok_clicked(self):
        self.new_name = self.lineEdit.text()
        self.accept()

    def get_new_name(self):
        return self.new_name
