import subprocess

__version__ = "0.1.0"

try:
    subprocess.check_output(["git", "describe", "--tags"], stderr=subprocess.DEVNULL)
except:
    try:
        git_hash = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
        __version__ = f"{__version__}+{git_hash}"
    except:
        pass
