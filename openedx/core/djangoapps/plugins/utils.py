from importlib import import_module as system_import_module
from logging import getLogger
from typing import Callable, List, Tuple

from django.utils.module_loading import import_string
from importlib_metadata import ModuleNotFoundError

from openedx.core.lib.cache_utils import process_cached
from . import registry

log = getLogger(__name__)


def import_module(module_path):
    """
    Import and returns the module at the specific path.

    Args:
        module_path is the full path to the module, including the package name.
    """
    return system_import_module(module_path)


def get_module_path(app_config, plugin_config, plugin_cls):
    return u'{package_path}.{module_path}'.format(
        package_path=app_config.name,
        module_path=plugin_config.get(plugin_cls.RELATIVE_PATH, plugin_cls.DEFAULT_RELATIVE_PATH),
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


@process_cached
def get_cached_functions_for_plugin(
    plugin_path_func: Callable[..., str],
    project_type: str,
    *plugin_path_namespace: str
) -> List[Tuple[Callable, str]]:
    """
    Returns a list of tuples where the first item is the plugin function, and
    the second item is the name of the plugin it's being called from.

    NOTE: These will be functions will be cached (in RAM not memcache) on this unique
    combination. If we enable many new views to use this system, we may notice an
    increase in memory usage as the entirety of these functions will be held in memory.

    Args:
        plugin_path_func: A function that fetches the plugin function path from the app config, project type
            and potentially additional parameter.
        project_type: a string that determines which project (lms or studio) the view is being called in. See the
            ProjectType enum in plugins/constants.py for valid options.
        *plugin_path_namespace: A variable number of additional string arguments to pass to the plugin path
            function to get the path for the desired context.

    """
    plugin_functions = []
    for app_config in registry.get_app_configs(project_type):
        plugin_function_path = plugin_path_func(app_config, project_type, *plugin_path_namespace)
        if plugin_function_path:
            module_path, _, name = plugin_function_path.rpartition('.')
            try:
                module = import_module(module_path)
            except (ImportError, ModuleNotFoundError):
                log.exception(
                    "Failed to import %s plugin",
                    module_path,
                )
                continue
            plugin_function = getattr(module, name, None)
            if plugin_function:
                plugin_name, _, _ = module_path.partition('.')
                plugin_functions.append((plugin_function, plugin_name))
            else:
                log.warning(
                    "Failed to retrieve %s function from %s plugin when rendering content",
                    name,
                    module_path,
                )
    return plugin_functions
