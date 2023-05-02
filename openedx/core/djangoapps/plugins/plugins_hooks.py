"""
Plugin extension points module
"""
import logging
from importlib import import_module

from django.conf import settings

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

log = logging.getLogger(__name__)


def run_extension_point(extension_point, *args, **kwargs):
    """
    Wrapper function to execute any extension point at platform level
    if exceptions occurs returns None.
    """
    path = configuration_helpers.get_value(
        extension_point,
        getattr(settings, extension_point, None),
    )

    if not path:
        return None

    try:
        module_name, func_name = path.rsplit('.', 1)
        module = import_module(module_name)
        extension_function = getattr(module, func_name)

        return extension_function(*args, **kwargs)
    except ImportError:
        log.info('Could not import the %s : %s', extension_point, module)
    except AttributeError:
        log.info('Could not import the function %s in the module %s', func_name, module)
    except ValueError:
        log.info('Could not load the information from \"%s\"', path)

    return None
