"""
Tests for the CCX REST APIs.
"""


import json
import math
import string
from datetime import timedelta

import ddt
import mock
import six
from ccx_keys.locator import CCXLocator
from django.conf import settings
from django.contrib.auth.models import User
from django.urls import Resolver404, resolve, reverse
from django.utils.timezone import now
from oauth2_provider import models as dot_models
from opaque_keys.edx.keys import CourseKey
from rest_framework import status
from rest_framework.test import APITestCase
from six.moves import range, zip

from lms.djangoapps.ccx.api.v0 import views
from lms.djangoapps.ccx.models import CcxFieldOverride, CustomCourseForEdX
from lms.djangoapps.ccx.overrides import override_field_for_ccx
from lms.djangoapps.ccx.tests.utils import CcxTestCase
from lms.djangoapps.ccx.utils import ccx_course as ccx_course_cm
from lms.djangoapps.courseware import courses
from lms.djangoapps.instructor.access import allow_access, list_with_level
from lms.djangoapps.instructor.enrollment import enroll_email, get_email_params
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.roles import CourseCcxCoachRole, CourseInstructorRole, CourseStaffRole
from common.djangoapps.student.tests.factories import AdminFactory, UserFactory

USER_PASSWORD = 'test'


class CcxRestApiTest(CcxTestCase, APITestCase):
    """
    Base class with common methods to be used in the test classes of this module
    """
    @classmethod
    def setUpClass(cls):
        super(CcxRestApiTest, cls).setUpClass()

    def setUp(self):
        """
        Set up tests
        """
        super(CcxRestApiTest, self).setUp()
        # add some info about the course for easy access
        self.master_course_key = self.course.location.course_key
        self.master_course_key_str = six.text_type(self.master_course_key)
        # OAUTH2 setup
        # create a specific user for the application
        self.app_user = app_user = UserFactory(
            username='test_app_user',
            email='test_app_user@openedx.org',
            password=USER_PASSWORD
        )

        # add staff role to the app user
        CourseStaffRole(self.master_course_key).add_users(app_user)

        # adding instructor to master course.
        instructor = UserFactory()
        allow_access(self.course, instructor, 'instructor')

        self.auth = self.prepare_auth_token(app_user)

        self.course.enable_ccx = True
        self.mstore.update_item(self.course, self.coach.id)
        # making the master course chapters easily available
        self.master_course_chapters = courses.get_course_chapter_ids(self.master_course_key)

    def prepare_auth_token(self, user):
        """
        creates auth token for users
        """
        # create an oauth2 provider client app entry
        app_client_oauth2_provider = dot_models.Application.objects.create(
            name='test client 2',
            user=user,
            client_type='confidential',
            authorization_grant_type='authorization-code',
            redirect_uris='http://localhost:8079/complete/edxorg/'
        )
        # create an authorization code
        auth_oauth2_provider = dot_models.AccessToken.objects.create(
            user=user,
            application=app_client_oauth2_provider,
            expires=now() + timedelta(weeks=1),
            scope='read write',
            token='16MGyP3OaQYHmpT1lK7Q6MMNAZsjwF'
        )

        auth_header_oauth2_provider = u"Bearer {0}".format(auth_oauth2_provider)

        return auth_header_oauth2_provider

    def expect_error(self, http_code, error_code_str, resp_obj):
        """
        Helper function that checks that the response object
        has a body with the provided error
        """
        self.assertEqual(resp_obj.status_code, http_code)
        self.assertIn('error_code', resp_obj.data)
        self.assertEqual(resp_obj.data['error_code'], error_code_str)

    def expect_error_fields(self, expected_field_errors, resp_obj):
        """
        Helper function that checks that the response object
        has a body with the provided field errors
        """
        self.assertEqual(resp_obj.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('field_errors', resp_obj.data)
        # restructure the error dictionary for a easier comparison
        resp_dict_error = {}
        for field_name, error_dict in six.iteritems(resp_obj.data['field_errors']):
            resp_dict_error[field_name] = error_dict.get('error_code', '')
        self.assertEqual(expected_field_errors, resp_dict_error)


@ddt.ddt
class CcxListTest(CcxRestApiTest):
    """
    Test for the CCX REST APIs
    """
    ENABLED_SIGNALS = ['course_published']

    @classmethod
    def setUpClass(cls):
        super(CcxListTest, cls).setUpClass()

    def setUp(self):
        """
        Set up tests
        """
        super(CcxListTest, self).setUp()
        self.list_url = reverse('ccx_api:v0:ccx:list')
        self.list_url_master_course = six.moves.urllib.parse.urljoin(
            self.list_url,
            '?master_course_id={0}'.format(six.moves.urllib.parse.quote_plus(self.master_course_key_str))
        )

    def test_authorization(self):
        """
        Test that only the right token is authorized
        """
        auth_list = [
            "Wrong token-type-obviously",
            "Bearer wrong token format",
            "Bearer wrong-token",
            "Bearer",
            "Bearer hfbhfbfwq398248fnid939rh3489fh39nd4m34r9"  # made up token
        ]
        # all the auths in the list fail to authorize
        for auth in auth_list:
            resp = self.client.get(self.list_url_master_course, {}, HTTP_AUTHORIZATION=auth)
            self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        resp = self.client.get(self.list_url_master_course, {}, HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_authorization_no_oauth_staff(self):
        """
        Check authorization for staff users logged in without oauth
        """
        # create a staff user
        staff_user = UserFactory(
            username='test_staff_user',
            email='test_staff_user@openedx.org',
            password=USER_PASSWORD
        )
        # add staff role to the staff user
        CourseStaffRole(self.master_course_key).add_users(staff_user)

        data = {
            'master_course_id': self.master_course_key_str,
            'max_students_allowed': 111,
            'display_name': 'CCX Test Title',
            'coach_email': self.coach.email
        }
        # the staff user can perform the request
        self.client.login(username=staff_user.username, password=USER_PASSWORD)
        resp = self.client.get(self.list_url_master_course)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        resp = self.client.post(self.list_url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_authorization_no_oauth_instructor(self):
        """
        Check authorization for instructor users logged in without oauth
        """
        # create an instructor user
        instructor_user = UserFactory(
            username='test_instructor_user', email='test_instructor_user@openedx.org', password=USER_PASSWORD
        )
        # add instructor role to the instructor user
        CourseInstructorRole(self.master_course_key).add_users(instructor_user)

        data = {
            'master_course_id': self.master_course_key_str,
            'max_students_allowed': 111,
            'display_name': 'CCX Test Title',
            'coach_email': self.coach.email
        }

        # the instructor user can perform the request
        self.client.login(username=instructor_user.username, password=USER_PASSWORD)
        resp = self.client.get(self.list_url_master_course)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        resp = self.client.post(self.list_url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_authorization_no_oauth(self):
        """
        Check authorization for coach users logged in without oauth
        """
        # create an coach user
        coach_user = UserFactory(
            username='test_coach_user', email='test_coach_user@openedx.org', password=USER_PASSWORD
        )
        # add coach role to the coach user
        CourseCcxCoachRole(self.master_course_key).add_users(coach_user)

        data = {
            'master_course_id': self.master_course_key_str,
            'max_students_allowed': 111,
            'display_name': 'CCX Test Title',
            'coach_email': self.coach.email
        }
        # the coach user cannot perform the request: this type of user can only get her own CCX
        self.client.login(username=coach_user.username, password=USER_PASSWORD)
        resp = self.client.get(self.list_url_master_course)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        resp = self.client.post(self.list_url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_list_wrong_master_course(self):
        """
        Test for various get requests with wrong master course string
        """
        # mock the permission class these cases can be tested
        mock_class_str = 'openedx.core.lib.api.permissions.IsMasterCourseStaffInstructor.has_permission'
        with mock.patch(mock_class_str, autospec=True) as mocked_perm_class:
            mocked_perm_class.return_value = True
            # case with no master_course_id provided
            resp = self.client.get(self.list_url, {}, HTTP_AUTHORIZATION=self.auth)
            self.expect_error(status.HTTP_400_BAD_REQUEST, 'master_course_id_not_provided', resp)

            base_url = six.moves.urllib.parse.urljoin(self.list_url, '?master_course_id=')
            # case with empty master_course_id
            resp = self.client.get(base_url, {}, HTTP_AUTHORIZATION=self.auth)
            self.expect_error(status.HTTP_400_BAD_REQUEST, 'course_id_not_valid', resp)

            # case with invalid master_course_id
            url = '{0}invalid_master_course_str'.format(base_url)
            resp = self.client.get(url, {}, HTTP_AUTHORIZATION=self.auth)
            self.expect_error(status.HTTP_400_BAD_REQUEST, 'course_id_not_valid', resp)

            # case with inexistent master_course_id
            url = '{0}course-v1%3Aorg_foo.0%2Bcourse_bar_0%2BRun_0'.format(base_url)
            resp = self.client.get(url, {}, HTTP_AUTHORIZATION=self.auth)
            self.expect_error(status.HTTP_404_NOT_FOUND, 'course_id_does_not_exist', resp)

    def test_get_list(self):
        """
        Tests the API to get a list of CCX Courses
        """
        # there are no CCX courses
        resp = self.client.get(self.list_url_master_course, {}, HTTP_AUTHORIZATION=self.auth)
        self.assertIn('count', resp.data)
        self.assertEqual(resp.data['count'], 0)

        # create few ccx courses
        num_ccx = 10
        for _ in range(num_ccx):
            self.make_ccx()
        resp = self.client.get(self.list_url_master_course, {}, HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('count', resp.data)
        self.assertEqual(resp.data['count'], num_ccx)
        self.assertIn('results', resp.data)
        self.assertEqual(len(resp.data['results']), num_ccx)

    def test_get_sorted_list(self):
        """
        Tests the API to get a sorted list of CCX Courses
        """
        # create few ccx courses
        num_ccx = 3
        for _ in range(num_ccx):
            self.make_ccx()
        # update the display_name fields
        all_ccx = CustomCourseForEdX.objects.all()
        all_ccx = all_ccx.order_by('id')
        self.assertEqual(len(all_ccx), num_ccx)
        title_str = u'Title CCX {0}'
        for num, ccx in enumerate(all_ccx):
            ccx.display_name = title_str.format(string.ascii_lowercase[-(num + 1)])
            ccx.save()

        # sort by display name
        url = '{0}&order_by=display_name'.format(self.list_url_master_course)
        resp = self.client.get(url, {}, HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data['results']), num_ccx)
        # the display_name should be sorted as "Title CCX x", "Title CCX y", "Title CCX z"
        for num, ccx in enumerate(resp.data['results']):
            self.assertEqual(title_str.format(string.ascii_lowercase[-(num_ccx - num)]), ccx['display_name'])

        # add sort order desc
        url = '{0}&order_by=display_name&sort_order=desc'.format(self.list_url_master_course)
        resp = self.client.get(url, {}, HTTP_AUTHORIZATION=self.auth)
        # the only thing I can check is that the display name is in alphabetically reversed order
        # in the same way when the field has been updated above, so with the id asc
        for num, ccx in enumerate(resp.data['results']):
            self.assertEqual(title_str.format(string.ascii_lowercase[-(num + 1)]), ccx['display_name'])

    def test_get_paginated_list(self):
        """
        Tests the API to get a paginated list of CCX Courses
        """
        # create some ccx courses
        num_ccx = 357
        for _ in range(num_ccx):
            self.make_ccx()
        page_size = settings.REST_FRAMEWORK.get('PAGE_SIZE', 10)
        num_pages = int(math.ceil(num_ccx / float(page_size)))
        # get first page
        resp = self.client.get(self.list_url_master_course, {}, HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['count'], num_ccx)
        self.assertEqual(resp.data['num_pages'], num_pages)
        self.assertEqual(resp.data['current_page'], 1)
        self.assertEqual(resp.data['start'], 0)
        self.assertIsNotNone(resp.data['next'])
        self.assertIsNone(resp.data['previous'])

        # get a page in the middle
        url = '{0}&page=24'.format(self.list_url_master_course)
        resp = self.client.get(url, {}, HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['count'], num_ccx)
        self.assertEqual(resp.data['num_pages'], num_pages)
        self.assertEqual(resp.data['current_page'], 24)
        self.assertEqual(resp.data['start'], (resp.data['current_page'] - 1) * page_size)
        self.assertIsNotNone(resp.data['next'])
        self.assertIsNotNone(resp.data['previous'])

        # get last page
        url = '{0}&page={1}'.format(self.list_url_master_course, num_pages)
        resp = self.client.get(url, {}, HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['count'], num_ccx)
        self.assertEqual(resp.data['num_pages'], num_pages)
        self.assertEqual(resp.data['current_page'], num_pages)
        self.assertEqual(resp.data['start'], (resp.data['current_page'] - 1) * page_size)
        self.assertIsNone(resp.data['next'])
        self.assertIsNotNone(resp.data['previous'])

        # last page + 1
        url = '{0}&page={1}'.format(self.list_url_master_course, num_pages + 1)
        resp = self.client.get(url, {}, HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    @ddt.data(
        (
            {},
            status.HTTP_400_BAD_REQUEST,
            'master_course_id_not_provided',
        ),
        (
            {'master_course_id': None},
            status.HTTP_400_BAD_REQUEST,
            'master_course_id_not_provided',
        ),
        (
            {'master_course_id': ''},
            status.HTTP_400_BAD_REQUEST,
            'course_id_not_valid',
        ),
        (
            {'master_course_id': 'invalid_master_course_str'},
            status.HTTP_400_BAD_REQUEST,
            'course_id_not_valid',
        ),
        (
            {'master_course_id': 'course-v1:org_foo.0+course_bar_0+Run_0'},
            status.HTTP_404_NOT_FOUND,
            'course_id_does_not_exist',
        ),
    )
    @ddt.unpack
    def test_post_list_wrong_master_course(self, data, expected_http_error, expected_error_string):
        """
        Test for various post requests with wrong master course string
        """
        # mock the permission class these cases can be tested
        mock_class_str = 'openedx.core.lib.api.permissions.IsMasterCourseStaffInstructor.has_permission'
        with mock.patch(mock_class_str, autospec=True) as mocked_perm_class:
            mocked_perm_class.return_value = True
            # case with no master_course_id provided
            resp = self.client.post(self.list_url, data, format='json', HTTP_AUTHORIZATION=self.auth)
            self.expect_error(expected_http_error, expected_error_string, resp)

    def test_post_list_wrong_master_course_special_cases(self):
        """
        Same as test_post_list_wrong_master_course,
        but different ways to test the wrong master_course_id
        """
        # case with ccx not enabled for  master_course_id
        self.course.enable_ccx = False
        self.mstore.update_item(self.course, self.coach.id)
        data = {'master_course_id': self.master_course_key_str}

        resp = self.client.post(self.list_url, data, format='json', HTTP_AUTHORIZATION=self.auth)
        self.expect_error(status.HTTP_403_FORBIDDEN, 'ccx_not_enabled_for_master_course', resp)
        self.course.enable_ccx = True
        self.mstore.update_item(self.course, self.coach.id)

        # case with deprecated  master_course_id
        with mock.patch('lms.djangoapps.courseware.courses.get_course_by_id', autospec=True) as mocked:
            mocked.return_value.id.deprecated = True
            resp = self.client.post(self.list_url, data, format='json', HTTP_AUTHORIZATION=self.auth)

        self.expect_error(status.HTTP_400_BAD_REQUEST, 'deprecated_master_course_id', resp)

    @ddt.data(
        (
            {},
            {
                'max_students_allowed': 'missing_field_max_students_allowed',
                'display_name': 'missing_field_display_name',
                'coach_email': 'missing_field_coach_email'
            },
        ),
        (
            {
                'max_students_allowed': 10,
                'display_name': 'CCX Title'
            },
            {
                'coach_email': 'missing_field_coach_email'
            },
        ),
        (
            {
                'max_students_allowed': None,
                'display_name': None,
                'coach_email': None
            },
            {
                'max_students_allowed': 'null_field_max_students_allowed',
                'display_name': 'null_field_display_name',
                'coach_email': 'null_field_coach_email'
            },
        ),
        (
            {
                'max_students_allowed': 10,
                'display_name': 'CCX Title',
                'coach_email': 'this is not an email@test.com'
            },
            {'coach_email': 'invalid_coach_email'},
        ),
        (
            {
                'max_students_allowed': 10,
                'display_name': '',
                'coach_email': 'email@test.com'
            },
            {'display_name': 'invalid_display_name'},
        ),
        (
            {
                'max_students_allowed': 'a',
                'display_name': 'CCX Title',
                'coach_email': 'email@test.com'
            },
            {'max_students_allowed': 'invalid_max_students_allowed'},
        ),
        (
            {
                'max_students_allowed': 10,
                'display_name': 'CCX Title',
                'coach_email': 'email@test.com',
                'course_modules': {'foo': 'bar'}
            },
            {'course_modules': 'invalid_course_module_list'},
        ),
        (
            {
                'max_students_allowed': 10,
                'display_name': 'CCX Title',
                'coach_email': 'email@test.com',
                'course_modules': 'block-v1:org.0+course_0+Run_0+type@chapter+block@chapter_1'
            },
            {'course_modules': 'invalid_course_module_list'},
        ),
        (
            {
                'max_students_allowed': 10,
                'display_name': 'CCX Title',
                'coach_email': 'email@test.com',
                'course_modules': ['foo', 'bar']
            },
            {'course_modules': 'invalid_course_module_keys'},
        )
    )
    @ddt.unpack
    def test_post_list_wrong_input_data(self, data, expected_errors):
        """
        Test for various post requests with wrong input data
        """
        # add the master_course_key_str to the request data
        data['master_course_id'] = self.master_course_key_str
        resp = self.client.post(self.list_url, data, format='json', HTTP_AUTHORIZATION=self.auth)
        self.expect_error_fields(expected_errors, resp)

    def test_post_list_coach_does_not_exist(self):
        """
        Specific test for the case when the input data is valid but the coach does not exist.
        """
        data = {
            'master_course_id': self.master_course_key_str,
            'max_students_allowed': 111,
            'display_name': 'CCX Title',
            'coach_email': 'inexisting_email@test.com'
        }
        resp = self.client.post(self.list_url, data, format='json', HTTP_AUTHORIZATION=self.auth)
        self.expect_error(status.HTTP_404_NOT_FOUND, 'coach_user_does_not_exist', resp)

    def test_post_list_wrong_modules(self):
        """
        Specific test for the case when the input data is valid but the
        course modules do not belong to the master course
        """
        data = {
            'master_course_id': self.master_course_key_str,
            'max_students_allowed': 111,
            'display_name': 'CCX Title',
            'coach_email': self.coach.email,
            'course_modules': [
                'block-v1:org.0+course_0+Run_0+type@chapter+block@chapter_foo',
                'block-v1:org.0+course_0+Run_0+type@chapter+block@chapter_bar'
            ]
        }
        resp = self.client.post(self.list_url, data, format='json', HTTP_AUTHORIZATION=self.auth)
        self.expect_error(status.HTTP_400_BAD_REQUEST, 'course_module_list_not_belonging_to_master_course', resp)

    def test_post_list_mixed_wrong_and_valid_modules(self):
        """
        Specific test for the case when the input data is valid but some of
        the course modules do not belong to the master course
        """
        modules = self.master_course_chapters[0:1] + ['block-v1:org.0+course_0+Run_0+type@chapter+block@chapter_foo']
        data = {
            'master_course_id': self.master_course_key_str,
            'max_students_allowed': 111,
            'display_name': 'CCX Title',
            'coach_email': self.coach.email,
            'course_modules': modules
        }
        resp = self.client.post(self.list_url, data, format='json', HTTP_AUTHORIZATION=self.auth)
        self.expect_error(status.HTTP_400_BAD_REQUEST, 'course_module_list_not_belonging_to_master_course', resp)

    def test_post_list(self):
        """
        Test the creation of a CCX
        """
        outbox = self.get_outbox()
        data = {
            'master_course_id': self.master_course_key_str,
            'max_students_allowed': 111,
            'display_name': 'CCX Test Title',
            'coach_email': self.coach.email,
            'course_modules': self.master_course_chapters[0:1]
        }
        resp = self.client.post(self.list_url, data, format='json', HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        # check if the response has at least the same data of the request
        for key, val in six.iteritems(data):
            self.assertEqual(resp.data.get(key), val)
        self.assertIn('ccx_course_id', resp.data)
        # check that the new CCX actually exists
        course_key = CourseKey.from_string(resp.data.get('ccx_course_id'))
        ccx_course = CustomCourseForEdX.objects.get(pk=course_key.ccx)
        self.assertEqual(
            six.text_type(CCXLocator.from_course_locator(ccx_course.course.id, ccx_course.id)),
            resp.data.get('ccx_course_id')
        )
        # check that the coach user has coach role on the master course
        coach_role_on_master_course = CourseCcxCoachRole(self.master_course_key)
        self.assertTrue(coach_role_on_master_course.has_user(self.coach))
        # check that the coach has been enrolled in the ccx
        ccx_course_object = courses.get_course_by_id(course_key)
        self.assertTrue(
            CourseEnrollment.objects.filter(course_id=ccx_course_object.id, user=self.coach).exists()
        )
        # check that an email has been sent to the coach
        self.assertEqual(len(outbox), 1)
        self.assertIn(self.coach.email, outbox[0].recipients())

    @ddt.data(
        True,
        False
    )
    def test_post_list_on_active_state(self, user_is_active):
        """
        Test the creation of a CCX on user's active states.
        """
        self.app_user.is_active = user_is_active
        self.app_user.save()

        data = {
            'master_course_id': self.master_course_key_str,
            'max_students_allowed': 111,
            'display_name': 'CCX Test Title',
            'coach_email': self.coach.email,
            'course_modules': self.master_course_chapters[0:1]
        }
        resp = self.client.post(self.list_url, data, format='json', HTTP_AUTHORIZATION=self.auth)

        if not user_is_active:
            self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        else:
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_post_list_duplicated_modules(self):
        """
        Test the creation of a CCX, but with duplicated modules
        """
        chapters = self.master_course_chapters[0:1]
        duplicated_chapters = chapters * 3
        data = {
            'master_course_id': self.master_course_key_str,
            'max_students_allowed': 111,
            'display_name': 'CCX Test Title',
            'coach_email': self.coach.email,
            'course_modules': duplicated_chapters
        }
        resp = self.client.post(self.list_url, data, format='json', HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data.get('course_modules'), chapters)

    def test_post_list_staff_master_course_in_ccx(self):
        """
        Specific test to check that the staff and instructor of the master
        course are assigned to the CCX.
        """
        outbox = self.get_outbox()
        data = {
            'master_course_id': self.master_course_key_str,
            'max_students_allowed': 111,
            'display_name': 'CCX Test Title',
            'coach_email': self.coach.email
        }
        resp = self.client.post(self.list_url, data, format='json', HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        # check that only one email has been sent and it is to to the coach
        self.assertEqual(len(outbox), 1)
        self.assertIn(self.coach.email, outbox[0].recipients())

        list_staff_master_course = list_with_level(self.course, 'staff')
        list_instructor_master_course = list_with_level(self.course, 'instructor')
        course_key = CourseKey.from_string(resp.data.get('ccx_course_id'))
        with ccx_course_cm(course_key) as course_ccx:
            list_staff_ccx_course = list_with_level(course_ccx, 'staff')
            list_instructor_ccx_course = list_with_level(course_ccx, 'instructor')

        # The "Coach" in the parent course becomes "Staff" on the CCX, so the CCX should have 1 "Staff"
        # user more than the parent course
        self.assertEqual(len(list_staff_master_course) + 1, len(list_staff_ccx_course))
        # Make sure all of the existing course staff are passed to the CCX
        for course_user in list_staff_master_course:
            self.assertIn(course_user, list_staff_ccx_course)
        # Make sure the "Coach" on the parent course is "Staff" on the CCX
        self.assertIn(self.coach, list_staff_ccx_course)
        self.assertEqual(len(list_instructor_master_course), len(list_instructor_ccx_course))
        for course_user, ccx_user in zip(sorted(list_instructor_master_course), sorted(list_instructor_ccx_course)):
            self.assertEqual(course_user, ccx_user)


@ddt.ddt
class CcxDetailTest(CcxRestApiTest):
    """
    Test for the CCX REST APIs
    """
    ENABLED_SIGNALS = ['course_published']

    def setUp(self):
        """
        Set up tests
        """
        super(CcxDetailTest, self).setUp()
        self.make_coach()
        # create a ccx
        self.ccx = self.make_ccx(max_students_allowed=123)
        self.ccx_key = CCXLocator.from_course_locator(self.ccx.course.id, self.ccx.id)
        self.ccx_key_str = six.text_type(self.ccx_key)
        self.detail_url = reverse('ccx_api:v0:ccx:detail', kwargs={'ccx_course_id': self.ccx_key_str})

    def make_ccx(self, max_students_allowed=200):
        """
        Overridden method to replicate (part of) the actual
        creation of ccx courses
        """
        ccx = super(CcxDetailTest, self).make_ccx(max_students_allowed=max_students_allowed)
        ccx.structure_json = json.dumps(self.master_course_chapters)
        ccx.save()

        override_field_for_ccx(ccx, self.course, 'start', now())
        override_field_for_ccx(ccx, self.course, 'due', None)
        # Hide anything that can show up in the schedule
        hidden = 'visible_to_staff_only'
        for chapter in self.course.get_children():
            override_field_for_ccx(ccx, chapter, hidden, True)
            for sequential in chapter.get_children():
                override_field_for_ccx(ccx, sequential, hidden, True)
                for vertical in sequential.get_children():
                    override_field_for_ccx(ccx, vertical, hidden, True)
        # enroll the coach in the CCX
        ccx_course_key = CCXLocator.from_course_locator(self.course.id, ccx.id)
        email_params = get_email_params(
            self.course,
            auto_enroll=True,
            course_key=ccx_course_key,
            display_name=ccx.display_name
        )
        enroll_email(
            course_id=ccx_course_key,
            student_email=self.coach.email,
            auto_enroll=True,
            email_students=False,
            email_params=email_params,
        )
        return ccx

    def test_authorization(self):
        """
        Test that only the right token is authorized
        """
        auth_list = [
            "Wrong token-type-obviously",
            "Bearer wrong token format",
            "Bearer wrong-token",
            "Bearer",
            "Bearer hfbhfbfwq398248fnid939rh3489fh39nd4m34r9"  # made up token
        ]
        # all the auths in the list fail to authorize
        for auth in auth_list:
            resp = self.client.get(self.detail_url, {}, HTTP_AUTHORIZATION=auth)
            self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        resp = self.client.get(self.detail_url, {}, HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_authorization_no_oauth_staff(self):
        """
        Check authorization for staff users logged in without oauth
        """
        # create a staff user
        staff_user = User.objects.create_user('test_staff_user', 'test_staff_user@openedx.org', 'test')
        # add staff role to the staff user
        CourseStaffRole(self.master_course_key).add_users(staff_user)

        data = {'display_name': 'CCX Title'}
        # the staff user can perform the request
        self.client.login(username=staff_user.username, password=USER_PASSWORD)
        resp = self.client.get(self.detail_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        resp = self.client.patch(self.detail_url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_authorization_no_oauth_instructor(self):
        """
        Check authorization for users logged in without oauth
        """
        # create an instructor user
        instructor_user = User.objects.create_user('test_instructor_user', 'test_instructor_user@openedx.org', 'test')
        # add instructor role to the instructor user
        CourseInstructorRole(self.master_course_key).add_users(instructor_user)

        data = {'display_name': 'CCX Title'}
        # the instructor user can perform the request
        self.client.login(username=instructor_user.username, password=USER_PASSWORD)
        resp = self.client.get(self.detail_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        resp = self.client.patch(self.detail_url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_authorization_no_oauth_other_coach(self):
        """
        Check authorization for other coach users logged in without oauth
        """
        # create an coach user
        coach_user = User.objects.create_user('test_coach_user', 'test_coach_user@openedx.org', 'test')
        # add coach role to the coach user
        CourseCcxCoachRole(self.master_course_key).add_users(coach_user)

        data = {'display_name': 'CCX Title'}
        # the coach user cannot perform the request: this type of user can only get her own CCX
        self.client.login(username=coach_user.username, password=USER_PASSWORD)
        resp = self.client.get(self.detail_url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        resp = self.client.patch(self.detail_url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_authorization_no_oauth_ccx_coach(self):
        """
        Check authorization for ccx coach users logged in without oauth
        """
        data = {'display_name': 'CCX Title'}
        # the coach owner of the CCX can perform the request only if it is a get
        self.client.login(username=self.coach.username, password=USER_PASSWORD)
        resp = self.client.get(self.detail_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        resp = self.client.patch(self.detail_url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_resolve_get_detail(self):
        """
        Test for the ccx detail view resolver. This is needed because it is assumed
        that only an URL with a valid course id string can reach the detail view.
        """
        # get the base url from the valid one to build invalid urls
        base_url = '{0}/'.format(self.detail_url.rsplit('/', 1)[0])
        # this url should be the same of the ccx list view
        resolver = resolve(base_url)
        self.assertEqual(views.CCXListView.__name__, resolver.func.__name__)
        self.assertEqual(views.CCXListView.__module__, resolver.func.__module__)
        # invalid urls
        for invalid_ccx_id in ('foo', 'ccx-v1:org.0', 'ccx-v1:org.0+course_0'):
            with self.assertRaises(Resolver404):
                resolve('{0}{1}'.format(base_url, invalid_ccx_id))
        # the following course ID works even if it is not a CCX valid course id (the regex matches course ID strings)
        resolver = resolve('{0}{1}'.format(base_url, 'ccx-v1:org.0+course_0+Run_0'))
        self.assertEqual(views.CCXDetailView.__name__, resolver.func.__name__)
        self.assertEqual(views.CCXDetailView.__module__, resolver.func.__module__)
        # and of course a valid ccx course id
        resolver = resolve('{0}{1}'.format(base_url, self.ccx_key_str))
        self.assertEqual(views.CCXDetailView.__name__, resolver.func.__name__)
        self.assertEqual(views.CCXDetailView.__module__, resolver.func.__module__)

    @ddt.data(
        'get',
        'delete',
        'patch',
    )
    def test_detail_wrong_ccx(self, http_method):
        """
        Test for different methods for detail of a ccx course.
        All check the validity of the ccx course id
        """
        client_request = getattr(self.client, http_method)
        # get a detail url with a master_course id string
        mock_class_str = 'openedx.core.lib.api.permissions.IsCourseStaffInstructor.has_object_permission'
        url = reverse('ccx_api:v0:ccx:detail', kwargs={'ccx_course_id': self.master_course_key_str})

        # the permission class will give a 403 error because will not find the CCX
        resp = client_request(url, {}, HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # bypassing the permission class we get another kind of error
        with mock.patch(mock_class_str, autospec=True) as mocked_perm_class:
            mocked_perm_class.return_value = True
            resp = client_request(url, {}, HTTP_AUTHORIZATION=self.auth)
            self.expect_error(status.HTTP_400_BAD_REQUEST, 'course_id_not_valid_ccx_id', resp)

        # use an non existing ccx id
        url = reverse('ccx_api:v0:ccx:detail', kwargs={'ccx_course_id': 'ccx-v1:foo.0+course_bar_0+Run_0+ccx@1'})
        # the permission class will give a 403 error because will not find the CCX
        resp = client_request(url, {}, HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # bypassing the permission class we get another kind of error
        with mock.patch(mock_class_str, autospec=True) as mocked_perm_class:
            mocked_perm_class.return_value = True
            resp = client_request(url, {}, HTTP_AUTHORIZATION=self.auth)
            self.expect_error(status.HTTP_404_NOT_FOUND, 'ccx_course_id_does_not_exist', resp)

        # get a valid ccx key and add few 0s to get a non existing ccx for a valid course
        ccx_key_str = '{0}000000'.format(self.ccx_key_str)
        url = reverse('ccx_api:v0:ccx:detail', kwargs={'ccx_course_id': ccx_key_str})
        # the permission class will give a 403 error because will not find the CCX
        resp = client_request(url, {}, HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # bypassing the permission class we get another kind of error
        with mock.patch(mock_class_str, autospec=True) as mocked_perm_class:
            mocked_perm_class.return_value = True
            resp = client_request(url, {}, HTTP_AUTHORIZATION=self.auth)
            self.expect_error(status.HTTP_404_NOT_FOUND, 'ccx_course_id_does_not_exist', resp)

    def test_get_detail(self):
        """
        Test for getting detail of a ccx course
        """
        resp = self.client.get(self.detail_url, {}, HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data.get('ccx_course_id'), self.ccx_key_str)
        self.assertEqual(resp.data.get('display_name'), self.ccx.display_name)
        self.assertEqual(
            resp.data.get('max_students_allowed'),
            self.ccx.max_student_enrollments_allowed
        )
        self.assertEqual(resp.data.get('coach_email'), self.ccx.coach.email)
        self.assertEqual(resp.data.get('master_course_id'), six.text_type(self.ccx.course_id))
        six.assertCountEqual(self, resp.data.get('course_modules'), self.master_course_chapters)

    def test_delete_detail(self):
        """
        Test for deleting a ccx course
        """
        # check that there are overrides
        self.assertGreater(CcxFieldOverride.objects.filter(ccx=self.ccx).count(), 0)
        self.assertGreater(CourseEnrollment.objects.filter(course_id=self.ccx_key).count(), 0)
        resp = self.client.delete(self.detail_url, {}, HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIsNone(resp.data)
        # the CCX does not exist any more
        with self.assertRaises(CustomCourseForEdX.DoesNotExist):
            CustomCourseForEdX.objects.get(id=self.ccx.id)
        # check that there are no overrides
        self.assertEqual(CcxFieldOverride.objects.filter(ccx=self.ccx).count(), 0)
        self.assertEqual(CourseEnrollment.objects.filter(course_id=self.ccx_key).count(), 0)

    def test_patch_detail_change_master_course(self):
        """
        Test to patch a ccx course to change a master course
        """
        data = {
            'master_course_id': 'changed_course_id'
        }
        resp = self.client.patch(self.detail_url, data, format='json', HTTP_AUTHORIZATION=self.auth)
        self.expect_error(status.HTTP_403_FORBIDDEN, 'master_course_id_change_not_allowed', resp)

    @ddt.data(
        (
            {
                'max_students_allowed': None,
                'display_name': None,
                'coach_email': None
            },
            {
                'max_students_allowed': 'null_field_max_students_allowed',
                'display_name': 'null_field_display_name',
                'coach_email': 'null_field_coach_email'
            },
        ),
        (
            {'coach_email': 'this is not an email@test.com'},
            {'coach_email': 'invalid_coach_email'},
        ),
        (
            {'display_name': ''},
            {'display_name': 'invalid_display_name'},
        ),
        (
            {'max_students_allowed': 'a'},
            {'max_students_allowed': 'invalid_max_students_allowed'},
        ),
        (
            {'course_modules': {'foo': 'bar'}},
            {'course_modules': 'invalid_course_module_list'},
        ),
        (
            {'course_modules': 'block-v1:org.0+course_0+Run_0+type@chapter+block@chapter_1'},
            {'course_modules': 'invalid_course_module_list'},
        ),
        (
            {'course_modules': ['foo', 'bar']},
            {'course_modules': 'invalid_course_module_keys'},
        ),
    )
    @ddt.unpack
    def test_patch_detail_wrong_input_data(self, data, expected_errors):
        """
        Test for different wrong inputs for the patch method
        """
        resp = self.client.patch(self.detail_url, data, format='json', HTTP_AUTHORIZATION=self.auth)
        self.expect_error_fields(expected_errors, resp)

    def test_empty_patch(self):
        """
        An empty patch does not modify anything
        """
        display_name = self.ccx.display_name
        max_students_allowed = self.ccx.max_student_enrollments_allowed
        coach_email = self.ccx.coach.email
        ccx_structure = self.ccx.structure
        resp = self.client.patch(self.detail_url, {}, format='json', HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        ccx = CustomCourseForEdX.objects.get(id=self.ccx.id)
        self.assertEqual(display_name, ccx.display_name)
        self.assertEqual(max_students_allowed, ccx.max_student_enrollments_allowed)
        self.assertEqual(coach_email, ccx.coach.email)
        self.assertEqual(ccx_structure, ccx.structure)

    def test_patch_detail_coach_does_not_exist(self):
        """
        Specific test for the case when the input data is valid but the coach does not exist.
        """
        data = {
            'max_students_allowed': 111,
            'display_name': 'CCX Title',
            'coach_email': 'inexisting_email@test.com'
        }
        resp = self.client.patch(self.detail_url, data, format='json', HTTP_AUTHORIZATION=self.auth)
        self.expect_error(status.HTTP_404_NOT_FOUND, 'coach_user_does_not_exist', resp)

    def test_patch_detail_wrong_modules(self):
        """
        Specific test for the case when the input data is valid but the
        course modules do not belong to the master course
        """
        data = {
            'course_modules': [
                'block-v1:org.0+course_0+Run_0+type@chapter+block@chapter_foo',
                'block-v1:org.0+course_0+Run_0+type@chapter+block@chapter_bar'
            ]
        }
        resp = self.client.patch(self.detail_url, data, format='json', HTTP_AUTHORIZATION=self.auth)
        self.expect_error(status.HTTP_400_BAD_REQUEST, 'course_module_list_not_belonging_to_master_course', resp)

    def test_patch_detail_mixed_wrong_and_valid_modules(self):
        """
        Specific test for the case when the input data is valid but some of
        the course modules do not belong to the master course
        """
        modules = self.master_course_chapters[0:1] + ['block-v1:org.0+course_0+Run_0+type@chapter+block@chapter_foo']
        data = {
            'course_modules': modules
        }
        resp = self.client.patch(self.detail_url, data, format='json', HTTP_AUTHORIZATION=self.auth)
        self.expect_error(status.HTTP_400_BAD_REQUEST, 'course_module_list_not_belonging_to_master_course', resp)

    def test_patch_detail(self):
        """
        Test for successful patch
        """
        outbox = self.get_outbox()
        # create a new coach
        new_coach = AdminFactory.create()
        data = {
            'max_students_allowed': 111,
            'display_name': 'CCX Title',
            'coach_email': new_coach.email
        }
        resp = self.client.patch(self.detail_url, data, format='json', HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        ccx_from_db = CustomCourseForEdX.objects.get(id=self.ccx.id)
        self.assertEqual(ccx_from_db.max_student_enrollments_allowed, data['max_students_allowed'])
        self.assertEqual(ccx_from_db.display_name, data['display_name'])
        self.assertEqual(ccx_from_db.coach.email, data['coach_email'])
        # check that the coach user has coach role on the master course
        coach_role_on_master_course = CourseCcxCoachRole(self.master_course_key)
        self.assertTrue(coach_role_on_master_course.has_user(new_coach))
        # check that the coach has been enrolled in the ccx
        ccx_course_object = courses.get_course_by_id(self.ccx_key)
        self.assertTrue(
            CourseEnrollment.objects.filter(course_id=ccx_course_object.id, user=new_coach).exists()
        )
        # check that an email has been sent to the coach
        self.assertEqual(len(outbox), 1)
        self.assertIn(new_coach.email, outbox[0].recipients())

    def test_patch_detail_modules(self):
        """
        Specific test for successful patch of the course modules
        """
        data = {'course_modules': self.master_course_chapters[0:1]}
        resp = self.client.patch(self.detail_url, data, format='json', HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        ccx_from_db = CustomCourseForEdX.objects.get(id=self.ccx.id)
        six.assertCountEqual(self, ccx_from_db.structure, data['course_modules'])

        data = {'course_modules': []}
        resp = self.client.patch(self.detail_url, data, format='json', HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        ccx_from_db = CustomCourseForEdX.objects.get(id=self.ccx.id)
        six.assertCountEqual(self, ccx_from_db.structure, [])

        data = {'course_modules': self.master_course_chapters}
        resp = self.client.patch(self.detail_url, data, format='json', HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        ccx_from_db = CustomCourseForEdX.objects.get(id=self.ccx.id)
        six.assertCountEqual(self, ccx_from_db.structure, self.master_course_chapters)

        data = {'course_modules': None}
        resp = self.client.patch(self.detail_url, data, format='json', HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        ccx_from_db = CustomCourseForEdX.objects.get(id=self.ccx.id)
        self.assertEqual(ccx_from_db.structure, None)

        chapters = self.master_course_chapters[0:1]
        data = {'course_modules': chapters * 3}
        resp = self.client.patch(self.detail_url, data, format='json', HTTP_AUTHORIZATION=self.auth)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        ccx_from_db = CustomCourseForEdX.objects.get(id=self.ccx.id)
        six.assertCountEqual(self, ccx_from_db.structure, chapters)

    @ddt.data(
        True,
        False
    )
    def test_patch_user_on_active_state(self, user_is_active):
        """
        Test patch ccx course on user's active state.
        """
        self.app_user.is_active = user_is_active
        self.app_user.save()

        chapters = self.master_course_chapters[0:1]
        data = {'course_modules': chapters * 3}
        resp = self.client.patch(self.detail_url, data, format='json', HTTP_AUTHORIZATION=self.auth)
        if not user_is_active:
            self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        else:
            self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
            ccx_from_db = CustomCourseForEdX.objects.get(id=self.ccx.id)
            six.assertCountEqual(self, ccx_from_db.structure, chapters)

    @ddt.data(
        True,
        False
    )
    def test_delete_detail_on_active_state(self, user_is_active):
        """
        Test for deleting a ccx course on user's active state.
        """
        self.app_user.is_active = user_is_active
        self.app_user.save()

        # check that there are overrides
        self.assertGreater(CcxFieldOverride.objects.filter(ccx=self.ccx).count(), 0)
        self.assertGreater(CourseEnrollment.objects.filter(course_id=self.ccx_key).count(), 0)
        resp = self.client.delete(self.detail_url, {}, HTTP_AUTHORIZATION=self.auth)

        if not user_is_active:
            self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        else:
            self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
            self.assertIsNone(resp.data)
            # the CCX does not exist any more
            with self.assertRaises(CustomCourseForEdX.DoesNotExist):
                CustomCourseForEdX.objects.get(id=self.ccx.id)
            # check that there are no overrides
            self.assertEqual(CcxFieldOverride.objects.filter(ccx=self.ccx).count(), 0)
            self.assertEqual(CourseEnrollment.objects.filter(course_id=self.ccx_key).count(), 0)
