"""
Tests for course_info
"""


import ddt
from django.conf import settings
from django.urls import reverse
from edx_toggles.toggles.testutils import override_waffle_flag
from milestones.tests.utils import MilestonesTestCaseMixin
from mock import patch
from rest_framework.test import APIClient  # pylint: disable=unused-import

from common.djangoapps.student.models import CourseEnrollment  # pylint: disable=unused-import
from common.djangoapps.student.tests.factories import UserFactory  # pylint: disable=unused-import
from lms.djangoapps.mobile_api.testutils import MobileAPITestCase, MobileAuthTestMixin, MobileCourseAccessTestMixin
from lms.djangoapps.mobile_api.utils import API_V1, API_V05
from openedx.features.course_experience import ENABLE_COURSE_GOALS
from xmodule.html_block import CourseInfoBlock  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore import ModuleStoreEnum  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.django import modulestore  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.tests.factories import CourseFactory  # lint-amnesty, pylint: disable=unused-import, wrong-import-order
from xmodule.modulestore.xml_importer import import_course_from_xml  # lint-amnesty, pylint: disable=wrong-import-order


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
