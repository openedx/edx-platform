__all__ = [
    "ZoneInfo",
    "reset_tzpath",
    "available_timezones",
    "TZPATH",
    "ZoneInfoNotFoundError",
    "InvalidTZPathWarning",
]
import sys

from . import _tzpath
from ._common import ZoneInfoNotFoundError
from ._version import __version__

try:
    from ._czoneinfo import ZoneInfo
except ImportError:  # pragma: nocover
    from ._zoneinfo import ZoneInfo

reset_tzpath = _tzpath.reset_tzpath
available_timezones = _tzpath.available_timezones
InvalidTZPathWarning = _tzpath.InvalidTZPathWarning

if sys.version_info < (3, 7):
    # Module-level __getattr__ was added in Python 3.7, so instead of lazily
    # populating TZPATH on every access, we will register a callback with
    # reset_tzpath to update the top-level tuple.
    TZPATH = _tzpath.TZPATH

    def _tzpath_callback(new_tzpath):
        global TZPATH
        TZPATH = new_tzpath

    _tzpath.TZPATH_CALLBACKS.append(_tzpath_callback)
    del _tzpath_callback

else:

    def __getattr__(name):
        if name == "TZPATH":
            return _tzpath.TZPATH
        else:
            raise AttributeError(
                f"module {__name__!r} has no attribute {name!r}"
            )


def __dir__():
    return sorted(list(globals()) + ["TZPATH"])
