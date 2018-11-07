"""
Tests for course verification sock
"""

import datetime
import ddt

from course_modes.models import CourseMode
from openedx.core.djangoapps.waffle_utils.testutils import override_waffle_flag
from openedx.features.course_experience import DISPLAY_COURSE_SOCK_FLAG
from student.tests.factories import UserFactory, CourseEnrollmentFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from .test_course_home import course_home_url

TEST_PASSWORD = 'test'
TEST_VERIFICATION_SOCK_LOCATOR = '<div class="verification-sock"'
TEST_COURSE_PRICE = 50


@ddt.ddt
class TestCourseSockView(SharedModuleStoreTestCase):
    """
    Tests for the course verification sock fragment view.
    """
    @classmethod
    def setUpClass(cls):
        super(TestCourseSockView, cls).setUpClass()

        # Create four courses
        cls.standard_course = CourseFactory.create()
        cls.verified_course = CourseFactory.create()
        cls.verified_course_update_expired = CourseFactory.create()
        cls.verified_course_already_enrolled = CourseFactory.create()

        # Assign each verifiable course a upgrade deadline
        cls._add_course_mode(cls.verified_course, upgrade_deadline_expired=False)
        cls._add_course_mode(cls.verified_course_update_expired, upgrade_deadline_expired=True)
        cls._add_course_mode(cls.verified_course_already_enrolled, upgrade_deadline_expired=False)

    def setUp(self):
        super(TestCourseSockView, self).setUp()
        self.user = UserFactory.create()

        # Enroll the user in the four courses
        CourseEnrollmentFactory.create(user=self.user, course_id=self.standard_course.id)
        CourseEnrollmentFactory.create(user=self.user, course_id=self.verified_course.id)
        CourseEnrollmentFactory.create(user=self.user, course_id=self.verified_course_update_expired.id)
        CourseEnrollmentFactory.create(user=self.user, course_id=self.verified_course_already_enrolled.id, mode=CourseMode.VERIFIED)

        # Log the user in
        self.client.login(username=self.user.username, password=TEST_PASSWORD)

    @override_waffle_flag(DISPLAY_COURSE_SOCK_FLAG, active=True)
    def test_standard_course(self):
        """
        Assure that a course that cannot be verified does
        not have a visible verification sock.
        """
        response = self.client.get(course_home_url(self.standard_course))
        self.assert_verified_sock_is_not_visible(self.standard_course, response)

    @override_waffle_flag(DISPLAY_COURSE_SOCK_FLAG, active=True)
    def test_verified_course(self):
        """
        Assure that a course that can be verified has a
        visible verification sock.
        """
        response = self.client.get(course_home_url(self.verified_course))
        self.assert_verified_sock_is_visible(self.verified_course, response)

    @override_waffle_flag(DISPLAY_COURSE_SOCK_FLAG, active=True)
    def test_verified_course_updated_expired(self):
        """
        Assure that a course that has an expired upgrade
        date does not display the verification sock.
        """
        response = self.client.get(course_home_url(self.verified_course_update_expired))
        self.assert_verified_sock_is_not_visible(self.verified_course_update_expired, response)

    @override_waffle_flag(DISPLAY_COURSE_SOCK_FLAG, active=True)
    def test_verified_course_user_already_upgraded(self):
        """
        Assure that a user that has already upgraded to a
        verified status cannot see the verification sock.
        """
        response = self.client.get(course_home_url(self.verified_course_already_enrolled))
        self.assert_verified_sock_is_not_visible(self.verified_course_already_enrolled, response)

    def assert_verified_sock_is_visible(self, course, response):
        return self.assertIn(
            TEST_VERIFICATION_SOCK_LOCATOR,
            response.content,
            msg='Student should be able to see sock if they have already upgraded to verified mode.',
        )

    def assert_verified_sock_is_not_visible(self, course, response):
        return self.assertNotIn(
            TEST_VERIFICATION_SOCK_LOCATOR,
            response.content,
            msg='Student should not be able to see sock in a unverifiable course.',
        )

    @classmethod
    def _add_course_mode(cls, course, upgrade_deadline_expired=False):
        """
        Adds a course mode to the test course.
        """
        upgrade_exp_date = datetime.datetime.now()
        if upgrade_deadline_expired:
            upgrade_exp_date = upgrade_exp_date - datetime.timedelta(days=21)
        else:
            upgrade_exp_date = upgrade_exp_date + datetime.timedelta(days=21)

        CourseMode(
            course_id=course.id,
            mode_slug=CourseMode.VERIFIED,
            mode_display_name="Verified Certificate",
            min_price=TEST_COURSE_PRICE,
            _expiration_datetime=upgrade_exp_date,  # pylint: disable=protected-access
        ).save()
