"""
Helpers for accessing comprehensive theming related variables.
"""
from django.conf import settings

from microsite_configuration import microsite, page_title_breadcrumbs


def get_page_title_breadcrumbs(*args):
    """
    This is a proxy function to hide microsite_configuration behind comprehensive theming.
    """
    return page_title_breadcrumbs(*args)


def get_value(val_name, default=None, **kwargs):
    """
    This is a proxy function to hide microsite_configuration behind comprehensive theming.
    """

    # Retrieve the requested field/value from the microsite configuration
    microsite_value = microsite.get_value(val_name, default=default, **kwargs)

    # Attempt to perform a dictionary update using the provided default
    # This will fail if either the default or the microsite value is not a dictionary
    try:
        value = dict(default)
        value.update(microsite_value)

    # If the dictionary update fails, just use the microsite value
    # TypeError: default is not iterable (simple value or None)
    # ValueError: default is iterable but not a dict (list, not dict)
    # AttributeError: default does not have an 'update' method
    except (TypeError, ValueError, AttributeError):
        value = microsite_value

    # Return the end result to the caller
    return value


def get_template_path(relative_path, **kwargs):
    """
    This is a proxy function to hide microsite_configuration behind comprehensive theming.
    """
    return microsite.get_template_path(relative_path, **kwargs)


def is_request_in_themed_site():
    """
    This is a proxy function to hide microsite_configuration behind comprehensive theming.
    """
    return microsite.is_request_in_microsite()


def get_themed_template_path(relative_path, default_path, **kwargs):
    """
    This is a proxy function to hide microsite_configuration behind comprehensive theming.

    The workflow considers the "Stanford theming" feature alongside of microsites.  It returns
    the path of the themed template (i.e. relative_path) if Stanford theming is enabled AND
    microsite theming is disabled, otherwise it will return the path of either the microsite
    override template or the base lms template.

    :param relative_path: relative path of themed template
    :param default_path: relative path of the microsite's or lms template to use if
        theming is disabled or microsite is enabled
    """
    is_stanford_theming_enabled = settings.FEATURES.get("USE_CUSTOM_THEME", False)
    is_microsite = microsite.is_request_in_microsite()
    if is_stanford_theming_enabled and not is_microsite:
        return relative_path
    return microsite.get_template_path(default_path, **kwargs)
