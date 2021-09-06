"""
Tests for the intercom should_show_intercom_widget helper.
"""

from mock import patch, Mock
import ddt
from django.test import TestCase
from django.conf import settings
from opaque_keys.edx.keys import CourseKey
from student.roles import (CourseCreatorRole,
                           CourseInstructorRole,
                           CourseStaffRole,
                           CourseBetaTesterRole)
from student.tests.factories import UserFactory

from openedx.core.djangoapps.appsembler.intercom_integration.helpers import (
    should_show_intercom_widget
)


@ddt.ddt
@patch.dict(settings.FEATURES, ENABLE_CREATOR_GROUP=True)
class TestShouldShowIntercomWidgetHelperTestCase(TestCase):
    """
    Tests for the `should_show_intercom_widget` helper.
    """

    def test_should_hide_for_non_authenticated(self):
        anonymous_user = Mock(is_authenticated=False)
        assert not should_show_intercom_widget(anonymous_user)

    def test_should_hide_for_superusers(self):
        superuser = UserFactory.create(is_superuser=True)
        assert not should_show_intercom_widget(superuser)

    def test_should_show_for_site_wide_staff(self):
        staff = UserFactory.create(is_staff=True)
        assert should_show_intercom_widget(staff)

    def test_should_show_for_course_creators(self):
        course_creator = UserFactory.create()
        CourseCreatorRole().add_users(course_creator)
        assert should_show_intercom_widget(course_creator)

    @ddt.unpack
    @ddt.data({
        'course_role_class': CourseStaffRole,
        'should_show': True,
    }, {
        'course_role_class': CourseInstructorRole,
        'should_show': True,
    }, {
        'course_role_class': CourseBetaTesterRole,
        'should_show': False,
    })
    def test_should_show_for_course_staff(self, course_role_class, should_show):
        course_staff = UserFactory.create(is_staff=False, is_superuser=False)
        course_key = CourseKey.from_string('course-v1:Demo+Course+2017')
        course_role_class(course_key).add_users(course_staff)
        assert should_show_intercom_widget(course_staff) == should_show
