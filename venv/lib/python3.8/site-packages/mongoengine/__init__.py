# Import submodules so that we can expose their __all__
from mongoengine import (
    connection,
    document,
    errors,
    fields,
    queryset,
    signals,
)

# Import everything from each submodule so that it can be accessed via
# mongoengine, e.g. instead of `from mongoengine.connection import connect`,
# users can simply use `from mongoengine import connect`, or even
# `from mongoengine import *` and then `connect('testdb')`.
from mongoengine.connection import *  # noqa: F401
from mongoengine.document import *  # noqa: F401
from mongoengine.errors import *  # noqa: F401
from mongoengine.fields import *  # noqa: F401
from mongoengine.queryset import *  # noqa: F401
from mongoengine.signals import *  # noqa: F401

__all__ = (
    list(document.__all__)
    + list(fields.__all__)
    + list(connection.__all__)
    + list(queryset.__all__)
    + list(signals.__all__)
    + list(errors.__all__)
)


VERSION = (0, 24, 1)


def get_version():
    """Return the VERSION as a string.

    For example, if `VERSION == (0, 10, 7)`, return '0.10.7'.
    """
    return ".".join(map(str, VERSION))


__version__ = get_version()
