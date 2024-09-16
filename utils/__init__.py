def path(*args):
    # now this might be a bad practice,
    # but I don't want to have unnecessary imports when running other utils.
    # and I like short function names, that's why this exists
    return __import__("os").path.join(*args)
