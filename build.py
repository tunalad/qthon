#!/usr/bin/env python3
import subprocess
import sys
import os
import shutil
import venv


def create_venv(venv_dir):
    if os.path.exists(venv_dir):
        shutil.rmtree(venv_dir)
    print("Creating virtual environment...")
    venv.create(venv_dir, with_pip=True)


def install_deps():
    print("Installing dependencies...")
    subprocess.run([
        sys.executable, "-m", "pip", "install", "--upgrade", "pip",
        "pyinstaller", "-r", "requirements.txt"
    ])


def compile_resources():
    print("Compiling resources...")
    subprocess.run(["pyrcc5", "assets/assets.qrc", "-o", "assets/ui/resource_ui.py"])


def build():
    from version import __version__
    print(f"Building version: {__version__}")

    with open("version_build.py", "w") as f:
        f.write(f'__version__ = "{__version__}"\n')

    subprocess.run([sys.executable, "-m", "PyInstaller", "qthon.spec"])

    if os.path.exists("version_build.py"):
        os.remove("version_build.py")


def main():
    venv_dir = "venv_build"

    create_venv(venv_dir)
    install_deps()
    compile_resources()
    build()

    print("\nDone! Binary is in `dist/qthon`")


if __name__ == "__main__":
    main()
