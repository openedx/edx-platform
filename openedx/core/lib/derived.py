"""
Allows the registration of Django/Python settings that are derived from other settings
via callable methods/lambdas. The derivation time can be controlled to happen after all
other settings have been set. The derived setting can also be overridden by setting the
derived setting to an actual value.
"""
import six
import sys

# Global list holding all settings which will be derived.
__DERIVED = []


def derived(*settings):
    """
    Registers settings which are derived from other settings.
    Can be called multiple times to add more derived settings.

    Args:
        settings (list): List of setting names to register.
    """
    __DERIVED.extend(settings)


def derived_dict_entry(setting_dict, key):
    """
    Registers a setting which is a dictionary and needs a derived value for a particular key.
    Can be called multiple times to add more derived settings.

    Args:
        setting_dict (str): Name of setting which contains a dictionary.
        key (str): Name of key in the setting dictionary which will be derived.
    """
    __DERIVED.append((setting_dict, key))


def derive_settings(module_name):
    """
    Derives all registered settings and sets them onto a particular module.
    Skips deriving settings that are set to a value.

    Args:
        module_name (str): Name of module to which the derived settings will be added.
    """
    module = sys.modules[module_name]
    for derived in __DERIVED:
        if isinstance(derived, six.string_types):
            setting = getattr(module, derived)
            if callable(setting):
                setting_val = setting(module)
                setattr(module, derived, setting_val)
        elif isinstance(derived, tuple):
            # If a tuple, two elements are expected - else ignore.
            if len(derived) == 2:
                # Both elements are expected to be strings.
                # The first string is the attribute which is expected to be a dictionary.
                # The second string is a key in that dictionary containing a derived setting.
                setting = getattr(module, derived[0])[derived[1]]
                if callable(setting):
                    setting_val = setting(module)
                    getattr(module, derived[0]).update({derived[1]: setting_val})


def clear_for_tests():
    """
    Clears all settings to be derived. For tests only.
    """
    global __DERIVED
    __DERIVED = []
