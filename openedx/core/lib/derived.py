"""
Allows the registration of Django/Python settings that are derived from other settings
via callable methods/lambdas. The derivation time can be controlled to happen after all
other settings have been set. The derived setting can also be overridden by setting the
derived setting to an actual value.
"""

import sys

# Global list holding all settings which will be derived.
__DERIVED = []


def derived(*settings):
    """
    Registers settings which are derived from other settings.
    Can be called multiple times to add more derived settings.

    Args:
        settings (str): Setting names to register.
    """
    __DERIVED.extend(settings)


def derived_collection_entry(collection_name, *accessors):
    """
    Registers a setting which is a dictionary or list and needs a derived value for a particular entry.
    Can be called multiple times to add more derived settings.

    Args:
        collection_name (str): Name of setting which contains a dictionary or list.
        accessors (int|str): Sequence of dictionary keys and list indices in the collection (and
            collections within it) leading to the value which will be derived.
            For example: 0, 'DIRS'.
    """
    __DERIVED.append((collection_name, accessors))


def derive_settings(module_name):
    """
    Derives all registered settings and sets them onto a particular module.
    Skips deriving settings that are set to a value.

    Args:
        module_name (str): Name of module to which the derived settings will be added.
    """
    module = sys.modules[module_name]
    for derived in __DERIVED:  # lint-amnesty, pylint: disable=redefined-outer-name
        if isinstance(derived, str):
            setting = getattr(module, derived)
            if callable(setting):
                setting_val = setting(module)
                setattr(module, derived, setting_val)
        elif isinstance(derived, tuple):
            # If a tuple, two elements are expected - else ignore.
            if len(derived) == 2:
                # The first element is the name of the attribute which is expected to be a dictionary or list.
                # The second element is a list of string keys in that dictionary leading to a derived setting.
                collection = getattr(module, derived[0])
                accessors = derived[1]
                for accessor in accessors[:-1]:
                    collection = collection[accessor]
                setting = collection[accessors[-1]]
                if callable(setting):
                    setting_val = setting(module)
                    collection[accessors[-1]] = setting_val


def clear_for_tests():
    """
    Clears all settings to be derived. For tests only.
    """
    global __DERIVED
    __DERIVED = []
