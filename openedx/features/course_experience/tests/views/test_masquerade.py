"""
Tests for masquerading functionality on course_experience
"""

from edx_toggles.toggles.testutils import override_waffle_flag
from lms.djangoapps.courseware.tests.helpers import MasqueradeMixin
from openedx.features.course_experience import DISPLAY_COURSE_SOCK_FLAG, SHOW_UPGRADE_MSG_ON_COURSE_HOME
from common.djangoapps.student.roles import CourseStaffRole
from common.djangoapps.student.tests.factories import CourseEnrollmentFactory, UserFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.partitions.partitions import ENROLLMENT_TRACK_PARTITION_ID
from xmodule.partitions.partitions_service import PartitionService

from .helpers import add_course_mode
from .test_course_home import course_home_url
from .test_course_sock import TEST_VERIFICATION_SOCK_LOCATOR

TEST_PASSWORD = 'test'
UPGRADE_MESSAGE_CONTAINER = 'section-upgrade'


class MasqueradeTestBase(SharedModuleStoreTestCase, MasqueradeMixin):
    """
    Base test class for masquerading functionality on course_experience
    """
    @classmethod
    def setUpClass(cls):
        super(MasqueradeTestBase, cls).setUpClass()

        # Create two courses
        cls.verified_course = CourseFactory.create()
        cls.masters_course = CourseFactory.create()
        # Create a verifiable course mode with an upgrade deadline in each course
        add_course_mode(cls.verified_course, upgrade_deadline_expired=False)
        add_course_mode(cls.masters_course, upgrade_deadline_expired=False)
        add_course_mode(cls.masters_course, mode_slug='masters', mode_display_name='Masters')

    def setUp(self):
        super(MasqueradeTestBase, self).setUp()
        self.course_staff = UserFactory.create()
        CourseStaffRole(self.verified_course.id).add_users(self.course_staff)
        CourseStaffRole(self.masters_course.id).add_users(self.course_staff)

        # Enroll the user in the two courses
        CourseEnrollmentFactory.create(user=self.course_staff, course_id=self.verified_course.id)
        CourseEnrollmentFactory.create(user=self.course_staff, course_id=self.masters_course.id)

        # Log the staff user in
        self.client.login(username=self.course_staff.username, password=TEST_PASSWORD)

    def get_group_id_by_course_mode_name(self, course_id, mode_name):
        """
        Get the needed group_id from the Enrollment_Track partition for the specific masquerading track.
        """
        partition_service = PartitionService(course_id)
        enrollment_track_user_partition = partition_service.get_user_partition(ENROLLMENT_TRACK_PARTITION_ID)
        for group in enrollment_track_user_partition.groups:
            if group.name == mode_name:
                return group.id
        return None


class TestVerifiedUpgradesWithMasquerade(MasqueradeTestBase):
    """
    Tests for the course verification upgrade messages while the user is being masqueraded.
    """

    @override_waffle_flag(DISPLAY_COURSE_SOCK_FLAG, active=True)
    @override_waffle_flag(SHOW_UPGRADE_MSG_ON_COURSE_HOME, active=True)
    def test_masquerade_as_student(self):
        # Elevate the staff user to be student
        self.update_masquerade(course=self.verified_course, user_partition_id=ENROLLMENT_TRACK_PARTITION_ID)
        response = self.client.get(course_home_url(self.verified_course))
        self.assertContains(response, TEST_VERIFICATION_SOCK_LOCATOR, html=False)
        self.assertContains(response, UPGRADE_MESSAGE_CONTAINER, html=False)

    @override_waffle_flag(DISPLAY_COURSE_SOCK_FLAG, active=True)
    def test_masquerade_as_verified_student(self):
        user_group_id = self.get_group_id_by_course_mode_name(
            self.verified_course.id,
            'Verified Certificate'
        )
        self.update_masquerade(course=self.verified_course, group_id=user_group_id,
                               user_partition_id=ENROLLMENT_TRACK_PARTITION_ID)
        response = self.client.get(course_home_url(self.verified_course))
        self.assertNotContains(response, TEST_VERIFICATION_SOCK_LOCATOR, html=False)
        self.assertNotContains(response, UPGRADE_MESSAGE_CONTAINER, html=False)

    @override_waffle_flag(DISPLAY_COURSE_SOCK_FLAG, active=True)
    def test_masquerade_as_masters_student(self):
        user_group_id = self.get_group_id_by_course_mode_name(
            self.masters_course.id,
            'Masters'
        )
        self.update_masquerade(course=self.masters_course, group_id=user_group_id,
                               user_partition_id=ENROLLMENT_TRACK_PARTITION_ID)
        response = self.client.get(course_home_url(self.masters_course))
        self.assertNotContains(response, TEST_VERIFICATION_SOCK_LOCATOR, html=False)
        self.assertNotContains(response, UPGRADE_MESSAGE_CONTAINER, html=False)
