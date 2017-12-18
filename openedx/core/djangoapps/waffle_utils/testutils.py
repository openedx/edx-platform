"""
Test utilities for waffle utilities.
"""

from waffle.testutils import override_flag

# Can be used with FilteredQueryCountMixin.assertNumQueries() to blacklist
# waffle tables. For example:
#   QUERY_COUNT_TABLE_BLACKLIST = WAFFLE_TABLES
#   with self.assertNumQueries(6, table_blacklist=QUERY_COUNT_TABLE_BLACKLIST):
WAFFLE_TABLES = ['waffle_utils_waffleflagcourseoverridemodel', 'waffle_flag', 'waffle_switch', 'waffle_sample']


class override_waffle_flag(override_flag):
    """
    override_waffle_flag is a contextmanager for easier testing of flags.

    It accepts two parameters, the flag itself and its intended state. Example
    usage::

        with override_waffle_flag(UNIFIED_COURSE_TAB_FLAG, active=True):
            ...

    If the flag already exists, its value will be changed inside the context
    block, then restored to the original value. If the flag does not exist
    before entering the context, it is created, then removed at the end of the
    block.

    It can also act as a decorator::

        @override_waffle_flag(UNIFIED_COURSE_TAB_FLAG, active=True)
        def test_happy_mode_enabled():
            ...
    """
    _cached_value = None

    def __init__(self, flag, active):
        """

        Args:
             flag (WaffleFlag): The namespaced cached waffle flag.
             active (Boolean): The value to which the flag will be set.
        """
        self.flag = flag
        waffle_namespace = flag.waffle_namespace
        name = waffle_namespace._namespaced_name(flag.flag_name)  # pylint: disable=protected-access
        super(override_waffle_flag, self).__init__(name, active)

    def __enter__(self):
        super(override_waffle_flag, self).__enter__()

        # pylint: disable=protected-access
        # Store values that have been cached on the flag
        self._cached_value = self.flag.waffle_namespace._cached_flags.get(self.name)
        self.flag.waffle_namespace._cached_flags[self.name] = self.active

    def __exit__(self, exc_type, exc_val, exc_tb):
        super(override_waffle_flag, self).__exit__(exc_type, exc_val, exc_tb)

        # pylint: disable=protected-access
        # Restore the cached values
        waffle_namespace = self.flag.waffle_namespace
        waffle_namespace._cached_flags.pop(self.name, None)

        if self._cached_value is not None:
            waffle_namespace._cached_flags[self.name] = self._cached_value
