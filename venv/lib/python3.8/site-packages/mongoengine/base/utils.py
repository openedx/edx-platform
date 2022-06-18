import re


class LazyRegexCompiler:
    """Descriptor to allow lazy compilation of regex"""

    def __init__(self, pattern, flags=0):
        self._pattern = pattern
        self._flags = flags
        self._compiled_regex = None

    @property
    def compiled_regex(self):
        if self._compiled_regex is None:
            self._compiled_regex = re.compile(self._pattern, self._flags)
        return self._compiled_regex

    def __get__(self, instance, owner):
        return self.compiled_regex

    def __set__(self, instance, value):
        raise AttributeError("Can not set attribute LazyRegexCompiler")
