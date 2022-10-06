"""
Common utility methods for Mobile APIs.
"""

API_V05 = 'v0.5'
API_V1 = 'v1'
API_V2 = 'v2'


def parsed_version(version):
    """ Converts string X.X.X.Y to int tuple (X, X, X) """
    return tuple(map(int, (version.split(".")[:3])))
