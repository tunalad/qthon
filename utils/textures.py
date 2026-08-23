# pylint: disable=missing-module-docstring
import os

from PIL import Image

from vgio import quake

TEMP_IMAGE_EXT = ".png"
_TEMP_IMAGE_KWARGS = {"format": "PNG", "compress_level": 0}


def quake_palette():
    """
    Flattens the Quake palette into a flat RGB triplet list.

    Returns:
        list: 768 integers (256 RGB colors).
    """
    palette = []
    for row in quake.palette:
        palette += row
    return palette


def temp_texture_path(temp_dir, name):
    """
    Builds the path of a working texture file inside a temp directory.

    Args:
        temp_dir (str): Directory where working textures live.
        name (str): Texture name without extension.

    Returns:
        str: Full path of the working texture file.
    """
    return os.path.join(temp_dir, f"{name}{TEMP_IMAGE_EXT}")


def save_temp_texture(img, path):
    """
    Saves a working texture file using the app's scratch format.

    Writes to a temp file and atomically replaces the target so that
    hard-linked history snapshots keep pointing at the old data instead
    of being modified in place.

    Args:
        img (Image): PIL image to save.
        path (str): Destination path.
    """
    tmp_path = f"{path}.tmp"

    # liquids must stay png for the chromium's liquid preview window
    if os.path.basename(path).startswith("*"):
        img.save(tmp_path, format="PNG", compress_level=0)
    else:
        img.save(tmp_path, **_TEMP_IMAGE_KWARGS)

    os.replace(tmp_path, path)


def flip_texture(texture_path, mirror=False):
    """
    Flips a texture image either horizontally or vertically.

    Args:
        texture_path (str): Path to the texture image file.
        mirror (bool, optional): If True, flips horizontally. If False, flips vertically. Defaults to False.
    """
    img = Image.open(texture_path)

    if mirror:
        flipped = img.transpose(Image.FLIP_LEFT_RIGHT)
    else:
        flipped = img.transpose(Image.FLIP_TOP_BOTTOM)

    save_temp_texture(flipped, texture_path)

    flipped.close()
    img.close()


def rotate_texture(texture_path, to_right=False):
    """
    Rotates a texture image 90 degrees clockwise or counterclockwise.

    Args:
        texture_path (str): Path to the texture image file.
        to_right (bool, optional): If True, rotates 90° clockwise. If False, rotates 90° counterclockwise. Defaults to False.
    """
    img = Image.open(texture_path)

    if to_right:
        rotated = img.transpose(Image.ROTATE_270)
    else:
        rotated = img.transpose(Image.ROTATE_90)

    save_temp_texture(rotated, texture_path)

    rotated.close()
    img.close()


def get_texture_size(image_path):
    """
    Returns the dimensions of a texture image.

    Args:
        image_path (str): Path to the texture image file.

    Returns:
        tuple: Width and height of the image in pixels.
    """
    with Image.open(image_path) as img:
        return img.size
