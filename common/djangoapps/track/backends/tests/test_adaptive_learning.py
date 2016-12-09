"""
Tests for `AdaptiveLearningBackend`.
"""
from __future__ import absolute_import

import ddt
from django.test import TestCase
from mock import Mock, patch

from track.backends.adaptive_learning import AdaptiveLearningBackend


@ddt.ddt
class TestAdaptiveLearningBackend(TestCase):
    """
    Tests for AdaptiveLearningBackend.
    """

    def setUp(self):
        super(TestAdaptiveLearningBackend, self).setUp()
        self.mock_modulestore_object = Mock()
        self.mock_course_object = Mock()
        self.mock_modulestore_object.get_course.return_value = self.mock_course_object
        self.mock_modulestore = Mock(return_value=self.mock_modulestore_object)
        self.backend = AdaptiveLearningBackend(self.mock_modulestore)

    def _make_mock_usage_key(self, block_id):
        """
        Return mock UsageKey whose `block_id` is set to `block_id`.
        """
        mock_usage_key = Mock()
        mock_usage_key.block_id = block_id
        return mock_usage_key

    @staticmethod
    def _make_adaptive_learning_configuration(meaningful):
        """
        Return adaptive learning configuration that is `meaningful`.
        """
        if meaningful:
            return {
                'a': 'meaningful-value',
                'b': 'another-meaningful-value',
                'c': 42
            }
        else:
            return {
                'a': '',
                'b': '',
                'c': -1
            }

    @ddt.data(
        ('problem_check', True),
        ('other', False)
    )
    @ddt.unpack
    def test_is_problem_check(self, event_type, expected_result):
        """
        Test that `_is_problem_check` function returns True if event is of type "problem_check",
        and False otherwise.
        """
        event = {'event_type': event_type}
        result = self.backend.is_problem_check(event)
        self.assertEqual(result, expected_result)

    def test_get_course(self):
        """
        Test that `_get_course` function extracts appropriate value from event and returns it.
        """
        course_id = 'block-v1:org+course+run+type@course+block@course'
        event = {
            'context': {
                'course_id': course_id
            }
        }
        with patch('track.backends.adaptive_learning.CourseKey') as patched_class:
            mock_course_key = Mock()
            patched_class.from_string.return_value = mock_course_key
            course = self.backend.get_course(event)
            self.assertEqual(course, self.mock_course_object)
            patched_class.from_string.assert_called_once_with(course_id)
            self.mock_modulestore.assert_called_once_with()
            self.mock_modulestore_object.get_course.assert_called_once_with(mock_course_key)

    def test_get_block_id(self):
        """
        Test that `_get_block_id` function extracts appropriate value from event and returns it.
        """
        usage_key_string = 'block-v1:org+course+run+type@problem+block@8e52e13fc4g696gb8g33'
        event = {
            'context': {
                'module': {
                    'usage_key': usage_key_string
                }
            }
        }
        with patch('track.backends.adaptive_learning.UsageKey') as patched_class:
            expected_block_id = '8e52e13fc4g696gb8g33'
            patched_class.from_string.return_value = self._make_mock_usage_key(expected_block_id)
            block_id = self.backend.get_block_id(event)
            self.assertEqual(block_id, expected_block_id)
            patched_class.from_string.assert_called_once_with(usage_key_string)

    def test_get_user_id(self):
        """
        Test that `_get_user_id` function extracts appropriate value from event and returns it.
        """
        event = {
            'context': {
                'user_id': 23
            }
        }
        user_id = self.backend.get_user_id(event)
        self.assertEqual(user_id, 23)

    @ddt.data(('correct', '100'), ('incorrect', '0'))
    @ddt.unpack
    def test_get_success(self, success, expected_success):
        """
        Test that `_get_success` function extracts appropriate value from event and returns it.
        """
        event = {
            'event': {
                'success': success
            }
        }
        success = self.backend.get_success(event)
        self.assertEqual(success, expected_success)

    @ddt.data(
        (True, True),
        (True, False),
        (False, True),
        (False, False),
    )
    @ddt.unpack
    def test_adaptive_learning_backend(self, is_problem_check, meaningful):
        """
        Test that `send` method of AdaptiveLearningBackend triggers logic for sending result event
        to external service that provides adaptive learning features, when appropriate.

        Backend should only trigger logic for sending result event to external service
        if event being processed is of type 'problem_check', and adaptive learning configuration
        of current course is `meaningful`.
        """
        block_id = '8e52e13fc4g696gb8g33'
        user_id = 23
        success = 'correct'
        event = {
            'event_type': 'problem_check',
            'context': {
                'course_id': 'block-v1:org+course+run+type@course+block@course',
                'user_id': user_id,
                'module': {
                    'usage_key': 'block-v1:org+course+run+type@problem+block@{block_id}'.format(block_id=block_id)
                },
            },
            'event': {
                'success': success
            }
        }
        with patch.object(self.backend, 'is_problem_check') as patched_is_problem_check, \
                patch.object(self.backend, 'get_course') as patched_get_course, \
                patch.object(self.backend, 'get_block_id') as patched_get_block_id, \
                patch.object(self.backend, 'get_user_id') as patched_get_user_id, \
                patch.object(self.backend, 'get_success') as patched_get_success, \
                patch('track.backends.adaptive_learning.AdaptiveLibraryContentModule') as patched_class:
            patched_is_problem_check.return_value = is_problem_check
            course_mock = Mock()
            course_mock.adaptive_learning_configuration = self._make_adaptive_learning_configuration(meaningful)
            patched_get_course.return_value = course_mock
            patched_get_block_id.return_value = block_id
            patched_get_user_id.return_value = user_id
            patched_get_success.return_value = success
            mock_send_result_event = Mock()
            patched_class.send_result_event = mock_send_result_event
            self.backend.send(event)
            if is_problem_check:
                patched_get_course.assert_called_once_with(event)
                if meaningful:
                    patched_get_block_id.assert_called_once_with(event)
                    patched_get_user_id.assert_called_once_with(event)
                    patched_get_success.assert_called_once_with(event)
                    mock_send_result_event.assert_called_once_with(course_mock, block_id, user_id, success)
                else:
                    patched_get_block_id.assert_not_called()
                    patched_get_user_id.assert_not_called()
                    patched_get_success.assert_not_called()
                    mock_send_result_event.assert_not_called()
            else:
                patched_get_course.assert_not_called()
                patched_get_block_id.assert_not_called()
                patched_get_user_id.assert_not_called()
                patched_get_success.assert_not_called()
                mock_send_result_event.assert_not_called()
