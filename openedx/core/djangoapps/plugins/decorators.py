from typing import Callable

from functools import wraps


def view_namespace(slot_namespace: str) -> Callable:
    """
    Adds the "slot_namespace" attribute to the decorated view.

    This is used by the template slots plugin mechanism to find which view to decorate.
    :param slot_namespace: The namespace for the slots rendered by this view.
    """
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            return view(*args, **kwargs)
        setattr(wrapper, 'slot_namespace', slot_namespace)
        return wrapper
    return decorator
