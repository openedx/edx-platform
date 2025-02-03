"""
Unit tests for course import and export Celery tasks
"""
import asyncio
import copy
import json
import logging
import pprint
from unittest import mock
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

import pytest as pytest
from django.conf import settings
from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user
from django.test import TestCase
from django.test.utils import override_settings
from edx_toggles.toggles.testutils import override_waffle_flag
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import CourseLocator
from organizations.models import OrganizationCourse
from organizations.tests.factories import OrganizationFactory
from user_tasks.models import UserTaskArtifact, UserTaskStatus

logging = logging.getLogger(__name__)

from ..tasks import (
    export_olx,
    update_special_exams_and_publish,
    rerun_course,
    _convert_to_standard_url,
    _validate_urls_access_in_batches,
    _filter_by_status,
    _get_urls,
    _check_broken_links,
    _is_studio_url,
    _scan_course_for_links
)
from cms.djangoapps.contentstore.tests.test_libraries import LibraryTestCase
from cms.djangoapps.contentstore.tests.utils import CourseTestCase
from common.djangoapps.course_action_state.models import CourseRerunState
from common.djangoapps.student.tests.factories import UserFactory
from openedx.core.djangoapps.course_apps.toggles import EXAMS_IDA
from openedx.core.djangoapps.embargo.models import Country, CountryAccessRule, RestrictedCourse
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.tests.django_utils import TEST_DATA_SPLIT_MODULESTORE, ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory  # lint-amnesty, pylint: disable=wrong-import-order
from celery import Task

TEST_DATA_CONTENTSTORE = copy.deepcopy(settings.CONTENTSTORE)
TEST_DATA_CONTENTSTORE['DOC_STORE_CONFIG']['db'] = 'test_xcontent_%s' % uuid4().hex


def side_effect_exception(*args, **kwargs):
    """
    Side effect for mocking which raises an exception
    """
    raise Exception('Boom!')


@override_settings(CONTENTSTORE=TEST_DATA_CONTENTSTORE)
class ExportCourseTestCase(CourseTestCase):
    """
    Tests of the export_olx task applied to courses
    """

    def test_success(self):
        """
        Verify that a routine course export task succeeds
        """
        key = str(self.course.location.course_key)
        result = export_olx.delay(self.user.id, key, 'en')
        status = UserTaskStatus.objects.get(task_id=result.id)
        self.assertEqual(status.state, UserTaskStatus.SUCCEEDED)
        artifacts = UserTaskArtifact.objects.filter(status=status)
        self.assertEqual(len(artifacts), 1)
        output = artifacts[0]
        self.assertEqual(output.name, 'Output')

    @mock.patch('cms.djangoapps.contentstore.tasks.export_course_to_xml', side_effect=side_effect_exception)
    def test_exception(self, mock_export):  # pylint: disable=unused-argument
        """
        The export task should fail gracefully if an exception is thrown
        """
        key = str(self.course.location.course_key)
        result = export_olx.delay(self.user.id, key, 'en')
        self._assert_failed(result, json.dumps({'raw_error_msg': 'Boom!'}))

    @mock.patch('cms.djangoapps.contentstore.tasks.User.objects.get', side_effect=User.DoesNotExist)
    def test_invalid_user_id(self, mock_raise_exc):  # pylint: disable=unused-argument
        """
        Verify that attempts to export a course as an invalid user fail
        """
        user = UserFactory(id=User.objects.order_by('-id').first().pk + 100)
        key = str(self.course.location.course_key)
        result = export_olx.delay(user.id, key, 'en')
        self._assert_failed(result, f'Unknown User ID: {user.id}')

    def test_non_course_author(self):
        """
        Verify that users who aren't authors of the course are unable to export it
        """
        _, nonstaff_user = self.create_non_staff_authed_user_client()
        key = str(self.course.location.course_key)
        result = export_olx.delay(nonstaff_user.id, key, 'en')
        self._assert_failed(result, 'Permission denied')

    def _assert_failed(self, task_result, error_message):
        """
        Verify that a task failed with the specified error message
        """
        status = UserTaskStatus.objects.get(task_id=task_result.id)
        self.assertEqual(status.state, UserTaskStatus.FAILED)
        artifacts = UserTaskArtifact.objects.filter(status=status)
        self.assertEqual(len(artifacts), 1)
        error = artifacts[0]
        self.assertEqual(error.name, 'Error')
        self.assertEqual(error.text, error_message)

