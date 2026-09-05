#!/usr/bin/env python3
import subprocess
import sys
import os
import shutil
import venv

VENV_DIR = "venv_build_win" if sys.platform == "win32" else "venv_build"
BIN_DIR = "Scripts" if sys.platform == "win32" else "bin"
EXE_SUFFIX = ".exe" if sys.platform == "win32" else ""


def create_venv():
    if os.path.exists(VENV_DIR):
        shutil.rmtree(VENV_DIR)
    print("Creating virtual environment...")
    venv.create(VENV_DIR, with_pip=True)


def install_deps():
    print("Installing dependencies...")
    subprocess.run(
        [
            f"{VENV_DIR}/{BIN_DIR}/python{EXE_SUFFIX}",
            "-m",
            "pip",
            "install",
            "--upgrade",
            "pip",
            "pyinstaller",
            "-r",
            "requirements.txt",
        ]
    )


def compile_resources():
    print("Compiling resources...")
    subprocess.run(["pyrcc5", "assets/assets.qrc", "-o", "assets/ui/resource_ui.py"])


def build():
    from version import __version__

    print(f"Building version: {__version__}")

    with open("version_build.py", "w") as f:
        f.write(f'__version__ = "{__version__}"\n')

    subprocess.run(
        [f"{VENV_DIR}/{BIN_DIR}/pyinstaller{EXE_SUFFIX}", "--noconfirm", "qthon.spec"]
    )

    if os.path.exists("version_build.py"):
        os.remove("version_build.py")


def main():
    create_venv()
    install_deps()
    compile_resources()
    build()
    print("\nDone! Binary is in `dist/qthon`")


if __name__ == "__main__":
    main()
