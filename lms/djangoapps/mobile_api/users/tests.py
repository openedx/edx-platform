"""
Tests for users API
"""

import datetime
import ddt
import json

from rest_framework.test import APITestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.django import modulestore
from courseware.tests.factories import UserFactory
from django.core.urlresolvers import reverse
from django.utils import timezone
from mobile_api.users.serializers import CourseEnrollmentSerializer
from mobile_api import errors
from student.models import CourseEnrollment
from mobile_api.tests import ROLE_CASES


@ddt.ddt
class TestUserApi(ModuleStoreTestCase, APITestCase):
    """
    Test the user info API
    """
    def setUp(self):
        super(TestUserApi, self).setUp()
        self.course = CourseFactory.create(mobile_available=True)
        self.user = UserFactory.create()
        self.password = 'test'
        self.username = self.user.username

    def tearDown(self):
        super(TestUserApi, self).tearDown()
        self.client.logout()

    def _enrollment_url(self):
        """
        api url that gets the current user's course enrollments
        """
        return reverse('courseenrollment-detail', kwargs={'username': self.user.username})

    def _enroll(self, course):
        """
        enroll test user in test course
        """
        resp = self.client.post(reverse('change_enrollment'), {
            'enrollment_action': 'enroll',
            'course_id': course.id.to_deprecated_string(),
            'check_access': True,
        })
        self.assertEqual(resp.status_code, 200)

    def _verify_single_course_enrollment(self, course, should_succeed):
        """
        check that enrolling in course adds us to it
        """

        url = self._enrollment_url()
        self.client.login(username=self.username, password=self.password)
        self._enroll(course)
        response = self.client.get(url)

        courses = response.data   # pylint: disable=maybe-no-member

        self.assertEqual(response.status_code, 200)

        if should_succeed:
            self.assertEqual(len(courses), 1)
            found_course = courses[0]['course']
            self.assertTrue('video_outline' in found_course)
            self.assertTrue('course_handouts' in found_course)
            self.assertEqual(found_course['id'], unicode(course.id))
            self.assertEqual(courses[0]['mode'], 'honor')
        else:
            self.assertEqual(len(courses), 0)

    @ddt.data(*ROLE_CASES)
    @ddt.unpack
    def test_non_mobile_enrollments(self, role, should_succeed):
        non_mobile_course = CourseFactory.create(mobile_available=False)

        if role:
            role(non_mobile_course.id).add_users(self.user)

        self._verify_single_course_enrollment(non_mobile_course, should_succeed)

    def test_mobile_enrollments(self):
        self._verify_single_course_enrollment(self.course, True)

    def test_user_overview(self):
        self.client.login(username=self.username, password=self.password)
        url = reverse('user-detail', kwargs={'username': self.user.username})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.data  # pylint: disable=maybe-no-member
        self.assertEqual(data['username'], self.user.username)
        self.assertEqual(data['email'], self.user.email)

    def test_overview_anon(self):
        # anonymous disallowed
        url = reverse('user-detail', kwargs={'username': self.user.username})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)
        # can't get info on someone else
        other = UserFactory.create()
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(reverse('user-detail', kwargs={'username': other.username}))
        self.assertEqual(response.status_code, 403)

    def test_redirect_userinfo(self):
        url = '/api/mobile/v0.5/my_user_info'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        self.client.login(username=self.username, password=self.password)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.username in response['location'])

    def test_course_serializer(self):
        self.client.login(username=self.username, password=self.password)
        self._enroll(self.course)
        serialized = CourseEnrollmentSerializer(CourseEnrollment.enrollments_for_user(self.user)[0]).data  # pylint: disable=E1101
        self.assertEqual(serialized['course']['video_outline'], None)
        self.assertEqual(serialized['course']['name'], self.course.display_name)
        self.assertEqual(serialized['course']['number'], self.course.id.course)
        self.assertEqual(serialized['course']['org'], self.course.id.org)

    def test_course_serializer_with_display_overrides(self):
        self.course.display_coursenumber = "overridden_number"
        self.course.display_organization = "overridden_org"
        modulestore().update_item(self.course, self.user.id)

        self.client.login(username=self.username, password=self.password)
        self._enroll(self.course)
        serialized = CourseEnrollmentSerializer(CourseEnrollment.enrollments_for_user(self.user)[0]).data  # pylint: disable=E1101
        self.assertEqual(serialized['course']['number'], self.course.display_coursenumber)
        self.assertEqual(serialized['course']['org'], self.course.display_organization)