@override_settings(CONTENTSTORE=TEST_DATA_CONTENTSTORE)
class ExportLibraryTestCase(LibraryTestCase):
    """
    Tests of the export_olx task applied to libraries
    """

    def test_success(self):
        """
        Verify that a routine library export task succeeds
        """
        key = str(self.lib_key)
        result = export_olx.delay(self.user.id, key, 'en')
        status = UserTaskStatus.objects.get(task_id=result.id)
        self.assertEqual(status.state, UserTaskStatus.SUCCEEDED)
        artifacts = UserTaskArtifact.objects.filter(status=status)
        self.assertEqual(len(artifacts), 1)
        output = artifacts[0]
        self.assertEqual(output.name, 'Output')


@override_settings(CONTENTSTORE=TEST_DATA_CONTENTSTORE)
class RerunCourseTaskTestCase(CourseTestCase):  # lint-amnesty, pylint: disable=missing-class-docstring

    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    def _rerun_course(self, old_course_key, new_course_key):
        CourseRerunState.objects.initiated(old_course_key, new_course_key, self.user, 'Test Re-run')
        rerun_course(str(old_course_key), str(new_course_key), self.user.id)

    def test_success(self):
        """ The task should clone the OrganizationCourse and RestrictedCourse data. """
        old_course_key = self.course.id
        new_course_key = CourseLocator(org=old_course_key.org, course=old_course_key.course, run='rerun')

        old_course_id = str(old_course_key)
        new_course_id = str(new_course_key)

        organization = OrganizationFactory(short_name=old_course_key.org)
        OrganizationCourse.objects.create(course_id=old_course_id, organization=organization)

        restricted_course = RestrictedCourse.objects.create(course_key=self.course.id)
        restricted_country = Country.objects.create(country='US')

        CountryAccessRule.objects.create(
            rule_type=CountryAccessRule.BLACKLIST_RULE,
            restricted_course=restricted_course,
            country=restricted_country
        )

        # Run the task!
        self._rerun_course(old_course_key, new_course_key)

        # Verify the new course run exists
        course = modulestore().get_course(new_course_key)
        self.assertIsNotNone(course)

        # Verify the OrganizationCourse is cloned
        self.assertEqual(OrganizationCourse.objects.count(), 2)
        # This will raise an error if the OrganizationCourse object was not cloned
        OrganizationCourse.objects.get(course_id=new_course_id, organization=organization)

        # Verify the RestrictedCourse and related objects are cloned
        self.assertEqual(RestrictedCourse.objects.count(), 2)
        restricted_course = RestrictedCourse.objects.get(course_key=new_course_key)

        self.assertEqual(CountryAccessRule.objects.count(), 2)
        CountryAccessRule.objects.get(
            rule_type=CountryAccessRule.BLACKLIST_RULE,
            restricted_course=restricted_course,
            country=restricted_country
        )


@override_settings(CONTENTSTORE=TEST_DATA_CONTENTSTORE)
class RegisterExamsTaskTestCase(CourseTestCase):  # pylint: disable=missing-class-docstring

    @mock.patch('cms.djangoapps.contentstore.exams.register_exams')
    @mock.patch('cms.djangoapps.contentstore.proctoring.register_special_exams')
    def test_exam_service_not_enabled_success(self, _mock_register_exams_proctoring, _mock_register_exams_service):
        """ edx-proctoring interface is called if exam service is not enabled """
        update_special_exams_and_publish(str(self.course.id))
        _mock_register_exams_proctoring.assert_called_once_with(self.course.id)
        _mock_register_exams_service.assert_not_called()

    @mock.patch('cms.djangoapps.contentstore.exams.register_exams')
    @mock.patch('cms.djangoapps.contentstore.proctoring.register_special_exams')
    @override_waffle_flag(EXAMS_IDA, active=True)
    def test_exam_service_enabled_success(self, _mock_register_exams_proctoring, _mock_register_exams_service):
        """ exams service interface is called if exam service is enabled """
        update_special_exams_and_publish(str(self.course.id))
        _mock_register_exams_proctoring.assert_not_called()
        _mock_register_exams_service.assert_called_once_with(self.course.id)

    @mock.patch('cms.djangoapps.contentstore.exams.register_exams')
    @mock.patch('cms.djangoapps.contentstore.proctoring.register_special_exams')
    def test_register_exams_failure(self, _mock_register_exams_proctoring, _mock_register_exams_service):
        """ credit requirements update signal fires even if exam registration fails """
        with mock.patch('openedx.core.djangoapps.credit.signals.handlers.on_course_publish') as course_publish:
            _mock_register_exams_proctoring.side_effect = Exception('boom!')
            update_special_exams_and_publish(str(self.course.id))
            course_publish.assert_called()


