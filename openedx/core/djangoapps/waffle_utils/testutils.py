"""
Test utilities for waffle utilities.
"""

from functools import wraps

from waffle.testutils import override_flag

# Can be used with FilteredQueryCountMixin.assertNumQueries() to blacklist
# waffle tables. For example:
#   QUERY_COUNT_TABLE_BLACKLIST = WAFFLE_TABLES
#   with self.assertNumQueries(6, table_blacklist=QUERY_COUNT_TABLE_BLACKLIST):
WAFFLE_TABLES = ['waffle_utils_waffleflagcourseoverridemodel', 'waffle_flag', 'waffle_switch', 'waffle_sample']


def override_waffle_flag(flag, active):
    """
    To be used as a decorator for a test function to override a namespaced
    waffle flag.

        flag (WaffleFlag): The namespaced cached waffle flag.
        active (Boolean): The value to which the flag will be set.

    Example usage:

        @override_waffle_flag(UNIFIED_COURSE_TAB_FLAG, active=True)

    """

    def real_decorator(function):
        """
        Actual decorator function.
        """

        @wraps(function)
        def wrapper(*args, **kwargs):
            """
            Provides the actual override functionality of the decorator.

            Saves the previous cached value of the flag and restores it (if it
            was set), after overriding it.

            """
            waffle_namespace = flag.waffle_namespace
            namespaced_flag_name = waffle_namespace._namespaced_name(flag.flag_name)

            # save previous value and whether it existed in the cache
            cached_value_existed = namespaced_flag_name in waffle_namespace._cached_flags
            if cached_value_existed:
                previous_value = waffle_namespace._cached_flags[namespaced_flag_name]

            # set new value
            waffle_namespace._cached_flags[namespaced_flag_name] = active

            with override_flag(namespaced_flag_name, active):
                # call wrapped function
                function(*args, **kwargs)

            # restore value
            if cached_value_existed:
                waffle_namespace._cached_flags[namespaced_flag_name] = previous_value
            elif namespaced_flag_name in waffle_namespace._cached_flags:
                del waffle_namespace._cached_flags[namespaced_flag_name]
        return wrapper

    return real_decorator
