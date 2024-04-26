"""
Tests for course_info
"""


import ddt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from django.urls import reverse
from edx_toggles.toggles.testutils import override_waffle_flag
from milestones.tests.utils import MilestonesTestCaseMixin
from mock import patch
from rest_framework import status

from common.djangoapps.student.tests.factories import UserFactory  # pylint: disable=unused-import
from common.djangoapps.util.course import get_link_for_about_page
from lms.djangoapps.mobile_api.testutils import MobileAPITestCase, MobileAuthTestMixin, MobileCourseAccessTestMixin
from lms.djangoapps.mobile_api.utils import API_V1, API_V05
from lms.djangoapps.mobile_api.course_info.views import BlocksInfoInCourseView
from lms.djangoapps.course_api.blocks.tests.test_views import TestBlocksInCourseView
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.features.course_experience import ENABLE_COURSE_GOALS
from xmodule.html_block import CourseInfoBlock  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore import ModuleStoreEnum  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.django import modulestore  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.xml_importer import import_course_from_xml  # lint-amnesty, pylint: disable=wrong-import-order


User = get_user_model()


@ddt.ddt
class TestUpdates(MobileAPITestCase, MobileAuthTestMixin, MobileCourseAccessTestMixin, MilestonesTestCaseMixin):
    """
    Tests for /api/mobile/{api_version}/course_info/{course_id}/updates
    """
    REVERSE_INFO = {'name': 'course-updates-list', 'params': ['course_id', 'api_version']}

    def verify_success(self, response):
        super().verify_success(response)
        assert response.data == []

    @ddt.data(
        (True, API_V05),
        (True, API_V1),
        (False, API_V05),
        (False, API_V1),
    )
    @ddt.unpack
    def test_updates(self, new_format, api_version):
        """
        Tests updates endpoint with /static in the content.
        Tests both new updates format (using "items") and old format (using "data").
        """
        self.login_and_enroll()

        # create course Updates item in modulestore
        updates_usage_key = self.course.id.make_usage_key('course_info', 'updates')
        course_updates = modulestore().create_item(
            self.user.id,
            updates_usage_key.course_key,
            updates_usage_key.block_type,
            block_id=updates_usage_key.block_id
        )

        # store content in Updates item (either new or old format)
        num_updates = 3
        if new_format:
            for num in range(1, num_updates + 1):
                course_updates.items.append(
                    {
                        "id": num,
                        "date": "Date" + str(num),
                        "content": "<a href=\"/static/\">Update" + str(num) + "</a>",
                        "status": CourseInfoBlock.STATUS_VISIBLE
                    }
                )
        else:
            update_data = ""
            # old format stores the updates with the newest first
            for num in range(num_updates, 0, -1):
                update_data += "<li><h2>Date" + str(num) + "</h2><a href=\"/static/\">Update" + str(num) + "</a></li>"
            course_updates.data = "<ol>" + update_data + "</ol>"
        modulestore().update_item(course_updates, self.user.id)

        # call API
        response = self.api_response(api_version=api_version)

        # verify static URLs are replaced in the content returned by the API
        self.assertNotContains(response, "\"/static/")

        # verify static URLs remain in the underlying content
        underlying_updates = modulestore().get_item(updates_usage_key)
        underlying_content = underlying_updates.items[0]['content'] if new_format else underlying_updates.data
        assert '"/static/' in underlying_content

        # verify content and sort order of updates (most recent first)
        for num in range(1, num_updates + 1):
            update_data = response.data[num_updates - num]
            assert num == update_data['id']
            assert 'Date' + str(num) == update_data['date']
            assert 'Update' + str(num) in update_data['content']


