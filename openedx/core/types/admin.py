"""
Typing utilities for the admin sites.
"""
import warnings

from typing import Any, Callable, Optional, Protocol


class AdminMethod(Protocol):
    """
    Duck-type definition of a callable admin method.

    See:
    https://github.com/python/mypy/issues/2087#issuecomment-462726600
    https://mypy.readthedocs.io/en/stable/protocols.html
    https://www.python.org/dev/peps/pep-0544/
    """

    short_description: str
    boolean: bool


def _admin_display(
    boolean: Optional[bool] = None, description: Optional[str] = None
) -> Callable[[Any], AdminMethod]:
    """
    Decorator for functions that need to be annotated with attributes from AdminMethod.

    This method and the above AdminMethod class will no longer be necessary in Django 3.2,
    when `admin.display` is introduced:
    https://docs.djangoproject.com/en/3.2/ref/contrib/admin/#django.contrib.admin.display
    """

    def decorator(func: Any) -> AdminMethod:
        if boolean is not None:
            func.boolean = boolean
        if description is not None:
            func.short_description = description
        return func

    return decorator


try:
    import django.contrib.admin

    admin_display = django.contrib.admin.display
    if _admin_display or AdminMethod:
        warnings.warn(
            (
                "Django 3.2+ available: the _admin_display method and the AdminMethod"
                "class should be removed from openedx.core.types"
            ),
            DeprecationWarning,
        )
except AttributeError:
    admin_display = _admin_display