class MockCourseLinkCheckTask(Task):
    def __init__(self):
        self.status = mock.Mock()

############## Course Optimizer tests ##############

class CheckBrokenLinksTaskTest(ModuleStoreTestCase):
    def setUp(self):
        super().setUp()
        self.store = modulestore()._get_modulestore_by_type(ModuleStoreEnum.Type.mongo)  # lint-amnesty, pylint: disable=protected-access
        self.test_course = CourseFactory.create(
            org="test", course="course1", display_name="run1"
        )
        self.mock_urls = [
            ["block-v1:edX+DemoX+Demo_Course+type@vertical+block@1", "http://example.com/valid"],
            ["block-v1:edX+DemoX+Demo_Course+type@vertical+block@2", "http://example.com/invalid"]
        ]
        self.expected_file_contents = [
            ['block-v1:edX+DemoX+Demo_Course+type@vertical+block@1', 'http://example.com/valid', False],
            ['block-v1:edX+DemoX+Demo_Course+type@vertical+block@2', 'http://example.com/invalid', False]
        ]

    @mock.patch('cms.djangoapps.contentstore.tasks.UserTaskArtifact', autospec=True)
    @mock.patch('cms.djangoapps.contentstore.tasks._scan_course_for_links')
    @mock.patch('cms.djangoapps.contentstore.tasks._save_broken_links_file', autospec=True)
    @mock.patch('cms.djangoapps.contentstore.tasks._write_broken_links_to_file', autospec=True)
    def test_check_broken_links_stores_broken_and_locked_urls(
        self,
        mock_write_broken_links_to_file,
        mock_save_broken_links_file,
        mock_scan_course_for_links,
        mock_user_task_artifact
    ):
        '''
        The test verifies that the check_broken_links task correctly
        stores broken or locked URLs in the course.
        The expected behavior is that the after scanning the course,
        validating the URLs, and filtering the results, the task stores the results in a
        JSON file.

        Note that this test mocks all validation functions and therefore
        does not test link validation or any of its support functions.
        '''
        # Arrange
        mock_user = UserFactory.create(username='student', password='password')
        mock_course_key_string = "course-v1:edX+DemoX+Demo_Course"
        mock_task = MockCourseLinkCheckTask()
        mock_scan_course_for_links.return_value = self.mock_urls

        # Act
        _check_broken_links(mock_task, mock_user.id, mock_course_key_string, 'en')  # pylint: disable=no-value-for-parameter

        # Assert
        ### Check that UserTaskArtifact was called with the correct arguments
        mock_user_task_artifact.assert_called_once_with(status=mock.ANY, name='BrokenLinks')

        ### Check that the correct links are written to the file
        mock_write_broken_links_to_file.assert_called_once_with(self.expected_file_contents, mock.ANY)

        ### Check that _save_broken_links_file was called with the correct arguments
        mock_save_broken_links_file.assert_called_once_with(mock_user_task_artifact.return_value, mock.ANY)

    def test_hash_tags_stripped_from_url_lists(self):
        NUM_HASH_TAG_LINES = 2
        url_list = '''
        href='#'                        # 1 of 2 lines that will be stripped
        href='http://google.com'
        src='#'                         # 2 of 2 lines that will be stripped
        href='https://microsoft.com'
        src="/static/resource_name"
        '''

        original_lines = len(url_list.splitlines()) - 2 # Correct for the two carriage returns surrounding the ''' marks
        processed_url_list = _get_urls(url_list)
        processed_lines = len(processed_url_list)

        assert processed_lines == original_lines - NUM_HASH_TAG_LINES, \
            f'Processed URL list lines = {processed_lines}; expected {original_lines - 2}'

    def test_http_url_not_recognized_as_studio_url_scheme(self):
        self.assertFalse(_is_studio_url(f'http://www.google.com'))

    def test_https_url_not_recognized_as_studio_url_scheme(self):
        self.assertFalse(_is_studio_url(f'https://www.google.com'))

    def test_http_with_studio_base_url_recognized_as_studio_url_scheme(self):
        self.assertTrue(_is_studio_url(f'http://{settings.CMS_BASE}/testurl'))

    def test_https_with_studio_base_url_recognized_as_studio_url_scheme(self):
        self.assertTrue(_is_studio_url(f'https://{settings.CMS_BASE}/testurl'))

    def test_container_url_without_url_base_is_recognized_as_studio_url_scheme(self):
        self.assertTrue(_is_studio_url(f'container/test'))

    def test_slash_url_without_url_base_is_recognized_as_studio_url_scheme(self):
        self.assertTrue(_is_studio_url(f'/static/test'))

    @mock.patch('cms.djangoapps.contentstore.tasks.ModuleStoreEnum', autospec=True)
    @mock.patch('cms.djangoapps.contentstore.tasks.modulestore', autospec=True)
    def test_course_scan_occurs_on_published_version(self, mock_modulestore, mock_module_store_enum):
        """_scan_course_for_links should only scan published courses"""
        mock_modulestore_instance = mock.Mock()
        mock_modulestore.return_value = mock_modulestore_instance
        mock_modulestore_instance.get_items.return_value = []

        mock_course_key_string = CourseKey.from_string("course-v1:edX+DemoX+Demo_Course")
        mock_module_store_enum.RevisionOption.published_only = "mock_published_only"

        _scan_course_for_links(mock_course_key_string)

        mock_modulestore_instance.get_items.assert_called_once_with(
            mock_course_key_string,
            qualifiers={'category': 'vertical'},
            revision=mock_module_store_enum.RevisionOption.published_only
        )

    @mock.patch('cms.djangoapps.contentstore.tasks._get_urls', autospec=True)
    def test_number_of_scanned_blocks_equals_blocks_in_course(self, mock_get_urls):
        """
        _scan_course_for_links should call _get_urls once per block in course.
        """
        expected_blocks = self.store.get_items(self.test_course.id)

        _scan_course_for_links(self.test_course.id)
        self.assertEqual(len(expected_blocks), mock_get_urls.call_count)

    @pytest.mark.asyncio
    async def test_every_detected_link_is_validated(self):
        '''
        The call to _validate_urls_access_in_batches() should call _validate_batch() three times, once for each
        of the three batches of length 2 in url_list. The lambda function supplied for _validate_batch will
        simply return the set of urls fed to _validate_batch(), and _validate_urls_access_in_batches() will
        aggregate these into a list identical to the original url_list.

        What this shows is that each url submitted to _validate_urls_access_in_batches() is ending up as an argument
        to one of the generated _validate_batch() calls, and that no input URL is left unprocessed.
        '''
        url_list = ['1', '2', '3', '4', '5']
        course_key = 'course-v1:edX+DemoX+Demo_Course'
        batch_size = 2
        with patch("cms.djangoapps.contentstore.tasks._validate_batch", new_callable=AsyncMock) as mock_validate_batch:
            mock_validate_batch.side_effect = lambda x, y: x
            validated_urls = await _validate_urls_access_in_batches(url_list, course_key, batch_size)
            mock_validate_batch.assert_called()
            assert mock_validate_batch.call_count == 3 # two full batches and one partial batch
            assert validated_urls == url_list, \
                f"List of validated urls {validated_urls} is not identical to sourced urls {url_list}"

    @pytest.mark.asyncio
    async def test_all_links_are_validated_with_batch_validation(self):
        '''
        Here the focus is not on batching, but rather that when validation occurs it does so on the intended
        URL strings
        '''
        with patch("cms.djangoapps.contentstore.tasks._validate_url_access", new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = {"status": 200}

            url_list = ['1', '2', '3', '4', '5']
            course_key = 'course-v1:edX+DemoX+Demo_Course'
            batch_size=2
            await _validate_urls_access_in_batches(url_list, course_key, batch_size)
            args_list = mock_validate.call_args_list
            urls = [call_args.args[1] for call_args in args_list] # The middle argument in each of the function calls
            for i in range(1,len(url_list)+1):
                assert str(i) in urls, f'{i} not supplied as a url for validation in batches function'

    def test_no_retries_on_403_access_denied_links(self):
        '''
        No mocking required here. Will populate "filtering_input" with simulated results for link checks where
        some links time out, some links receive 403 errors, and some receive 200 success. This test then
        ensures that "_filter_by_status()" tallies the three categories as expected, and formats the result
        as expected.
        '''
        url_list = ['1', '2', '3', '4', '5']
        filtering_input = []
        for i in range(1, len(url_list)+1): # Notch out one of the URLs, having it return a '403' status code
            filtering_input.append(
            {'block_id': f'block_{i}',
             'url': str(i),
             'status': 200},
            )
        filtering_input[2]['status'] = 403
        filtering_input[3]['status'] = 500
        filtering_input[4]['status'] = None

        broken_or_locked_urls, retry_list = _filter_by_status(filtering_input)
        assert len(broken_or_locked_urls) == 2  # The inputs with status = 403 and 500
        assert len(retry_list) == 1             # The input with status = None
        assert retry_list[0][1] == '5'      # The only URL fit for a retry operation (status == None)

    @patch("cms.djangoapps.contentstore.tasks._validate_user", return_value=MagicMock())
    @patch("cms.djangoapps.contentstore.tasks._scan_course_for_links", return_value=["url1", "url2"])
    @patch("cms.djangoapps.contentstore.tasks._validate_urls_access_in_batches",
                  return_value=[{"url": "url1", "status": "ok"}])
    @patch("cms.djangoapps.contentstore.tasks._filter_by_status",
           return_value=(["block_1", "url1", True], ["block_2", "url2"]))
    @patch("cms.djangoapps.contentstore.tasks._retry_validation",
           return_value=['block_2', 'url2'])
    def test_check_broken_links_calls_expected_support_functions(self,
                          mock_retry_validation,
                          mock_filter,
                          mock_validate_urls,
                          mock_scan_course,
                          mock_validate_user):
        # Parameters for the function
        user_id = 1234
        language = "en"
        course_key_string = "course-v1:edX+DemoX+2025"

        # Mocking self and status attributes for the test
        class MockStatus:
            def __init__(self):
                self.state = "READY"

            def set_state(self, state):
                self.state = state

            def increment_completed_steps(self):
                pass

            def fail(self, error_details):
                self.state = "FAILED"

        class MockSelf:
            def __init__(self):
                self.status = MockStatus()

        mock_self = MockSelf()

        _check_broken_links(mock_self, user_id, course_key_string, language)

        # Prepare expected results based on mock settings
        url_list = mock_scan_course.return_value
        validated_url_list = mock_validate_urls.return_value
        broken_or_locked_urls, retry_list = mock_filter.return_value
        course_key = CourseKey.from_string(course_key_string)

        if retry_list:
            retry_results = mock_retry_validation.return_value
            broken_or_locked_urls.extend(retry_results)

        # Perform verifications
        try:
            mock_self.status.increment_completed_steps()
            mock_retry_validation.assert_called_once_with(
                mock_filter.return_value[1], course_key, retry_count=3
            )
        except Exception as e:
            logging.exception("Error checking links for course %s", course_key_string, exc_info=True)
            if mock_self.status.state != "FAILED":
                mock_self.status.fail({"raw_error_msg": str(e)})
            assert False, "Exception should not occur"

        # Assertions to confirm patched calls were invoked
        mock_validate_user.assert_called_once_with(mock_self, user_id, language)
        mock_scan_course.assert_called_once_with(course_key)
        mock_validate_urls.assert_called_once_with(url_list, course_key, batch_size=100)
        mock_filter.assert_called_once_with(validated_url_list)
        if retry_list:
            mock_retry_validation.assert_called_once_with(retry_list, course_key, retry_count=3)



