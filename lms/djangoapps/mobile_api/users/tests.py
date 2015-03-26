"""
Tests for users API
"""

import datetime
from django.utils import timezone

from xmodule.modulestore.tests.factories import ItemFactory, CourseFactory
from xmodule.modulestore.django import modulestore
from student.models import CourseEnrollment

from .. import errors
from ..testutils import MobileAPITestCase, MobileAuthTestMixin, MobileAuthUserTestMixin, MobileEnrolledCourseAccessTestMixin
from .serializers import CourseEnrollmentSerializer


class TestUserDetailApi(MobileAPITestCase, MobileAuthUserTestMixin):
    """
    Tests for /api/mobile/v0.5/users/<user_name>...
    """
    REVERSE_INFO = {'name': 'user-detail', 'params': ['username']}

    def test_success(self):
        self.login()

        response = self.api_response()
        self.assertEqual(response.data['username'], self.user.username)
        self.assertEqual(response.data['email'], self.user.email)


class TestUserInfoApi(MobileAPITestCase, MobileAuthTestMixin):
    """
    Tests for /api/mobile/v0.5/my_user_info
    """
    def reverse_url(self, reverse_args=None, **kwargs):
        return '/api/mobile/v0.5/my_user_info'

    def test_success(self):
        """Verify the endpoint redirects to the user detail endpoint"""
        self.login()

        response = self.api_response(expected_response_code=302)
        self.assertTrue(self.username in response['location'])


class TestUserEnrollmentApi(MobileAPITestCase, MobileAuthUserTestMixin, MobileEnrolledCourseAccessTestMixin):
    """
    Tests for /api/mobile/v0.5/users/<user_name>/course_enrollments/
    """
    REVERSE_INFO = {'name': 'courseenrollment-detail', 'params': ['username']}
    ALLOW_ACCESS_TO_UNRELEASED_COURSE = True

    def verify_success(self, response):
        super(TestUserEnrollmentApi, self).verify_success(response)
        courses = response.data
        self.assertEqual(len(courses), 1)

        found_course = courses[0]['course']
        self.assertTrue('video_outline' in found_course)
        self.assertTrue('course_handouts' in found_course)
        self.assertEqual(found_course['id'], unicode(self.course.id))
        self.assertEqual(courses[0]['mode'], 'honor')

    def verify_failure(self, response):
        self.assertEqual(response.status_code, 200)
        courses = response.data
        self.assertEqual(len(courses), 0)

    def test_sort_order(self):
        self.login()

        num_courses = 3
        courses = []
        for course_num in range(num_courses):
            courses.append(CourseFactory.create(mobile_available=True))
            self.enroll(courses[course_num].id)

        # verify courses are returned in the order of enrollment, with most recently enrolled first.
        response = self.api_response()
        for course_num in range(num_courses):
            self.assertEqual(
                response.data[course_num]['course']['id'],  # pylint: disable=no-member
                unicode(courses[num_courses - course_num - 1].id)
            )


class CourseStatusAPITestCase(MobileAPITestCase):
    """
    Base test class for /api/mobile/v0.5/users/<user_name>/course_status_info/{course_id}
    """
    REVERSE_INFO = {'name': 'user-course-status', 'params': ['username', 'course_id']}

    def _setup_course_skeleton(self):
        """
        Creates a basic course structure for our course
        """
        section = ItemFactory.create(
            parent_location=self.course.location,
        )
        sub_section = ItemFactory.create(
            parent_location=section.location,
        )
        unit = ItemFactory.create(
            parent_location=sub_section.location,
        )
        other_unit = ItemFactory.create(
            parent_location=sub_section.location,
        )
        return section, sub_section, unit, other_unit


class TestCourseStatusGET(CourseStatusAPITestCase, MobileAuthUserTestMixin, MobileEnrolledCourseAccessTestMixin):
    """
    Tests for GET of /api/mobile/v0.5/users/<user_name>/course_status_info/{course_id}
    """
    def test_success(self):
        self.login_and_enroll()
        (section, sub_section, unit, __) = self._setup_course_skeleton()

        response = self.api_response()
        self.assertEqual(response.data["last_visited_module_id"], unicode(unit.location))
        self.assertEqual(
            response.data["last_visited_module_path"],
            [unicode(module.location) for module in [unit, sub_section, section, self.course]]
        )


