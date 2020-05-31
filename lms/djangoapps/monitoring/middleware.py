"""
Middleware for monitoring the LMS
"""
from collections.abc import Iterable
import logging
from django.conf import settings
from edx_django_utils.monitoring import set_custom_metric

log = logging.getLogger(__name__)


class CodeOwnerMetricMiddleware:
    """
    Django middleware object to set custom metric for the owner of each view.

    See _code_owner_mappings_to_path_mappings for details of the lookup structure.

    Custom metrics set:
    - code_owner: The owning team mapped to the current view.
    - code_owner_mapping_config_load_errors: If there are errors loading config. Even
        though this isn't done as part of the transaction, we want to ensure that any
        config issue is addressed immediately because it could affect monitoring and
        alerts.
    - code_owner_mapping_error: If there are any errors when trying to perform the mapping.
    - view_func_module: The __module__ of the view_func, which can be used to
        find missing mappings.

    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Set custom metric for the code_owner of the view if configured to do so.
        """
        if _CODE_OWNER_MAPPINGS_CONFIG_LOAD_ERRORS:
            set_custom_metric('code_owner_mapping_config_load_errors', _CODE_OWNER_MAPPINGS_CONFIG_LOAD_ERRORS)

        if not _PATH_TO_CODE_OWNER_MAPPINGS:
            return

        try:
            view_func_module = _get_view_func_module(view_func)
            set_custom_metric('view_func_module', view_func_module)
            code_owner = self._find_code_owner(view_func_module)
            if code_owner:
                set_custom_metric('code_owner', code_owner)
        except Exception as e:
            set_custom_metric('code_owner_mapping_error', e)

    def _find_code_owner(self, view_func_module):
        """
        Attempts lookup of code_owner based on the view_func's __module__,
        finding the most specific match. If no match, returns None.

        For example, if the module were 'openedx.features.discounts.views',
        this lookup would match on 'openedx.features.discounts' before
        'openedx.features', because the former is more specific.

        """
        view_func_module_parts = view_func_module.split('.')
        # To match the most specific, tests the most number of parts first
        for number_of_parts in range(len(view_func_module_parts), 0, -1):
            partial_path = '.'.join(view_func_module_parts[0:number_of_parts])
            if partial_path in _PATH_TO_CODE_OWNER_MAPPINGS:
                code_owner = _PATH_TO_CODE_OWNER_MAPPINGS[partial_path]
                return code_owner
        return None


def _load_path_to_code_owner_mappings():
    """
    Takes the CODE_OWNER_MAPPINGS Django Setting, and re-organizes and loads
    into _PATH_TO_CODE_OWNER_MAPPINGS. Sets to None if there are no mappings.

    Returns
        tuple: (mappings, load_errors)

    Example CODE_OWNER_MAPPINGS Django Setting:

        CODE_OWNER_MAPPINGS = {
            'team-red': [
                'xblock_django',
                'openedx.core.djangoapps.xblock',
            ],
            'team-blue': [
                'badges',
            ],
        }

    Example return value::

        {
            'xblock_django': 'team-red',
            'openedx.core.djangoapps.xblock': 'team-red',
            'badges': 'team-blue',
        }

    Note: If the Django Setting has invalid data, we load as much as possible
        and logs errors for bad data. Also will add errors as custom metric on
        all transactions to increase visibility of any config issue.

    """
    if not hasattr(settings, 'CODE_OWNER_MAPPINGS') or not settings.CODE_OWNER_MAPPINGS:
        return (None, None)

    path_to_code_owner_mappings = {}
    errors = []
    try:
        if isinstance(settings.CODE_OWNER_MAPPINGS, dict):
            for code_owner in settings.CODE_OWNER_MAPPINGS:
                if not isinstance(code_owner, str):
                    errors.append(
                        'CODE_OWNER_MAPPINGS keys should be code owner as string, but found {}'.format(code_owner)
                    )
                path_list = settings.CODE_OWNER_MAPPINGS[code_owner]
                if isinstance(path_list, Iterable):
                    for path in path_list:
                        if isinstance(path, str):
                            path_to_code_owner_mappings[path] = code_owner
                        else:
                            errors.append(
                                'CODE_OWNER_MAPPINGS[{}] list should contain path strings, but found {}'.format(
                                    code_owner, path
                                )
                            )
                else:
                    errors.append(
                        'CODE_OWNER_MAPPINGS[{}] should be a list of paths, but found {}'.format(code_owner, path_list)
                    )
        else:
            errors.append(
                'CODE_OWNER_MAPPINGS should be a dict, but found {}'.format(type(settings.CODE_OWNER_MAPPINGS))
            )
    except Exception as e:
        errors.append('Unknown error loading from settings.CODE_OWNER_MAPPINGS: {}'.format(e))
    if errors:
        log.error('Errors loading path_to_code_owner_mappings. {}'.format(errors))
    return path_to_code_owner_mappings, errors

_mappings_and_errors = _load_path_to_code_owner_mappings()
# Stores lookup table for code owner given a module path
_PATH_TO_CODE_OWNER_MAPPINGS = _mappings_and_errors[0]
_CODE_OWNER_MAPPINGS_CONFIG_LOAD_ERRORS = _mappings_and_errors[1]


def _get_view_func_module(view_func):
    """
    Returns the view_func's __module__.  Enables simpler testing via mocking.
    """
    return view_func.__module__