@ddt.ddt
class TestHandouts(MobileAPITestCase, MobileAuthTestMixin, MobileCourseAccessTestMixin, MilestonesTestCaseMixin):
    """
    Tests for /api/mobile/{api_version}/course_info/{course_id}/handouts
    """
    REVERSE_INFO = {'name': 'course-handouts-list', 'params': ['course_id', 'api_version']}

    @ddt.data(API_V05, API_V1)
    def test_handouts(self, api_version):
        self.add_mobile_available_toy_course()
        response = self.api_response(expected_response_code=200, api_version=api_version)
        assert 'Sample' in response.data['handouts_html']

    @ddt.data(API_V05, API_V1)
    def test_no_handouts(self, api_version):
        self.add_mobile_available_toy_course()

        # delete handouts in course
        handouts_usage_key = self.course.id.make_usage_key('course_info', 'handouts')
        with self.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred, self.course.id):
            self.store.delete_item(handouts_usage_key, self.user.id)

        response = self.api_response(expected_response_code=200, api_version=api_version)
        assert response.data['handouts_html'] is None

    @ddt.data(API_V05, API_V1)
    def test_empty_handouts(self, api_version):
        self.add_mobile_available_toy_course()

        # set handouts to empty tags
        handouts_usage_key = self.course.id.make_usage_key('course_info', 'handouts')
        underlying_handouts = self.store.get_item(handouts_usage_key)
        underlying_handouts.data = "<ol></ol>"
        self.store.update_item(underlying_handouts, self.user.id)
        response = self.api_response(expected_response_code=200, api_version=api_version)
        assert response.data['handouts_html'] is None

    @ddt.data(API_V05, API_V1)
    def test_handouts_static_rewrites(self, api_version):
        self.add_mobile_available_toy_course()

        # check that we start with relative static assets
        handouts_usage_key = self.course.id.make_usage_key('course_info', 'handouts')
        underlying_handouts = self.store.get_item(handouts_usage_key)
        assert "'/static/" in underlying_handouts.data

        # but shouldn't finish with any
        response = self.api_response(api_version=api_version)
        assert "'/static/" not in response.data['handouts_html']

    @ddt.data(API_V05, API_V1)
    def test_jump_to_id_handout_href(self, api_version):
        self.add_mobile_available_toy_course()

        # check that we start with relative static assets
        handouts_usage_key = self.course.id.make_usage_key('course_info', 'handouts')
        underlying_handouts = self.store.get_item(handouts_usage_key)
        underlying_handouts.data = "<a href=\"/jump_to_id/identifier\">Intracourse Link</a>"
        self.store.update_item(underlying_handouts, self.user.id)

        # but shouldn't finish with any
        response = self.api_response(api_version=api_version)
        assert f'/courses/{self.course.id}/jump_to_id/' in response.data['handouts_html']

    @ddt.data(API_V05, API_V1)
    def test_course_url_handout_href(self, api_version):
        self.add_mobile_available_toy_course()

        # check that we start with relative static assets
        handouts_usage_key = self.course.id.make_usage_key('course_info', 'handouts')
        underlying_handouts = self.store.get_item(handouts_usage_key)
        underlying_handouts.data = "<a href=\"/course/identifier\">Linked Content</a>"
        self.store.update_item(underlying_handouts, self.user.id)

        # but shouldn't finish with any
        response = self.api_response(api_version=api_version)
        assert f'/courses/{self.course.id}/' in response.data['handouts_html']

    def add_mobile_available_toy_course(self):
        """ use toy course with handouts, and make it mobile_available """
        course_items = import_course_from_xml(
            self.store, self.user.id,
            settings.COMMON_TEST_DATA_ROOT, ['toy'],
            create_if_not_present=True
        )
        self.course = course_items[0]
        self.course.mobile_available = True
        self.store.update_item(self.course, self.user.id)
        self.login_and_enroll()


@override_waffle_flag(ENABLE_COURSE_GOALS, active=True)
class TestCourseGoalsUserActivityAPI(MobileAPITestCase, SharedModuleStoreTestCase):
    """
    Testing the Course Goals User Activity API.
    """

    def setUp(self):
        super().setUp()
        self.apiUrl = reverse('record_user_activity', args=['v1'])
        self.login_and_enroll()

    def test_record_activity(self):
        '''
        Test the happy path of recording user activity
        '''
        post_data = {
            'course_key': self.course.id,
            'user_id': self.user.id,
        }

        response = self.client.post(self.apiUrl, post_data)
        assert response.status_code == 200

    def test_invalid_parameters(self):
        '''
        Ensure that we check that parameters meet the requirements
        and return a 400 otherwise.
        '''
        post_data = {
            'course_key': self.course.id,
        }

        response = self.client.post(self.apiUrl, post_data)
        assert response.status_code == 400

        post_data = {
            'user_id': self.user.id,
        }

        response = self.client.post(self.apiUrl, post_data)
        assert response.status_code == 400

        post_data = {
            'user_id': self.user.id,
            'course_key': 'invalidcoursekey',
        }

        response = self.client.post(self.apiUrl, post_data)
        assert response.status_code == 400

    @override_waffle_flag(ENABLE_COURSE_GOALS, active=False)
    @patch('lms.djangoapps.mobile_api.course_info.views.log')
    def test_flag_disabled(self, mock_logger):
        '''
        Test the API behavior when the goals flag is disabled
        '''
        post_data = {
            'user_id': self.user.id,
            'course_key': self.course.id,
        }

        response = self.client.post(self.apiUrl, post_data)
        assert response.status_code == 200
        mock_logger.warning.assert_called_with(
            'For this mobile request, user activity is not enabled for this user {} and course {}'.format(
                str(self.user.id), str(self.course.id))
        )


