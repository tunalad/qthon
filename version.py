import subprocess

__version__ = "0.2.2"

try:
    desc = subprocess.check_output(
        ["git", "describe", "--tags"],
        stderr=subprocess.DEVNULL,
    ).decode().strip()

    if "-" in desc:
        __version__ = f"{__version__}+{desc.split('-', 1)[1]}"
except Exception:
    pass
