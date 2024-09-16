from PyQt5 import uic
from PyQt5.QtWidgets import (
    QDialog,
)

from utils import path


class AboutWindow(QDialog):
    def __init__(self):
        super(AboutWindow, self).__init__()
        uic.loadUi(path("assets", "ui", "about.iu"), self)
