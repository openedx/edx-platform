"""
Tests for Tahoe modifications in course_creators.views.py.
"""

from unittest.mock import patch
from django.contrib.auth.models import User
from django.test import TestCase

from common.djangoapps.student.roles import CourseCreatorRole
from cms.djangoapps.course_creators.views import (
    add_user_with_status_granted,
    get_course_creator_status,
)


@patch.dict('django.conf.settings.FEATURES', {
    "ENABLE_CREATOR_GROUP": True,
    "TAHOE_GRANT_CREATOR_STATUS_TO_COURSE_CREATOR_ROLE": True,
})
class CourseCreatorViewTahoeTests(TestCase):
    """
    Tests for the TAHOE_GRANT_CREATOR_STATUS_TO_COURSE_CREATOR_ROLE feature.
    """

    def setUp(self):
        """ Test case setup """
        super().setUp()
        self.user = User.objects.create_user('test_user', 'test_user+courses@edx.org', 'foo')
        self.admin = User.objects.create_user('Mark', 'admin+courses@edx.org', 'foo')
        self.admin.is_staff = True

    def test_table_initially_empty_sanity_check(self):
        """
        By default, learners don't have this status.

        This behaviour isn't related to `TAHOE_GRANT_CREATOR_STATUS_TO_COURSE_CREATOR_ROLE`.

        This redundant sanity check helps in case of platform core logic changes.
        """
        assert not get_course_creator_status(self.user)

    def test_course_creator_request_granted_sanity_check(self):
        """
        Ensure CourseCreator requests is respected when this feature is used.

        This behaviour isn't related to `TAHOE_GRANT_CREATOR_STATUS_TO_COURSE_CREATOR_ROLE`.

        This redundant sanity check helps in case of platform core logic changes.
        """
        add_user_with_status_granted(caller=self.admin, user=self.user)
        assert get_course_creator_status(self.user) == 'granted'

    def test_table_admin_is_allowed_via_feature(self):
        """
        Admin users get `granted` status instead of the Open edX default `None`.

        This is only applicable if `TAHOE_GRANT_CREATOR_STATUS_TO_COURSE_CREATOR_ROLE` is enabled.
        """
        assert get_course_creator_status(self.admin) == 'granted'

    def test_course_creator_role_allowed_via_feature(self):
        """
        Test Tahoe change of supporting `CourseCreatorRole` without explicit `CourseCreator.GRANTED`.

        This is only applicable if `TAHOE_GRANT_CREATOR_STATUS_TO_COURSE_CREATOR_ROLE` is enabled.
        """
        CourseCreatorRole().add_users(self.user)
        assert get_course_creator_status(self.user) == 'granted'
