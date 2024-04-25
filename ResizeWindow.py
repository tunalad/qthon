from PIL import Image

from PyQt5 import uic
from PyQt5.QtWidgets import (
    QDialog,
)


class ResizeWindow(QDialog):
    def __init__(self, textures):
        super().__init__()
        uic.loadUi("ui/resize.ui", self)

        self.textures = textures
        self.x, self.y = Image.open(textures[0]["path"]).size
        self.sb_X.setValue(self.x)
        self.sb_Y.setValue(self.y)

        self.sb_X.lineEdit().setReadOnly(True)
        self.sb_Y.lineEdit().setReadOnly(True)

        self.sb_X.valueChanged.connect(lambda: self.spinbox_constrain())
        self.sb_Y.valueChanged.connect(lambda: self.spinbox_constrain())

        self.buttonBox.accepted.connect(lambda: self.ok_clicked())
        self.buttonBox.rejected.connect(lambda: self.reject())

    def spinbox_constrain(self):
        if self.cb_constrain.isChecked():
            sender = self.sender()
            other_spinbox = self.sb_X if sender == self.sb_Y else self.sb_Y
            other_spinbox.setValue(sender.value())

    def ok_clicked(self):
        for t in self.textures:
            img = Image.open(t["path"])
            resized = img.resize((self.sb_X.value(), self.sb_Y.value()))

            resized.save(t["path"])

        self.accept()
