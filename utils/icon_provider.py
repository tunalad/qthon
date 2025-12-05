from PyQt5.QtCore import QFileInfo
from PyQt5.QtGui import QIcon, QPixmap, QPainter
from PyQt5.QtWidgets import QFileIconProvider


from utils.wad import get_wad_type


class WadIconProvider(QFileIconProvider):
    """
    A custom icon provider to display overlay icons on WAD files
    based on their game type.
    """

    def __init__(self):
        super().__init__()
        self.WAD_ICONS = {
            "DOOM": QPixmap(":/games/doom-48x48.png"),
            "QUAKE": QPixmap(":/games/quake-48x48.png"),
            "HL": QPixmap(":/games/hl1-32x32.png"),
        }

    def icon(self, fileInfo: QFileInfo):
        """
        Overrides the default icon implementation.

        Args:
            fileInfo (QFileInfo): Information about the file.

        Returns:
            QIcon: The new icon for the file.
        """
        if fileInfo.isFile() and fileInfo.suffix().lower() == "wad":
            wad_type = get_wad_type(fileInfo.filePath())

            if wad_type and wad_type in self.WAD_ICONS:
                # get the default icon
                default_icon = super().icon(QFileIconProvider.File)
                pixmap = default_icon.pixmap(32, 32)

                # get overlay icon
                overlay_pixmap = self.WAD_ICONS.get(wad_type)

                if overlay_pixmap:
                    # create a painter to compose the icons
                    painter = QPainter(pixmap)
                    try:
                        # scale and draw the overlay
                        overlay_scaled = overlay_pixmap.scaled(20, 20)
                        painter.drawPixmap(
                            pixmap.width() - overlay_scaled.width(),
                            pixmap.height() - overlay_scaled.height(),
                            overlay_scaled,
                        )
                    finally:
                        painter.end()

                return QIcon(pixmap)

        # fallback to the default implementation
        return super().icon(fileInfo)
