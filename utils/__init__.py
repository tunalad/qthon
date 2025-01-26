def path(*args):
    # now this might be a bad practice,
    # but I don't want to have unnecessary imports when running other utils.
    # and I like short function names, that's why this exists
    os = __import__("os")
    sys = __import__("sys")

    if getattr(sys, "frozen", False):
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    else:
        # Development environment
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    return os.path.join(base_path, *args)
