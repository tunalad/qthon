import os, sys

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QMessageBox
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import QTimer
from PIL import Image


class PreviewWindow(QDialog):
    def __init__(self, texture, scale=1, animated=False):
        super().__init__()
        self.setWindowTitle("Preview texture - QtWADitor")

        layout = QVBoxLayout()

        filename = os.path.basename(texture)

        if filename.startswith("+") and animated:
            # animation textures
            self.frame_index = 0
            self.frames = self.load_animation_frames(texture, scale)

            self.animation_label = QLabel()
            layout.addWidget(self.animation_label)

            self.timer = QTimer(self)
            self.timer.timeout.connect(self.update_frame)
            self.timer.start(250)  # animation speed
        else:
            # mipmap
            mipmaps = self.generate_mipmaps(texture, scale)
            for mipmap_texture in mipmaps:
                mipmap_label = QLabel()
                mipmap_label.setPixmap(mipmap_texture)
                layout.addWidget(mipmap_label)

        self.setLayout(layout)

    # MIPMAP
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

    # ANIMATION
    def load_animation_frames(self, texture_path, scale):
        frames = []

        temp_dir = os.path.dirname(texture_path)
        frames_name = os.path.basename(texture_path)

        # find other frames
        animation_paths = []
        for filename in os.listdir(temp_dir):
            if (
                len(filename) == len(frames_name)
                and filename[1] != frames_name[1]
                and all(
                    filename[i] == frames_name[i]
                    for i in range(len(frames_name))
                    if i != 1
                )
            ):
                animation_paths.append(os.path.join(temp_dir, filename))

        # sort them
        animation_paths.sort()

        # load them & scale
        for frame_path in animation_paths:
            img = Image.open(frame_path)
            resized_image = img.resize(
                (img.width * scale // 2, img.height * scale // 2)
            )
            resized_image = resized_image.convert("RGBA")
            qimage = QImage(
                resized_image.tobytes(),
                resized_image.width,
                resized_image.height,
                QImage.Format_RGBA8888,
            )
            pixmap = QPixmap(qimage)
            frames.append(pixmap)

        return frames

    def update_frame(self):
        if self.frame_index < len(self.frames):
            pixmap = self.frames[self.frame_index]
            self.animation_label.setPixmap(pixmap)
            self.frame_index += 1
        else:
            self.frame_index = 0