class TestCourseStatusPATCH(CourseStatusAPITestCase, MobileAuthUserTestMixin, MobileEnrolledCourseAccessTestMixin):
    """
    Tests for PATCH of /api/mobile/v0.5/users/<user_name>/course_status_info/{course_id}
    """
    def url_method(self, url, **kwargs):
        # override implementation to use PATCH method.
        return self.client.patch(url, data=kwargs.get('data', None))  # pylint: disable=no-member

    def test_success(self):
        self.login_and_enroll()
        (__, __, __, other_unit) = self._setup_course_skeleton()

        response = self.api_response(data={"last_visited_module_id": unicode(other_unit.location)})
        self.assertEqual(response.data["last_visited_module_id"], unicode(other_unit.location))

    def test_invalid_module(self):
        self.login_and_enroll()
        response = self.api_response(data={"last_visited_module_id": "abc"}, expected_response_code=400)
        self.assertEqual(response.data, errors.ERROR_INVALID_MODULE_ID)

    def test_nonexistent_module(self):
        self.login_and_enroll()
        non_existent_key = self.course.id.make_usage_key('video', 'non-existent')
        response = self.api_response(data={"last_visited_module_id": non_existent_key}, expected_response_code=400)
        self.assertEqual(response.data, errors.ERROR_INVALID_MODULE_ID)

    def test_no_timezone(self):
        self.login_and_enroll()
        (__, __, __, other_unit) = self._setup_course_skeleton()

        past_date = datetime.datetime.now()
        response = self.api_response(
            data={
                "last_visited_module_id": unicode(other_unit.location),
                "modification_date": past_date.isoformat()  # pylint: disable=maybe-no-member
            },
            expected_response_code=400
        )
        self.assertEqual(response.data, errors.ERROR_INVALID_MODIFICATION_DATE)

    def _date_sync(self, date, initial_unit, update_unit, expected_unit):
        """
        Helper for test cases that use a modification to decide whether
        to update the course status
        """
        self.login_and_enroll()

        # save something so we have an initial date
        self.api_response(data={"last_visited_module_id": unicode(initial_unit.location)})

        # now actually update it
        response = self.api_response(
            data={
                "last_visited_module_id": unicode(update_unit.location),
                "modification_date": date.isoformat()
            }
        )
        self.assertEqual(response.data["last_visited_module_id"], unicode(expected_unit.location))

    def test_old_date(self):
        self.login_and_enroll()
        (__, __, unit, other_unit) = self._setup_course_skeleton()
        date = timezone.now() + datetime.timedelta(days=-100)
        self._date_sync(date, unit, other_unit, unit)

    def test_new_date(self):
        self.login_and_enroll()
        (__, __, unit, other_unit) = self._setup_course_skeleton()

        date = timezone.now() + datetime.timedelta(days=100)
        self._date_sync(date, unit, other_unit, other_unit)

    def test_no_initial_date(self):
        self.login_and_enroll()
        (__, __, _, other_unit) = self._setup_course_skeleton()
        response = self.api_response(
            data={
                "last_visited_module_id": unicode(other_unit.location),
                "modification_date": timezone.now().isoformat()
            }
        )
        self.assertEqual(response.data["last_visited_module_id"], unicode(other_unit.location))

    def test_invalid_date(self):
        self.login_and_enroll()
        response = self.api_response(data={"modification_date": "abc"}, expected_response_code=400)
        self.assertEqual(response.data, errors.ERROR_INVALID_MODIFICATION_DATE)


class TestCourseEnrollmentSerializer(MobileAPITestCase):
    """
    Test the course enrollment serializer
    """
    def test_success(self):
        self.login_and_enroll()

        serialized = CourseEnrollmentSerializer(CourseEnrollment.enrollments_for_user(self.user)[0]).data  # pylint: disable=no-member
        self.assertEqual(serialized['course']['video_outline'], None)
        self.assertEqual(serialized['course']['name'], self.course.display_name)
        self.assertEqual(serialized['course']['number'], self.course.id.course)
        self.assertEqual(serialized['course']['org'], self.course.id.org)

    def test_with_display_overrides(self):
        self.login_and_enroll()

        self.course.display_coursenumber = "overridden_number"
        self.course.display_organization = "overridden_org"
        modulestore().update_item(self.course, self.user.id)

        serialized = CourseEnrollmentSerializer(CourseEnrollment.enrollments_for_user(self.user)[0]).data  # pylint: disable=no-member
        self.assertEqual(serialized['course']['number'], self.course.display_coursenumber)
        self.assertEqual(serialized['course']['org'], self.course.display_organization)
