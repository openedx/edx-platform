"""
This file defines any decorators used by the shopping cart app
"""

from django.http import Http404
from .utils import is_shopping_cart_enabled


def enforce_shopping_cart_enabled(func):
    """
    Is a decorator that forces a wrapped method to be run in a runtime
    which has the ENABLE_SHOPPING_CART flag set
    """
    def func_wrapper(*args, **kwargs):
        """
        Wrapper function that does the enforcement that
        the shopping cart feature is enabled
        """
        if not is_shopping_cart_enabled():
            raise Http404
        return func(*args, **kwargs)
    return func_wrapper