# Tests for user-course-status

    def _course_status_url(self):
        """
        Convenience to fetch the url for our user and course
        """
        return reverse('user-course-status', kwargs={'username': self.username, 'course_id': unicode(self.course.id)})

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

    def test_course_status_course_not_found(self):
        self.client.login(username=self.username, password=self.password)
        url = reverse('user-course-status', kwargs={'username': self.username, 'course_id': 'a/b/c'})
        response = self.client.get(url)
        json_data = json.loads(response.content)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(json_data, errors.ERROR_INVALID_COURSE_ID)

    def test_course_status_wrong_user(self):
        url = reverse('user-course-status', kwargs={'username': 'other_user', 'course_id': unicode(self.course.id)})
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_course_status_no_auth(self):
        url = self._course_status_url()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def test_default_value(self):
        (section, sub_section, unit, __) = self._setup_course_skeleton()
        self.client.login(username=self.username, password=self.password)

        url = self._course_status_url()
        result = self.client.get(url)
        json_data = json.loads(result.content)

        self.assertEqual(result.status_code, 200)
        self.assertEqual(json_data["last_visited_module_id"], unicode(unit.location))
        self.assertEqual(
            json_data["last_visited_module_path"],
            [unicode(module.location) for module in [unit, sub_section, section, self.course]]
        )

    def test_course_update_no_args(self):
        self.client.login(username=self.username, password=self.password)

        url = self._course_status_url()
        result = self.client.patch(url)  # pylint: disable=no-member
        self.assertEqual(result.status_code, 200)

    def test_course_update(self):
        (__, __, __, other_unit) = self._setup_course_skeleton()
        self.client.login(username=self.username, password=self.password)

        url = self._course_status_url()
        result = self.client.patch(  # pylint: disable=no-member
            url,
            {"last_visited_module_id": unicode(other_unit.location)}
        )
        self.assertEqual(result.status_code, 200)
        result = self.client.get(url)
        json_data = json.loads(result.content)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(json_data["last_visited_module_id"], unicode(other_unit.location))

    def test_course_update_bad_module(self):
        self.client.login(username=self.username, password=self.password)

        url = self._course_status_url()
        result = self.client.patch(  # pylint: disable=no-member
            url,
            {"last_visited_module_id": "abc"},
        )
        json_data = json.loads(result.content)
        self.assertEqual(result.status_code, 400)
        self.assertEqual(json_data, errors.ERROR_INVALID_MODULE_ID)

    def test_course_update_no_timezone(self):
        (__, __, __, other_unit) = self._setup_course_skeleton()
        self.client.login(username=self.username, password=self.password)
        url = self._course_status_url()
        past_date = datetime.datetime.now()
        result = self.client.patch(  # pylint: disable=no-member
            url,
            {
                "last_visited_module_id": unicode(other_unit.location),
                "modification_date": past_date.isoformat()  # pylint: disable=maybe-no-member
            },
        )

        json_data = json.loads(result.content)
        self.assertEqual(result.status_code, 400)
        self.assertEqual(json_data, errors.ERROR_INVALID_MODIFICATION_DATE)

    def _test_course_update_date_sync(self, date, initial_unit, update_unit, expected_unit):
        """
        Helper for test cases that use a modification to decide whether
        to update the course status
        """
        self.client.login(username=self.username, password=self.password)
        url = self._course_status_url()
        # save something so we have an initial date
        self.client.patch(  # pylint: disable=no-member
            url,
            {"last_visited_module_id": unicode(initial_unit.location)}
        )

        # now actually update it
        result = self.client.patch(  # pylint: disable=no-member
            url,
            {
                "last_visited_module_id": unicode(update_unit.location),
                "modification_date": date.isoformat()
            },
        )

        json_data = json.loads(result.content)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(json_data["last_visited_module_id"], unicode(expected_unit.location))

    def test_course_update_old_date(self):
        (__, __, unit, other_unit) = self._setup_course_skeleton()
        date = timezone.now() + datetime.timedelta(days=-100)
        self._test_course_update_date_sync(date, unit, other_unit, unit)

    def test_course_update_new_date(self):
        (__, __, unit, other_unit) = self._setup_course_skeleton()

        date = timezone.now() + datetime.timedelta(days=100)
        self._test_course_update_date_sync(date, unit, other_unit, other_unit)

    def test_course_update_no_initial_date(self):
        (__, __, _, other_unit) = self._setup_course_skeleton()
        self.client.login(username=self.username, password=self.password)
        url = self._course_status_url()
        result = self.client.patch(  # pylint: disable=no-member
            url,
            {
                "last_visited_module_id": unicode(other_unit.location),
                "modification_date": timezone.now().isoformat()
            }
        )
        json_data = json.loads(result.content)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(json_data["last_visited_module_id"], unicode(other_unit.location))

    def test_course_update_invalid_date(self):
        self.client.login(username=self.username, password=self.password)

        url = self._course_status_url()
        result = self.client.patch(  # pylint: disable=no-member
            url,
            {"modification_date": "abc"}
        )
        json_data = json.loads(result.content)
        self.assertEqual(result.status_code, 400)
        self.assertEqual(json_data, errors.ERROR_INVALID_MODIFICATION_DATE)
