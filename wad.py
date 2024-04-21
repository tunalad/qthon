import os, array, sys

from pprint import pprint

from PIL import Image

from vgio import quake
from vgio.quake import lmp, wad


def unwad(wad_path, temp_dir):
    """
    Extracts contents of a WAD file to PNG files and returns texture names.

    Args:
        wad_path (str): Path to the WAD file.
        temp_dir (str): Path to the TEMP folder, where we extract the textures.

    Returns:
        tuple: A tuple containing the path to the temporary directory where contents are extracted
               and a list of texture names extracted from the WAD file.
    """
    if not wad.is_wadfile(wad_path):
        raise ValueError(f"Invalid WAD file: {wad_path}")

    texture_names = []

    # Flatten out palette
    palette = []
    for p in quake.palette:
        palette += p

    with wad.WadFile(wad_path) as wad_file:
        for item in wad_file.infolist():
            filename = item.filename
            fullpath = os.path.join(temp_dir, filename)
            fullpath_ext = "{0}.png".format(fullpath)

            # Check if duplicate
            count = 1
            while os.path.exists(fullpath_ext):
                # append suffix
                filename, ext = os.path.splitext(filename)
                fullpath_ext = f"{os.path.join(temp_dir, filename)} ({count}){ext}"
                fullpath_ext = "{0}.png".format(fullpath_ext)  # Update fullpath_ext
                count += 1

            print(fullpath_ext)

            # Add texture name to the list
            texture_names.append(os.path.splitext(os.path.basename(fullpath_ext))[0])

            data = None
            size = None

            # Pictures
            if item.type == wad.LumpType.QPIC:
                with wad_file.open(filename) as lmp_file:
                    lump = lmp.Lmp.open(lmp_file)
                    size = lump.width, lump.height
                    data = array.array("B", lump.pixels)

            # Special cases
            elif item.type == wad.LumpType.MIPTEX:
                try:
                    with wad_file.open(filename) as mip_file:
                        mip = wad.Miptexture.read(mip_file)
                        data = mip.pixels[: mip.width * mip.height]
                        data = array.array("B", data)
                        size = mip.width, mip.height
                except Exception as e:
                    print(f"Failed to extract resource: {filename}", file=sys.stderr)
                    continue

            try:
                # Convert to image file
                if data is not None and size is not None:
                    img = Image.frombuffer("P", size, data, "raw", "P", 0, 1)
                    img.putpalette(palette)
                    img.save(fullpath_ext)
                else:
                    wad_file.extract(filename, temp_dir)
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr)

    return temp_dir, texture_names


def main():
    unwaded = unwad("catacomb.wad")
    pprint(unwaded)


if __name__ == "__main__":
    main()
