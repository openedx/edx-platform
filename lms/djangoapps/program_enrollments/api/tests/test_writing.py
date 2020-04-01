"""
Tests for program enrollment writing Python API.

Currently, we do not directly unit test the functions in api/writing.py extensively.
This is okay for now because they are all used in
`rest_api.v1.views` and is thus tested through `rest_api.v1.tests.test_views`.
Eventually it would be good to directly test the Python API function and just use
mocks in the view tests.
"""


from uuid import UUID

from django.core.cache import cache
from opaque_keys.edx.keys import CourseKey
from organizations.tests.factories import OrganizationFactory

from course_modes.models import CourseMode
from lms.djangoapps.program_enrollments.constants import ProgramCourseEnrollmentStatuses as PCEStatuses
from lms.djangoapps.program_enrollments.constants import ProgramCourseOperationStatuses as CourseStatuses
from lms.djangoapps.program_enrollments.constants import ProgramEnrollmentStatuses as PEStatuses
from lms.djangoapps.program_enrollments.models import (
    CourseAccessRoleAssignment,
    ProgramCourseEnrollment,
    ProgramEnrollment
)
from lms.djangoapps.program_enrollments.tests.factories import ProgramCourseEnrollmentFactory, ProgramEnrollmentFactory
from openedx.core.djangoapps.catalog.cache import PROGRAM_CACHE_KEY_TPL
from openedx.core.djangoapps.catalog.tests.factories import CourseFactory, CourseRunFactory
from openedx.core.djangoapps.catalog.tests.factories import OrganizationFactory as CatalogOrganizationFactory
from openedx.core.djangoapps.catalog.tests.factories import ProgramFactory
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase
from student.roles import CourseStaffRole
from student.tests.factories import CourseEnrollmentFactory, UserFactory
from third_party_auth.tests.factories import SAMLProviderConfigFactory

from ..writing import write_program_course_enrollments, write_program_enrollments


class EnrollmentWriteTest(CacheIsolationTestCase):
    ENABLED_CACHES = ['default']

    organization_key = 'test'

    program_uuid = UUID('dddddddd-5f48-493d-9910-84e1d36c657f')

    curriculum_uuid_a = UUID('aaaaaaaa-bd26-4370-94b8-b4063858210b')

    @classmethod
    def setUpClass(cls):
        """
        Set up test data
        """
        super(EnrollmentWriteTest, cls).setUpClass()
        catalog_org = CatalogOrganizationFactory.create(key=cls.organization_key)
        cls.program = ProgramFactory.create(
            uuid=cls.program_uuid,
            authoring_organizations=[catalog_org]
        )
        organization = OrganizationFactory.create(short_name=cls.organization_key)
        SAMLProviderConfigFactory.create(organization=organization)

        catalog_course_id_str = 'course-v1:edX+ToyX'
        course_run_id_str = '{}+Toy_Course'.format(catalog_course_id_str)
        cls.course_id = CourseKey.from_string(course_run_id_str)
        CourseOverviewFactory(id=cls.course_id)
        course_run = CourseRunFactory(key=course_run_id_str)
        cls.course = CourseFactory(key=catalog_course_id_str, course_runs=[course_run])
        cls.student_1 = UserFactory(username='student-1')
        cls.student_2 = UserFactory(username='student-2')

    def setUp(self):
        super(EnrollmentWriteTest, self).setUp()
        cache.set(PROGRAM_CACHE_KEY_TPL.format(uuid=self.program_uuid), self.program, None)

    def create_program_enrollment(self, external_user_key, user=False):
        """
        Creates and returns a ProgramEnrollment for the given external_user_key and
        user if specified.
        """
        program_enrollment = ProgramEnrollmentFactory.create(
            external_user_key=external_user_key,
            program_uuid=self.program_uuid,
        )
        if user is not False:
            program_enrollment.user = user
            program_enrollment.save()
        return program_enrollment
        

class WritingProgramEnrollmentTest(EnrollmentWriteTest):
    """
    Test cases for program enrollment writing functions.
    """
    def test_write_program_enrollments_status_ended(self):
        """
        Successfully updates program enrollment to status ended if requested.
        This also validates history records are created on both create and update.
        """
        assert ProgramEnrollment.objects.count() == 0
        assert ProgramEnrollment.historical_records.count() == 0  # pylint: disable=no-member
        write_program_enrollments(self.program_uuid, [{
            'external_user_key': 'learner-1',
            'status': PEStatuses.PENDING,
            'curriculum_uuid': self.curriculum_uuid_a,
        }], True, False)
        assert ProgramEnrollment.objects.count() == 1
        assert ProgramEnrollment.historical_records.count() == 1  # pylint: disable=no-member
        write_program_enrollments(self.program_uuid, [{
            'external_user_key': 'learner-1',
            'status': PEStatuses.ENDED,
            'curriculum_uuid': self.curriculum_uuid_a,
        }], False, True)
        assert ProgramEnrollment.objects.count() == 1
        assert ProgramEnrollment.historical_records.count() == 2  # pylint: disable=no-member
        assert ProgramEnrollment.objects.filter(status=PEStatuses.ENDED).exists()


