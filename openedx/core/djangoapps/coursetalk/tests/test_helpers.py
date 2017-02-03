""" CourseTalk widget helpers tests """
from __future__ import unicode_literals

from django import test

from opaque_keys.edx.locations import SlashSeparatedCourseKey
from openedx.core.djangoapps.coursetalk import helpers
from openedx.core.djangoapps.coursetalk import models
from openedx.core.djangolib.testing.utils import skip_unless_lms


@skip_unless_lms
class CourseTalkKeyTests(test.TestCase):
    """
    CourseTalkKeyTests:
    tests for function get_coursetalk_course_key
    tests for function inject_coursetalk_keys_into_context
    """

    PLATFORM_KEY = 'some_platform'

    def setUp(self):
        super(CourseTalkKeyTests, self).setUp()
        self.course_key = SlashSeparatedCourseKey('org', 'course', 'run')
        self.context = {}

    def db_set_up(self, enabled):
        """
        Setup database for this test:
        Create CourseTalkWidgetConfiguration
        """
        config = models.CourseTalkWidgetConfiguration.current()
        config.enabled = enabled
        config.platform_key = self.PLATFORM_KEY
        config.save()

    def test_simple_key(self):
        coursetalk_course_key = helpers.get_coursetalk_course_key(self.course_key)
        self.assertEqual(coursetalk_course_key, 'org_course')

    def test_inject_coursetalk_keys_when_widget_not_enabled(self):
        self.db_set_up(False)
        helpers.inject_coursetalk_keys_into_context(self.context, self.course_key)
        self.assertNotIn('show_coursetalk_widget', self.context)
        self.assertNotIn('platform_key', self.context)
        self.assertNotIn('course_review_key', self.context)

    def test_inject_coursetalk_keys_when_widget_enabled(self):
        self.db_set_up(True)
        helpers.inject_coursetalk_keys_into_context(self.context, self.course_key)
        self.assertIn('show_coursetalk_widget', self.context)
        self.assertIn('platform_key', self.context)
        self.assertIn('course_review_key', self.context)
        self.assertEqual(self.context.get('show_coursetalk_widget'), True)
        self.assertEqual(self.context.get('platform_key'), self.PLATFORM_KEY)
        self.assertEqual(self.context.get('course_review_key'), 'org_course')
