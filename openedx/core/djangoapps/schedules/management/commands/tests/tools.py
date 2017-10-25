from openedx.core.djangolib.testing.utils import CacheIsolationTestCase, FilteredQueryCountMixin

class ScheduleBaseEmailTestBase(FilteredQueryCountMixin, CacheIsolationTestCase):

    ENABLED_CACHES = ['default']
