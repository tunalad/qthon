from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel
from PyQt5.QtGui import QPixmap, QImage
from PIL import Image


class PreviewWindow(QDialog):
    def __init__(self, texture, scale=1):
        super().__init__()
        self.setWindowTitle("Preview texture - QtWADitor")

        layout = QVBoxLayout()

        # mipmap
        mipmaps = self.generate_mipmaps(texture, scale)
        for mipmap_texture in mipmaps:
            mipmap_label = QLabel()
            mipmap_label.setPixmap(mipmap_texture)
            layout.addWidget(mipmap_label)

        # animated preview

        # water preview

        self.setLayout(layout)

    def generate_mipmaps(self, texture, scale):
        mipmaps = []

        img = Image.open(texture)

        for i in range(4):
            resized_image = img.resize(
                (img.width // pow(2, i) * scale, img.height // pow(2, i) * scale)
            )
            resized_image = resized_image.convert("RGBA")  # Convert to RGBA format
            qimage = QImage(
                resized_image.tobytes(),
                resized_image.width,
                resized_image.height,
                QImage.Format_RGBA8888,
            )
            pixmap = QPixmap(qimage)  # Convert QImage to QPixmap
            mipmaps.append(pixmap)

        return mipmaps
