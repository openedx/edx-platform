"""
Common utility methods for Mobile APIs.
"""


def parsed_version(version):
    """ Converts string X.X.X.Y to int tuple (X, X, X) """
    return tuple(map(int, (version.split(".")[:3])))
