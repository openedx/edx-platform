"""
Common utility methods for Mobile APIs.
"""

API_V05 = 'v0.5'
API_V1 = 'v1'
API_V2 = 'v2'
API_V3 = 'v3'
<<<<<<< HEAD
=======
API_V4 = 'v4'
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374


def parsed_version(version):
    """ Converts string X.X.X.Y to int tuple (X, X, X) """
    return tuple(map(int, (version.split(".")[:3])))
