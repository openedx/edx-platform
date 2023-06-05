"""
Tests for the models that configures Edit LTI fields feature.
"""


from contextlib import contextmanager

import ddt
from django.test import TestCase
from edx_django_utils.cache import RequestCache
from opaque_keys.edx.locator import CourseLocator

from cms.djangoapps.xblock_config.models import CourseEditLTIFieldsEnabledFlag


@contextmanager
def lti_consumer_fields_editing_flag(course_id, enabled_for_course=False):
    """
    Yields CourseEditLTIFieldsEnabledFlag record for unit tests

    Arguments:
        course_id (CourseLocator): course locator to control this feature for.
        enabled_for_course (bool): whether feature is enabled for 'course_id'
    """
    RequestCache.clear_all_namespaces()
    CourseEditLTIFieldsEnabledFlag.objects.create(course_id=course_id, enabled=enabled_for_course)
    yield


@ddt.ddt
class TestLTIConsumerHideFieldsFlag(TestCase):
    """
    Tests the behavior of the flags for lti consumer fields' editing feature.
    These are set via Django admin settings.
    """
    def setUp(self):
        super(TestLTIConsumerHideFieldsFlag, self).setUp()
        self.course_id = CourseLocator(org="edx", course="course", run="run")

    @ddt.data(
        (True, True),
        (True, False),
        (False, True),
        (False, False),
    )
    @ddt.unpack
    def test_lti_fields_editing_feature_flags(self, enabled_for_course, is_already_sharing_learner_info):
        """
        Test that feature flag works correctly with course-specific configuration in combination with
        a boolean which indicates whether a course-run already sharing learner username/email - given
        the course-specific configuration record is present.
        """
        with lti_consumer_fields_editing_flag(
            course_id=self.course_id,
            enabled_for_course=enabled_for_course
        ):
            feature_enabled = CourseEditLTIFieldsEnabledFlag.lti_access_to_learners_editable(
                self.course_id,
                is_already_sharing_learner_info,
            )
            self.assertEqual(feature_enabled, enabled_for_course)

    @ddt.data(True, False)
    def test_lti_fields_editing_is_backwards_compatible(self, is_already_sharing_learner_info):
        """
        Test that feature flag works correctly with a boolean which indicates whether a course-run already
        sharing learner username/email - given the course-specific configuration record is not set previously.

        This tests the backward compatibility which currently is: if an existing course run is already
        sharing learner information then this feature should be enabled for that course run by default.
        """
        feature_enabled = CourseEditLTIFieldsEnabledFlag.lti_access_to_learners_editable(
            self.course_id,
            is_already_sharing_learner_info,
        )
        feature_flag_created = CourseEditLTIFieldsEnabledFlag.objects.filter(course_id=self.course_id).exists()
        self.assertEqual(feature_flag_created, is_already_sharing_learner_info)
        self.assertEqual(feature_enabled, is_already_sharing_learner_info)

    def test_enable_disable_course_flag(self):
        """
        Ensures that the flag, once enabled for a course, can also be disabled.
        """
        with lti_consumer_fields_editing_flag(
            course_id=self.course_id,
            enabled_for_course=True
        ):
            self.assertTrue(CourseEditLTIFieldsEnabledFlag.lti_access_to_learners_editable(self.course_id, False))
            with lti_consumer_fields_editing_flag(
                course_id=self.course_id,
                enabled_for_course=False
            ):
                self.assertFalse(CourseEditLTIFieldsEnabledFlag.lti_access_to_learners_editable(self.course_id, False))
