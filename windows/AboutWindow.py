# pylint: disable=invalid-name
# pylint: disable=too-few-public-methods
# pylint: disable=missing-class-docstring
# pylint: disable=missing-module-docstring
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog

from utils import path


class AboutWindow(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi(path("assets", "ui", "about.ui"), self)
