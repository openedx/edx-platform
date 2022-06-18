import ntpath
import fnmatch


def load(param):
    """
    If the supplied parameter is a string, assume it's a simple
    pattern.
    """
    return (
        Pattern(param)
        if isinstance(param, str)
        else param
        if param is not None
        else Null()
    )


class Base:
    pass


class Null(Base):
    def __call__(self, path):
        return True


class Pattern(Base):
    def __init__(self, pattern):
        self.pattern = pattern

    def get_pattern(self, normcase):
        try:
            return self._pattern
        except AttributeError:
            pass
        self._pattern = normcase(self.pattern)
        return self._pattern

    def __call__(self, path):
        normcase = getattr(self, 'normcase', path.module.normcase)
        pattern = self.get_pattern(normcase)
        return fnmatch.fnmatchcase(normcase(path.name), pattern)


class CaseInsensitive(Pattern):
    """
    A Pattern with a ``'normcase'`` property, suitable for passing to
    :meth:`listdir`, :meth:`dirs`, :meth:`files`, :meth:`walk`,
    :meth:`walkdirs`, or :meth:`walkfiles` to match case-insensitive.

    For example, to get all files ending in .py, .Py, .pY, or .PY in the
    current directory::

        from path import Path, matchers
        Path('.').files(matchers.CaseInsensitive('*.py'))
    """

    normcase = staticmethod(ntpath.normcase)
