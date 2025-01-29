"""
Allows the registration of Django/Python settings that are derived from other settings
via callable methods/lambdas. The derivation time can be controlled to happen after all
other settings have been set. The derived setting can also be overridden by setting the
derived setting to an actual value.

Example

In `lms/envs/common.py`:

```
# Double some other value that might get set later.
VALUE = lambda settings: settings.SOME_OTHER_VALUE * 2
# Register this value as one that needs to be derived later.
derived(VALUE)
```

Later in a settings file that depends on common.py

```
from lms.envs.common *

# Set some other value however you want.
SOME_OTHER_VALUE = 4

# Derive any settings and pass them this settings file for reference.
# This will update VALUE so that it is the scaler `8` instead of a lambda.
derive_settings(__name__)
```
"""
from __future__ import annotations

import sys
import typing as t
from collections.abc import Sequence


class Derived:
    """
    TODO doc
    TODO typing
    """
    def __init__(self, calculate_value: t.Callable):
        self.calculate_value = calculate_value


def derive_settings(module_name: str):
    """
    Derives all registered settings and sets them onto a particular module.

    Args:
        module_name (str): Name of module to which the derived settings will be added.
    """
    module = sys.modules[module_name]
    _derive_dict_items(module, vars(module))


def _derive_dict_items(settings, the_dict: dict):
    """
    TODO doc
    """
    for key, child in the_dict.items():
        if isinstance(child, Derived):
            the_dict[key] = child.calculate_value(settings)
        elif isinstance(child, Sequence) and not isinstance(child, str):
            the_dict[key] = _derive_sequence_items(settings, child)
            _derive_sequence_items(settings, child)
        elif isinstance(child, dict):
            _derive_dict_items(settings, child)


def _derive_sequence_items(settings, the_seq: Sequence):
    """
    TODO doc
    """
    result = []
    for ix, child in enumerate(the_seq):
        if isinstance(child, Derived):
            result.append(child.calculate_value(settings))
        elif isinstance(child, Sequence) and not isinstance(child, str):
            result.append(_derive_sequence_items(settings, child))
        elif isinstance(child, dict):
            _derive_dict_items(settings, child)
            result.append(child)
    return type(the_seq)(result)
