"""
    Helpers for accessing comprehensive theming related variables.
"""
from microsite_configuration import microsite
from microsite_configuration import page_title_breadcrumbs


def get_page_title_breadcrumbs(*args):
    """
    This is a proxy function to hide microsite_configuration behind comprehensive theming.
    """
    return page_title_breadcrumbs(*args)


def get_value(val_name, default=None, **kwargs):
    """
    This is a proxy function to hide microsite_configuration behind comprehensive theming.
    """
    return microsite.get_value(val_name, default=default, **kwargs)
