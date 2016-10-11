"""
Tests for coursegraph's signal handler on course publish
"""
from __future__ import unicode_literals

from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.coursegraph.signals import _listen_for_course_publish
from openedx.core.djangoapps.coursegraph.utils import CourseLastPublishedCache
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase


class TestCourseGraphSignalHandler(CacheIsolationTestCase):
    """
    Tests for the course publish course handler
    """
    ENABLED_CACHES = ['default']

    def test_cache_set_on_course_publish(self):
        """
        Tests that the last published cache is set on course publish
        """
        course_key = CourseKey.from_string('course-v1:org+course+run')
        last_published_cache = CourseLastPublishedCache()
        self.assertIsNone(last_published_cache.get(course_key))
        _listen_for_course_publish(None, course_key)
        self.assertIsNotNone(last_published_cache.get(course_key))
