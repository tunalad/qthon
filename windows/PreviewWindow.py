# pylint: disable=invalid-name
# pylint: disable=too-few-public-methods
# pylint: disable=missing-class-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=too-many-locals
import os

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import QTimer, Qt
from PIL import Image


class PreviewWindow(QDialog):
    def __init__(self, texture, max_dimension=100, animated=False):
        super().__init__()
        self.setWindowTitle("Preview texture - Qthon")
        self.setMinimumSize(500, 300)
        layout = QVBoxLayout()

        filename = os.path.basename(texture)

        if filename.startswith("+") and animated:
            # animation textures
            self.frame_index = 0
            self.frames = self.load_animation_frames(texture, max_dimension)

            self.animation_label = QLabel()
            self.animation_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            layout.addWidget(self.animation_label)

            self.timer = QTimer(self)
            self.timer.timeout.connect(self.update_frame)
            self.timer.start(250)  # animation speed
        elif filename.startswith("*") and animated:
            pass
        else:
            # mipmap
            mipmaps = self.generate_mipmaps(texture, max_dimension)
            for mipmap_texture in mipmaps:
                mipmap_label = QLabel()
                mipmap_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
                mipmap_label.setPixmap(mipmap_texture)
                layout.addWidget(mipmap_label)

        self.setLayout(layout)

    # MIPMAP
    def generate_mipmaps(self, texture, max_dimension=200):
        mipmaps = []

        img = Image.open(texture)

        # calc new dimensions
        width, height = img.size
        if width > height:
            new_width = max_dimension
            new_height = int(height * max_dimension / width)
        else:
            new_height = max_dimension
            new_width = int(width * max_dimension / height)

        # resize pics
        resized_image = img.resize((new_width, new_height))
        resized_image = resized_image.convert("RGBA")  # Convert to RGBA format

        # generate mipmaps
        for i in range(4):
            mip_width = max(new_width // pow(2, i), 1)
            mip_height = max(new_height // pow(2, i), 1)
            mip_image = resized_image.resize((mip_width, mip_height))
            qimage = QImage(
                mip_image.tobytes(),
                mip_image.width,
                mip_image.height,
                QImage.Format_RGBA8888,
            )
            pixmap = QPixmap(qimage)
            mipmaps.append(pixmap)

        return mipmaps

    # ANIMATION
    def load_animation_frames(self, texture_path, max_dimension=200):
        frames = []

        temp_dir = os.path.dirname(texture_path)
        frames_name = os.path.basename(texture_path)

        # find other frames
        animation_paths = []

        animation_paths.append(texture_path)
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

            # calc new size
            width, height = img.size
            if width > height:
                new_width = max_dimension
                new_height = int(height * max_dimension / width)
            else:
                new_height = max_dimension
                new_width = int(width * max_dimension / height)

            # resize frames to that
            resized_image = img.resize((new_width, new_height))
            resized_image = resized_image.convert("RGBA")  # Convert to RGBA format

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
