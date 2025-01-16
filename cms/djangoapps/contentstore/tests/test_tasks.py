"""
Unit tests for course import and export Celery tasks
"""


import copy
import json
import os
from tempfile import NamedTemporaryFile
from unittest import mock, TestCase
from uuid import uuid4

import pytest as pytest
from django.conf import settings
from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user
from django.test.utils import override_settings
from django.core.files import File
from edx_toggles.toggles.testutils import override_waffle_flag
from opaque_keys.edx.locator import CourseLocator
from organizations.models import OrganizationCourse
from organizations.tests.factories import OrganizationFactory
from user_tasks.models import UserTaskArtifact, UserTaskStatus

from cms.djangoapps.contentstore.tasks import (
    export_olx,
    update_special_exams_and_publish,
    rerun_course,
    _convert_to_standard_url,
    _check_broken_links
)
from cms.djangoapps.contentstore.tests.test_libraries import LibraryTestCase
from cms.djangoapps.contentstore.tests.utils import CourseTestCase
from common.djangoapps.course_action_state.models import CourseRerunState
from common.djangoapps.student.tests.factories import UserFactory
from openedx.core.djangoapps.course_apps.toggles import EXAMS_IDA
from openedx.core.djangoapps.embargo.models import Country, CountryAccessRule, RestrictedCourse
from xmodule.modulestore.django import modulestore  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.tests.django_utils import TEST_DATA_SPLIT_MODULESTORE, ModuleStoreTestCase
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


class CheckBrokenLinksTaskTest(ModuleStoreTestCase):
    def setUp(self):
        super().setUp()
        self.mock_urls = [
            ["block-v1:edX+DemoX+Demo_Course+type@vertical+block@1", "http://example.com/valid"],
            ["block-v1:edX+DemoX+Demo_Course+type@vertical+block@2", "http://example.com/invalid"]
        ]
        self.expected_file_contents = [
            ['block-v1:edX+DemoX+Demo_Course+type@vertical+block@1', 'http://example.com/valid', False],
            ['block-v1:edX+DemoX+Demo_Course+type@vertical+block@2', 'http://example.com/invalid', False]
        ]

    @mock.patch('cms.djangoapps.contentstore.tasks.UserTaskArtifact', autospec=True)
    @mock.patch('cms.djangoapps.contentstore.tasks.UserTaskStatus', autospec=True)
    @mock.patch('cms.djangoapps.contentstore.tasks._scan_course_for_links')
    @mock.patch('cms.djangoapps.contentstore.tasks._save_broken_links_file', autospec=True)
    @mock.patch('cms.djangoapps.contentstore.tasks._write_broken_links_to_file', autospec=True)
    def test_check_broken_links_stores_broken_and_locked_urls(
        self,
        mock_write_links,
        mock_save_broken_links_file,
        mock_scan_course_for_links,
        _mock_user_task_status,
        mock_user_task_artifact
    ):
        '''
        The test should verify that the check_broken_links task correctly
        identifies and stores broken or locked URLs in the course.
        The expected behavior is that the task scans the course,
        validates the URLs, filters the results, and stores them in a
        JSON file.
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
        mock_write_links.assert_called_once_with(self.expected_file_contents, mock.ANY)

        ### Check that _save_broken_links_file was called with the correct arguments
        mock_save_broken_links_file.assert_called_once_with(mock_user_task_artifact.return_value, mock.ANY)


    def test_user_does_not_exist_raises_exception(self):
        raise NotImplementedError

    def test_no_course_access_raises_exception(self):
        raise NotImplementedError

    def test_hash_tags_stripped_from_url_lists(self):
        raise NotImplementedError

    def test_urls_out_count_equals_urls_in_count_when_no_hashtags(self):
        raise NotImplementedError

    def test_http_and_https_recognized_as_studio_url_schemes(self):
        raise NotImplementedError

    def test_file_not_recognized_as_studio_url_scheme(self):
        raise NotImplementedError

    @pytest.mark.parametrize("url, course_key, post_substitution_url",
                             ["/static/anything_goes_here?raw", "1", "2"])
    def test_url_substitution_on_static_prefixes(self, url, course_key, post_substitution_url):
        with_substitution = _convert_to_standard_url(url, course_key)
        assert with_substitution == post_substitution_url, f'{with_substitution} expected to be {post_substitution_url}'

    def test_url_substitution_on_forward_slash_prefixes(self):
        raise NotImplementedError

    def test_url_subsitution_on_containers(self):
        raise NotImplementedError

    def test_optimization_occurs_on_published_version(self):
        raise NotImplementedError

    def test_number_of_scanned_blocks_equals_blocks_in_course(self):
        raise NotImplementedError

    def test_every_detected_link_is_validated(self):
        raise NotImplementedError

    def test_link_validation_is_batched(self):
        raise NotImplementedError

    def test_all_links_in_link_list_longer_than_batch_size_are_validated(self):
        raise NotImplementedError

    def test_no_retries_on_403_access_denied_links(self):
        raise NotImplementedError

    def test_retries_attempted_on_connection_errors(self):
        raise NotImplementedError

    def test_max_number_of_retries_is_respected(self):
        raise NotImplementedError

    def test_scan_generates_file_named_by_course_key(self):
        raise NotImplementedError
