from PyQt5 import uic
from PyQt5.QtWidgets import (
    QDialog,
)


class AboutWindow(QDialog):
    def __init__(self):
        super(AboutWindow, self).__init__()
        uic.loadUi("ui/about.ui", self)
