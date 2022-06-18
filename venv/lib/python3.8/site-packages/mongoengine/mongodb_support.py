"""
Helper functions, constants, and types to aid with MongoDB version support
"""
from mongoengine.connection import get_connection

# Constant that can be used to compare the version retrieved with
# get_mongodb_version()
MONGODB_34 = (3, 4)
MONGODB_36 = (3, 6)
MONGODB_42 = (4, 2)
MONGODB_44 = (4, 4)


def get_mongodb_version():
    """Return the version of the default connected mongoDB (first 2 digits)

    :return: tuple(int, int)
    """
    version_list = get_connection().server_info()["versionArray"][:2]  # e.g: (3, 2)
    return tuple(version_list)
