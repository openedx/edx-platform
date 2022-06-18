"""
Allows overriding existing functions and methods with alternative implementations.
"""

import functools
from importlib import import_module

from django.conf import settings


def pluggable_override(override):
    """
    This decorator allows overriding any function or method by pointing to an alternative implementation
    with `override` param.
    :param override: path to the alternative function

    Example usage:

    1. Add this decorator to an existing function `OVERRIDE_TRANSFORM` is the variable name in settings that can be
       used for overriding this function. Remember to add the `OVERRIDE_` prefix to the name to have the consistent
       namespace for the overrides.
        >>> @pluggable_override('OVERRIDE_TRANSFORM')
        ... def transform(value):
        ...     return value + 10

    2. Prepare an alternative implementation. It will have the same set of arguments as the original function, with the
       `prev_fn` added at the beginning.
        >>> def decrement(prev_fn, value):
        ...     if value >= 10:
        ...         return value - 1  # Return the decremented value.
        ...     else:
        ...         return prev_fn(value) - 1  # Call the original `transform` method before decrementing and returning.

    3. Specify the path in settings (e.g. in `envs/private.py`):
        >>> OVERRIDE_TRANSFORM = 'transform_plugin.decrement'

        You can also chain overrides:
        >>> OVERRIDE_TRANSFORM = [
        ...     'transform_plugin.decrement',
        ...     'transform_plugin.increment',
        ... ]

    Another example:

    1. We want to limit access to a Django view (e.g. `common.djangoapps.student.views.dashboard.student_dashboard`)
       to allow only logged in users. To do this add `OVERRIDE_DASHBOARD` to the original function:
       >>> @pluggable_override('OVERRIDE_DASHBOARD')
       ... def student_dashboard(request):
       ...     ...  # The rest of the implementation is not relevant in this case.

   2. Prepare an alternative implementation (e.g. in `envs/private.py` to make this example simpler):
      >>> from django.contrib.auth.decorators import login_required
      ...
      ... def dashboard(prev_fn, request):
      ...     return login_required(prev_fn)(request)
      ...
      ... OVERRIDE_DASHBOARD = 'lms.envs.private.dashboard'
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            prev_fn = f

            override_functions = getattr(settings, override, ())

            if isinstance(override_functions, str):
                override_functions = [override_functions]

            for impl in override_functions:
                module, function = impl.rsplit('.', 1)
                mod = import_module(module)
                func = getattr(mod, function)

                prev_fn = functools.partial(func, prev_fn)
            # Call the last specified function. It can call the previous one, which can call the previous one, etc.
            # (until it reaches the base implementation). It can also return without calling `prev_fn`.
            return prev_fn(*args, **kwargs)
        return wrapper
    return decorator
