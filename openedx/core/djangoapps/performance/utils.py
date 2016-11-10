"""
Common utilities for performance testing.
"""
from contextlib import contextmanager


def collect_profile_func(file_prefix, enabled=False):
    """
    Method decorator for collecting profile.
    """
    import functools

    def _outer(func):
        """
        Outer function decorator.
        """
        @functools.wraps(func)
        def _inner(self, *args, **kwargs):
            """
            Inner wrapper function.
            """
            if enabled:
                with collect_profile(file_prefix):
                    return func(self, *args, **kwargs)
            else:
                return func(self, *args, **kwargs)
        return _inner
    return _outer


@contextmanager
def collect_profile(file_prefix):
    """
    Context manager to collect profile information.
    """
    import cProfile
    import uuid
    profiler = cProfile.Profile()
    profiler.enable()
    try:
        yield
    finally:
        profiler.disable()
        profiler.dump_stats("{0}_{1}_master.profile".format(file_prefix, uuid.uuid4()))
