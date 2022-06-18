"""
utils to help with imports

Please remember to expose any new public methods in the `__init__.py` file.
"""
from importlib import import_module as system_import_module

from django.utils.module_loading import import_string


def import_module(module_path):
    """
    Import and returns the module at the specific path.

    Args:
        module_path is the full path to the module, including the package name.
    """
    return system_import_module(module_path)


def get_module_path(app_config, plugin_config, plugin_cls):
    return "{package_path}.{module_path}".format(
        package_path=app_config.name,
        module_path=plugin_config.get(
            plugin_cls.RELATIVE_PATH, plugin_cls.DEFAULT_RELATIVE_PATH
        ),
    )


def import_attr(attr_path):
    """
    Import and returns a module's attribute at the specific path.

    Args:
        attr_path should be of the form:
            {full_module_path}.attr_name
    """
    return import_string(attr_path)


def import_attr_in_module(imported_module, attr_name):
    """
    Import and returns the attribute with name attr_name
    in the given module.
    """
    return getattr(imported_module, attr_name)
