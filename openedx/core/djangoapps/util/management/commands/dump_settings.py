"""
Defines the dump_settings management command.
"""
import inspect
import json
import re

from django.conf import settings
from django.core.management.base import BaseCommand


SETTING_NAME_REGEX = re.compile(r'^[A-Z][A-Z0-9_]*$')


class Command(BaseCommand):
    """
    Dump current Django settings to JSON for debugging/diagnostics.

    BEWARE: OUTPUT IS NOT SUITABLE FOR CONSUMPTION BY PRODUCTION SYSTEMS.
    The purpose of this output is to be *helpful* for a *human* operator to understand how their settings are being
    rendered and how they differ between different settings files. The serialization format is NOT perfect: there are
    certain situations where two different settings will output identical JSON. For example, this command does NOT:

    disambiguate between lists and tuples:
    * (1, 2, 3)  # <-- this tuple will be printed out as [1, 2, 3]
    * [1, 2, 3]

    disambiguate between sets and sorted lists:
    * {2, 1, 3}  # <-- this set will be printed out as [1, 2, 3]
    * [1, 2, 3]

    disambiguate between internationalized and non-internationalized strings:
    * _("hello") # <-- this will become just "hello"
    * "hello"

    Furthermore, objects which are not easily JSON-ifiable will stringified using their `repr(...)`, e.g.:
    * "Path('my/path')"                                                # a Path object
    * "<lms.myapp.MyClass object at 0x704599fa2fd0>"                   # some random class instance
    * "<_io.TextIOWrapper name='<stderr>' mode='w' encoding='utf-8'>"  # sys.stderr

    and lambdas are printed by *roughly* printing out their source lines (it's impossible in Python to get the *exact*
    source code, as it's been compiled into bytecode).
    """

    def handle(self, *args, **kwargs):
        """
        Handle the command.
        """
        settings_json = {
            name: _to_json_friendly_repr(getattr(settings, name))
            for name in dir(settings)
            if SETTING_NAME_REGEX.match(name)
        }
        print(json.dumps(settings_json, indent=4))


def _to_json_friendly_repr(value: object) -> object:
    """
    Turn the value into something that we can print to a JSON file (that is: str, bool, None, int, float, list, dict).

    See the docstring of `Command` for warnings about this function's behavior.
    """
    if isinstance(value, (type(None), bool, int, float, str)):
        # All these types can be printed directly
        return value
    if isinstance(value, (list, tuple, set)):
        if isinstance(value, set):
            # Print sets by sorting them (so that order doesn't matter) into a JSON array.
            elements = sorted(value)
        else:
            # Print both lists and tuples as JSON arrays.
            elements = value
        return [_to_json_friendly_repr(element) for ix, element in enumerate(elements)]
    if isinstance(value, dict):
        # Print dicts as JSON objects
        for subkey in value.keys():
            if not isinstance(subkey, (str, int)):
                raise ValueError(f"Unexpected dict key {subkey} of type {type(subkey)}")
        return {subkey: _to_json_friendly_repr(subval) for subkey, subval in value.items()}
    if proxy_args := getattr(value, "_proxy____args", None):
        if len(proxy_args) == 1 and isinstance(proxy_args[0], str):
            # Print gettext_lazy as simply the wrapped string
            return proxy_args[0]
    try:
        qualname = value.__qualname__
    except AttributeError:
        pass
    else:
        if qualname == "<lambda>":
            # Handle lambdas by printing the source lines
            return "lambda defined with line(s): " + inspect.getsource(value).strip()
    # For all other objects, print the repr
    return repr(value)
