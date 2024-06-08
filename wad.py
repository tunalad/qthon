import os, sys

from io import BytesIO
from array import array
from struct import unpack

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

            # print(fullpath_ext)

            # Add texture name to the list
            texture_names.append(os.path.splitext(os.path.basename(fullpath_ext))[0])

            data = None
            size = None

            # Pictures
            if item.type == wad.LumpType.QPIC:
                with wad_file.open(filename) as lmp_file:
                    lump = lmp.Lmp.open(lmp_file)
                    size = lump.width, lump.height
                    data = array("B", lump.pixels)

            # Special cases
            elif item.type == wad.LumpType.MIPTEX:
                try:
                    with wad_file.open(filename) as mip_file:
                        mip = wad.Miptexture.read(mip_file)
                        data = mip.pixels[: mip.width * mip.height]
                        data = array("B", data)
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


def wadup(in_paths, out_path):
    # ensure output directory structure
    out_dir = os.path.dirname(out_path) or "."
    os.makedirs(out_dir, exist_ok=True)

    # making the palette
    palette = []
    for p in quake.palette:
        palette += p

    palette_image = Image.frombytes("P", (16, 16), bytes(palette))
    palette_image.putpalette(palette)

    # making the WAD itself
    with wad.WadFile(out_path, "w") as wad_file:
        for file_path in in_paths:
            if file_path.endswith(".png"):
                try:
                    # process the image
                    with Image.open(file_path).convert(mode="RGB") as img:
                        img = img.quantize(palette=palette_image)

                        name = os.path.basename(file_path).split(".")[0]

                        mip = wad.Miptexture()
                        mip.name = name
                        mip.width = img.width
                        mip.height = img.height
                        mip.offsets = [40]
                        mip.pixels = []

                        # mipmap pics up them
                        for i in range(4):
                            resized_image = img.resize(
                                (img.width // pow(2, i), img.height // pow(2, i))
                            )
                            data = resized_image.tobytes()
                            mip.pixels += unpack(f"<{len(data)}B", data)
                            if i < 3:
                                mip.offsets += [mip.offsets[-1] + len(data)]

                        buff = BytesIO()
                        wad.Miptexture.write(buff, mip)
                        buff.seek(0)

                        info = wad.WadInfo(name)
                        info.file_size = 40 + len(mip.pixels)
                        info.disk_size = info.file_size
                        info.compression = wad.CompressionType.NONE
                        info.type = wad.LumpType.MIPTEX

                        print(f"Adding: {file_path}")

                        wad_file.writestr(info, buff)

                except Exception as e:
                    print(f"Error processing {file_path}: {e}")


def flip_texture(texture_path, mirror=False):
    img = Image.open(texture_path)

    if mirror:
        flipped = img.transpose(Image.FLIP_LEFT_RIGHT)
    else:
        flipped = img.transpose(Image.FLIP_TOP_BOTTOM)

    flipped.save(texture_path)

    flipped.close()
    img.close()


def import_texture(images, temp_dir):
    new_paths = []
    for i in images:
        img = Image.open(i)
        x, y = img.size

        # make sure we can divide the size by 16
        if x % 16 == 0 and y % 16 == 0 and max(x, y) <= 512:
            new_width, new_height = x, y
        else:
            # use the closest sizes dividable by 16
            new_width = (x // 16) * 16
            new_height = (y // 16) * 16

            # max size 512
            if max(new_width, new_height) > 512:
                ratio = 512 / max(new_width, new_height)
                new_width = int(new_width * ratio)
                new_height = int(new_height * ratio)

            # resize if needed
            if x != new_width or y != new_height:
                img = img.resize((new_width, new_height))

        img = img.convert("P", palette=Image.ADAPTIVE, colors=256)
        base_name = os.path.splitext(os.path.basename(i))[0]

        # dealing with duplicate names
        index = 1
        new_path = f"{temp_dir}/{base_name}.png"
        while os.path.exists(new_path):
            new_path = f"{temp_dir}/{base_name} ({index}).png"
            index += 1

        # save image
        img.save(new_path, format="PNG")
        img.close()
        new_paths.append(new_path)
    return new_paths


def main():
    # unwaded = unwad("catacomb.wad")
    # pprint(unwaded)
    wadup("./gass", "gass.wad")


if __name__ == "__main__":
    main()
