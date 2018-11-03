import sys

import six

try:
    from os import fsencode, fsdecode
except ImportError:
    from backports.os import fsencode, fsdecode  # type: ignore

try:
    from os import fspath
except ImportError:

    def fspath(path):
        """Return the path representation of a path-like object.

        If str or bytes is passed in, it is returned unchanged. Otherwise the
        os.PathLike interface is used to get the path representation. If the
        path representation is not str or bytes, TypeError is raised. If the
        provided path is not str, bytes, or os.PathLike, TypeError is raised.
        """
        if isinstance(path, (six.text_type, bytes)):
            return path

        # Work from the object's type to match method resolution of other magic
        # methods.
        path_type = type(path)
        try:
            path_repr = path_type.__fspath__(path)
        except AttributeError:
            if hasattr(path_type, "__fspath__"):
                raise
            else:
                raise TypeError(
                    "expected string type or os.PathLike object, "
                    "not " + path_type.__name__
                )
        if isinstance(path_repr, (six.text_type, bytes)):
            return path_repr
        else:
            raise TypeError(
                "expected {}.__fspath__() to return string type "
                "not {}".format(path_type.__name__, type(path_repr).__name__)
            )