@ddt.ddt
class TestBlocksInfoInCourseView(TestBlocksInCourseView, MilestonesTestCaseMixin):  # lint-amnesty, pylint: disable=test-inherits-tests
    """
    Test class for BlocksInfoInCourseView
    """

    def setUp(self):
        super().setUp()
        self.url = reverse('blocks_info_in_course', kwargs={
            'api_version': 'v3',
        })
        self.request = RequestFactory().get(self.url)
        self.student_user = UserFactory.create(username="student_user")

    @ddt.data(
        ('anonymous', None, None),
        ('staff', 'student_user', 'student_user'),
        ('student', 'student_user', 'student_user'),
        ('student', None, 'student_user'),
        ('student', 'other_student', None),
    )
    @ddt.unpack
    @patch('lms.djangoapps.mobile_api.course_info.views.User.objects.get')
    def test_get_requested_user(self, user_role, username, expected_username, mock_get):
        """
        Test get_requested_user utility from the BlocksInfoInCourseView.

        Parameters:
        user_role: type of the user that making a request.
        username: username query parameter from the request.
        expected_username: username of the returned user.
        """
        if user_role == 'anonymous':
            request_user = AnonymousUser()
        elif user_role == 'staff':
            request_user = self.admin_user
        elif user_role == 'student':
            request_user = self.student_user

        self.request.user = request_user

        if expected_username == 'student_user':
            mock_user = self.student_user
            mock_get.return_value = mock_user

        result_user = BlocksInfoInCourseView().get_requested_user(self.request.user, username)
        if expected_username:
            self.assertEqual(result_user.username, expected_username)
            if username and request_user.username != username:
                mock_get.assert_called_with(username=username)
        else:
            self.assertIsNone(result_user)

    @ddt.data(
        ({'is_downloadable': True, 'download_url': 'https://test_certificate_url'},
         {'url': 'https://test_certificate_url'}),
        ({'is_downloadable': False}, {}),
    )
    @ddt.unpack
    @patch('lms.djangoapps.mobile_api.course_info.views.certificate_downloadable_status')
    def test_get_certificate(self, certificate_status_return, expected_output, mock_certificate_status):
        """
        Test get_certificate utility from the BlocksInfoInCourseView.

        Parameters:
        certificate_status_return: returned value of the mocked certificate_downloadable_status function.
        expected_output: return_value of the get_certificate function with specified mock return_value.
        """
        mock_certificate_status.return_value = certificate_status_return
        self.request.user = self.user

        certificate_info = BlocksInfoInCourseView().get_certificate(
            self.request, self.user, 'course-v1:Test+T101+2021_T1'
        )
        self.assertEqual(certificate_info, expected_output)

    @patch('lms.djangoapps.mobile_api.course_info.views.certificate_downloadable_status')
    def test_additional_info_response(self, mock_certificate_downloadable_status):
        certificate_url = 'https://test_certificate_url'
        mock_certificate_downloadable_status.return_value = {
            'is_downloadable': True,
            'download_url': certificate_url,
        }

        expected_image_urls = {
            'image':
                {
                    'large': '/asset-v1:edX+toy+2012_Fall+type@asset+block@just_a_test.jpg',
                    'raw': '/asset-v1:edX+toy+2012_Fall+type@asset+block@just_a_test.jpg',
                    'small': '/asset-v1:edX+toy+2012_Fall+type@asset+block@just_a_test.jpg'
                }
        }

        response = self.verify_response(url=self.url)

        assert response.status_code == 200
        assert response.data['id'] == str(self.course.id)
        assert response.data['name'] == self.course.display_name
        assert response.data['number'] == self.course.display_number_with_default
        assert response.data['org'] == self.course.display_org_with_default
        assert response.data['start'] == self.course.start.strftime('%Y-%m-%dT%H:%M:%SZ')
        assert response.data['start_display'] == 'July 17, 2015'
        assert response.data['start_type'] == 'timestamp'
        assert response.data['end'] == self.course.end
        assert response.data['media'] == expected_image_urls
        assert response.data['certificate'] == {'url': certificate_url}
        assert response.data['is_self_paced'] is False
        mock_certificate_downloadable_status.assert_called_once()

    def test_course_access_details(self):
        response = self.verify_response(url=self.url)

        expected_course_access_details = {
            'has_unmet_prerequisites': False,
            'is_too_early': False,
            'is_staff': False,
            'audit_access_expires': None,
            'courseware_access': {
                'has_access': True,
                'error_code': None,
                'developer_message': None,
                'user_message': None,
                'additional_context_user_message': None,
                'user_fragment': None
            }
        }

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.data['course_access_details'], expected_course_access_details)

    def test_course_sharing_utm_parameters(self):
        response = self.verify_response(url=self.url)

        expected_course_sharing_utm_parameters = {
            'facebook': 'utm_medium=social&utm_campaign=social-sharing-db&utm_source=facebook',
            'twitter': 'utm_medium=social&utm_campaign=social-sharing-db&utm_source=twitter'
        }

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.data['course_sharing_utm_parameters'], expected_course_sharing_utm_parameters)

    def test_course_about_url(self):
        response = self.verify_response(url=self.url)

        course_overview = CourseOverview.objects.get(id=self.course.course_id)
        expected_course_about_link = get_link_for_about_page(course_overview)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['course_about'], expected_course_about_link)

    def test_course_modes(self):
        response = self.verify_response(url=self.url)

        expected_course_modes = [{'slug': 'audit', 'sku': None, 'android_sku': None, 'ios_sku': None, 'min_price': 0}]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertListEqual(response.data['course_modes'], expected_course_modes)