class WritingProgramCourseEnrollmentTest(EnrollmentWriteTest):

    def course_enrollment_request(self, external_key, status='active', course_staff=None):
        return {
            'external_user_key': external_key,
            'status': status,
            'course_staff': course_staff
        }

    def create_program_course_enrollment(self, program_enrollment, course_status='active'):
        """
        Creates and returns a ProgramCourseEnrollment for the given program_enrollment and
        self.course_key, creating a CourseEnrollment if the program enrollment has a user
        """
        course_enrollment = None
        if program_enrollment.user:
            course_enrollment = CourseEnrollmentFactory.create(
                course_id=self.course_id,
                user=program_enrollment.user,
                mode=CourseMode.MASTERS
            )
            course_enrollment.is_active = course_status == "active"
            course_enrollment.save()
        return ProgramCourseEnrollmentFactory.create(
            program_enrollment=program_enrollment,
            course_key=self.course_id,
            course_enrollment=course_enrollment,
            status=course_status,
        )

    def create_program_and_course_enrollments(self, external_user_key, user=False, course_status='active'):
        program_enrollment = self.create_program_enrollment(external_user_key, user)
        return self.create_program_course_enrollment(program_enrollment, course_status=course_status)

    def assert_program_course_enrollment(self, external_user_key, expected_status, has_user, mode=CourseMode.MASTERS):
        """
        Convenience method to assert that a ProgramCourseEnrollment exists,
        and potentially that a CourseEnrollment also exists
        """
        enrollment = ProgramCourseEnrollment.objects.get(
            program_enrollment__external_user_key=external_user_key,
            program_enrollment__program_uuid=self.program_uuid
        )
        self.assertEqual(expected_status, enrollment.status)
        self.assertEqual(self.course_id, enrollment.course_key)
        course_enrollment = enrollment.course_enrollment
        if has_user:
            self.assertIsNotNone(course_enrollment)
            self.assertEqual(expected_status == "active", course_enrollment.is_active)
            self.assertEqual(self.course_id, course_enrollment.course_id)
            self.assertEqual(mode, course_enrollment.mode)
        else:
            self.assertIsNone(course_enrollment)

    def test_create_enrollments(self):
        self.create_program_enrollment('learner-1')
        self.create_program_enrollment('learner-2')
        self.create_program_enrollment('learner-3', user=None)
        self.create_program_enrollment('learner-4', user=None)
        course_enrollment_requests = [
            self.course_enrollment_request('learner-1', 'active'),
            self.course_enrollment_request('learner-2', 'inactive'),
            self.course_enrollment_request('learner-3', 'active'),
            self.course_enrollment_request('learner-4', 'inactive'),
        ]

        result = write_program_course_enrollments(
            self.program_uuid,
            self.course_id,
            course_enrollment_requests,
            True,
            False
        )
        self.assertDictEqual(
            {
                'learner-1': 'active',
                'learner-2': 'inactive',
                'learner-3': 'active',
                'learner-4': 'inactive',
            },
            result,
        )
        self.assert_program_course_enrollment('learner-1', 'active', True)
        self.assert_program_course_enrollment('learner-2', 'inactive', True)
        self.assert_program_course_enrollment('learner-3', 'active', False)
        self.assert_program_course_enrollment('learner-4', 'inactive', False)

    def test_program_course_enrollment_exists(self):
        """
        The program enrollments application already has a program_course_enrollment
        record for this user and course
        """
        self.create_program_and_course_enrollments('learner-1')
        course_enrollment_requests = [self.course_enrollment_request('learner-1')]
        result = write_program_course_enrollments(
            self.program_uuid,
            self.course_id,
            course_enrollment_requests,
            True,
            False 
        )
        self.assertDictEqual({'learner-1': CourseStatuses.CONFLICT}, result)

    def test_create_enrollments_and_assign_staff(self):
        """
        Successfully creates both waiting and linked program course enrollments with the course staff role.
        """
        course_staff_role = CourseStaffRole(self.course_id)
        course_staff_role.add_users(self.student_1)

        self.create_program_enrollment('learner-1', user=None)
        self.create_program_enrollment('learner-2', user=None)
        self.create_program_enrollment('learner-3', user=self.student_1)
        self.create_program_enrollment('learner-4', user=self.student_2)
        course_enrollment_requests = [
            self.course_enrollment_request('learner-1', 'active', True),
            self.course_enrollment_request('learner-2', 'active', True),
            self.course_enrollment_request('learner-3', 'active', True),
            self.course_enrollment_request('learner-4', 'active', True),
        ]
        write_program_course_enrollments(
            self.program_uuid,
            self.course_id,
            course_enrollment_requests,
            True,
            False
        )

        self.assert_program_course_enrollment('learner-1', 'active', False)
        self.assert_program_course_enrollment('learner-2', 'active', False)
        self.assert_program_course_enrollment('learner-3', 'active', True)
        self.assert_program_course_enrollment('learner-4', 'active', True)

        # Users linked to either enrollment are given the course staff role
        self.assertListEqual(
            [self.student_1, self.student_2],
            list(course_staff_role.users_with_role())
        )

        # CourseAccessRoleAssignment objects are created for enrollments with no linked user
        pending_role_assingments = CourseAccessRoleAssignment.objects.all()
        assert pending_role_assingments.count() == 2
        pending_role_assingments.get(
            enrollment__program_enrollment__external_user_key='learner-1',
            enrollment__course_key=self.course_id
        )
        pending_role_assingments.get(
            enrollment__program_enrollment__external_user_key='learner-2',
            enrollment__course_key=self.course_id
        )
    
    def test_user_currently_enrolled_in_course(self):
        """
        If a user is already enrolled in a course through a different method
        that enrollment should be linked but not overwritten as masters.
        """
        CourseEnrollmentFactory.create(
            course_id=self.course_id,
            user=self.student_1,
            mode=CourseMode.VERIFIED
        )
        self.create_program_enrollment('learner-1', user=self.student_1)
        write_program_course_enrollments(
            self.program_uuid,
            self.course_id,
            [self.course_enrollment_request('learner-1', 'active')],
            True,
            False
        )
        self.assert_program_course_enrollment('learner-1', 'active', True, mode=CourseMode.VERIFIED)
