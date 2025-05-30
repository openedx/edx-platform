"""
Test for xmodule.capa.score_render module
"""
import json
from unittest.mock import MagicMock, patch

from django.http import Http404

from common.djangoapps.student.models import AnonymousUserId
from common.djangoapps.student.tests.factories import UserFactory
from lms.djangoapps.grades.signals.handlers import handle_external_grader_score
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, BlockFactory
from xmodule.capa.score_render import (
    load_xblock_for_external_grader,
    get_block_for_descriptor_without_access_check
)


class ScoreEvent:
    """
    Mock class to represent an external grader score event.
    """

    def __init__(
        self,
        score_msg=None,
        course_id=None,
        user_id=None,
        module_id=None,
        submission_id=None,
        queue_key=None,
        queue_name=None
    ):
        self.score_msg = score_msg
        self.course_id = course_id
        self.user_id = user_id
        self.module_id = module_id
        self.submission_id = submission_id
        self.queue_key = queue_key
        self.queue_name = queue_name


class TestScoreRender(ModuleStoreTestCase):
    """
    Tests for the score_render module which handles external grader score submissions.
    """

    def setUp(self):
        """
        Set up the test environment.
        """
        super().setUp()
        self.course = CourseFactory.create()
        self.user = UserFactory.create()
        self.problem = BlockFactory.create(
            category='problem',
            parent=self.course,
            display_name='Test Problem'
        )
        self.anonymous_user_id = '12345'
        # Create AnonymousUserId instance
        AnonymousUserId.objects.create(
            user=self.user,
            anonymous_user_id=self.anonymous_user_id,
            course_id=self.course.id
        )

    @patch('xmodule.capa.score_render.modulestore')
    @patch('xmodule.capa.score_render.FieldDataCache')
    def test_load_xblock_for_external_grader(self, mock_field_data_cache, mock_modulestore):
        """
        Test loading an XBlock for external grading.
        """
        # Setup mock returns
        mock_modulestore.return_value = MagicMock()
        mock_modulestore.return_value.get_item.return_value = MagicMock()
        mock_field_data_cache.cache_for_block_descendents.return_value = MagicMock()

        with patch('xmodule.capa.score_render.get_block_for_descriptor_without_access_check') as mock_get_block:
            mock_get_block.return_value = MagicMock()

            # Call the function
            result = load_xblock_for_external_grader(
                self.anonymous_user_id,
                str(self.course.id),
                str(self.problem.location),
                self.course
            )

            # Assertions
            self.assertIsNotNone(result, "Should return a block instance")
            mock_modulestore.return_value.get_item.assert_called_once()
            mock_field_data_cache.cache_for_block_descendents.assert_called_once()
            mock_get_block.assert_called_once()

    @patch('xmodule.capa.score_render.modulestore')
    @patch('xmodule.capa.score_render.AnonymousUserId.objects.get')
    def test_load_xblock_for_external_grader_missing_block(self, mock_anon_user, mock_modulestore):
        """
        Test that Http404 is raised when the block is not found.
        """
        # Setup mock returns
        mock_anon_user.return_value = MagicMock(user=self.user)
        mock_modulestore.return_value = MagicMock()
        mock_modulestore.return_value.get_item.side_effect = Exception("Block not found")

        # Test that Http404 is raised
        with self.assertRaises(Http404):
            load_xblock_for_external_grader(
                self.anonymous_user_id,
                str(self.course.id),
                str(self.problem.location),
                self.course
            )

    @patch('xmodule.capa.score_render.prepare_runtime_for_user')
    def test_get_block_for_descriptor_without_access_check(self, mock_prepare_runtime):
        """
        Test initializing an XBlock instance without access checks.
        """
        # Setup mocks
        block = MagicMock()
        block.runtime = MagicMock()
        student_data = MagicMock()

        # Call the function
        result = get_block_for_descriptor_without_access_check(
            self.user,
            block,
            student_data,
            self.course.id,
            self.course
        )

        # Assertions
        self.assertIsNotNone(result, "Should return a block instance")
        mock_prepare_runtime.assert_called_once()
        block.bind_for_student.assert_called_once()

    @patch('xmodule.capa.score_render.modulestore')
    @patch('xmodule.capa.score_render.load_xblock_for_external_grader')
    def test_handle_external_grader_score_json_string(self, mock_load_xblock, mock_modulestore):
        """
        Test handling an external grader score with a JSON string message.
        """
        # Setup mocks
        mock_modulestore.return_value = MagicMock()
        mock_instance = MagicMock()
        mock_load_xblock.return_value = mock_instance

        # Create score event
        score = ScoreEvent(
            score_msg='{"score": 10, "feedback": "Great job!"}',
            course_id=str(self.course.id),
            user_id=self.anonymous_user_id,
            module_id=str(self.problem.location),
            submission_id='sub_123',
            queue_key='key_456',
            queue_name='test_queue'
        )

        # Call the handler
        handle_external_grader_score(None, None, score)

        # Assertions
        mock_load_xblock.assert_called_once()
        call_args, call_kwargs = mock_load_xblock.call_args

        self.assertEqual(call_args[0], score.user_id)
        self.assertEqual(call_args[1], score.course_id)
        self.assertEqual(call_args[2], score.module_id)

        self.assertIn('course', call_kwargs)

        mock_instance.handle_ajax.assert_called_once()
        ajax_args, _ = mock_instance.handle_ajax.call_args
        self.assertEqual(ajax_args[0], 'score_update')
        self.assertIn('xqueue_header', ajax_args[1])
        self.assertIn('xqueue_body', ajax_args[1])
        self.assertIn('queuekey', ajax_args[1])
        mock_instance.save.assert_called_once()

    @patch('xmodule.capa.score_render.modulestore')
    @patch('xmodule.capa.score_render.load_xblock_for_external_grader')
    def test_handle_external_grader_score_dict(self, mock_load_xblock, mock_modulestore):
        """
        Test handling an external grader score with a dictionary message.
        """
        # Setup mocks
        mock_modulestore.return_value = MagicMock()
        mock_instance = MagicMock()
        mock_load_xblock.return_value = mock_instance

        # Create score event with a dictionary
        score_dict = {"score": 10, "feedback": "Great job!"}
        score = ScoreEvent(
            score_msg=score_dict,
            course_id=str(self.course.id),
            user_id=self.anonymous_user_id,
            module_id=str(self.problem.location),
            submission_id='sub_123',
            queue_key='key_456',
            queue_name='test_queue'
        )

        # Call the handler
        handle_external_grader_score(None, None, score)

        # Assertions
        mock_load_xblock.assert_called_once()

        # Check that handle_ajax was called with the right arguments
        args, _ = mock_instance.handle_ajax.call_args
        self.assertEqual(args[0], 'score_update')

        data = args[1]
        self.assertIn('xqueue_header', data)
        self.assertIn('xqueue_body', data)
        self.assertIn('queuekey', data)

        # Verify header structure
        header = json.loads(data['xqueue_header'])
        self.assertEqual(header['lms_key'], 'sub_123')
        self.assertEqual(header['queue_name'], 'test_queue')

        # Verify body JSON - should be the same as original dictionary
        body = json.loads(data['xqueue_body'])
        self.assertEqual(body, score_dict)

        # Verify queue key
        self.assertEqual(data['queuekey'], 'key_456')

        # Verify instance was saved
        mock_instance.save.assert_called_once()

    @patch('xmodule.capa.score_render.modulestore')
    @patch('xmodule.capa.score_render.load_xblock_for_external_grader')
    def test_handle_external_grader_score_plain_text(self, mock_load_xblock, mock_modulestore):
        """
        Test handling an external grader score with a plain text message.
        """
        # Setup mocks
        mock_modulestore.return_value = MagicMock()
        mock_instance = MagicMock()
        mock_load_xblock.return_value = mock_instance

        # Create score event with plain text
        plain_text = "Plain text feedback that is not JSON"
        score = ScoreEvent(
            score_msg=plain_text,
            course_id=str(self.course.id),
            user_id=self.anonymous_user_id,
            module_id=str(self.problem.location),
            submission_id='sub_123',
            queue_key='key_456',
            queue_name='test_queue'
        )

        # Call the handler
        handle_external_grader_score(None, None, score)

        # Assertions
        mock_load_xblock.assert_called_once()

        # Check data sent to handle_ajax
        args, _ = mock_instance.handle_ajax.call_args
        data = args[1]

        # Verify the body is passed as-is (not JSON-serialized again)
        self.assertEqual(data['xqueue_body'], plain_text)

        # Verify instance was saved
        mock_instance.save.assert_called_once()

    @patch('xmodule.capa.score_render.modulestore')
    @patch('xmodule.capa.score_render.load_xblock_for_external_grader')
    def test_handle_external_grader_score_exception(self, mock_load_xblock, mock_modulestore):
        """
        Test handling an exception during score processing.
        """
        # Setup mocks
        mock_modulestore.return_value = MagicMock()
        mock_load_xblock.side_effect = Exception("Test exception")

        # Create score event
        score = ScoreEvent(
            score_msg='{"score": 10}',
            course_id=str(self.course.id),
            user_id=self.anonymous_user_id,
            module_id=str(self.problem.location),
            submission_id='sub_123',
            queue_key='key_456',
            queue_name='test_queue'
        )

        # Call the handler and expect exception to be raised
        with self.assertRaises(Exception):
            handle_external_grader_score(None, None, score)

    @patch('xmodule.capa.score_render.AnonymousUserId.objects.get')
    @patch('xmodule.capa.score_render.modulestore')
    @patch('xmodule.capa.score_render.FieldDataCache')
    @patch('xmodule.capa.score_render.get_block_for_descriptor_without_access_check')
    def test_load_xblock_for_external_grader_none_instance(self, mock_get_block, mock_field_data_cache,
                                                           mock_modulestore, mock_anon_user):
        """
        Test that Http404 is raised when get_block_for_descriptor_without_access_check returns None.
        """
        # Setup mock returns
        mock_anon_user.return_value = MagicMock(user=self.user)
        mock_modulestore.return_value = MagicMock()
        mock_block = MagicMock()
        mock_modulestore.return_value.get_item.return_value = mock_block
        mock_field_data_cache.cache_for_block_descendents.return_value = MagicMock()
        mock_get_block.return_value = None

        # Test that Http404 is raised
        with self.assertRaises(Http404) as context:
            load_xblock_for_external_grader(
                self.anonymous_user_id,
                str(self.course.id),
                str(self.problem.location)
            )

        expected_msg = f"It {str(self.problem.location)}"
        self.assertEqual(str(context.exception), expected_msg)

        # Verify that all mocks were called
        mock_anon_user.assert_called_once()
        mock_modulestore.return_value.get_item.assert_called_once()
        mock_field_data_cache.cache_for_block_descendents.assert_called_once()
        mock_get_block.assert_called_once()


class TestScoreRenderIntegration(ModuleStoreTestCase):
    """
    Integration tests for the score_render module.
    """

    def setUp(self):
        """
        Set up the test environment.
        """
        super().setUp()
        self.course = CourseFactory.create()
        self.user = UserFactory.create()
        self.problem = BlockFactory.create(
            category='problem',
            parent=self.course,
            display_name='Test Problem'
        )
        self.anonymous_user_id = '12345'
        # Create AnonymousUserId instance
        AnonymousUserId.objects.create(
            user=self.user,
            anonymous_user_id=self.anonymous_user_id,
            course_id=self.course.id
        )

    @patch('xmodule.capa.score_render.modulestore')
    def test_end_to_end_grading_flow(self, mock_modulestore):
        """
        Test the end-to-end flow from receiving a score event to updating the grade.
        """
        # Mock the internal call to load_xblock_for_external_grader
        with patch('xmodule.capa.score_render.load_xblock_for_external_grader') as mock_load_xblock:
            # Setup the mock XBlock instance
            mock_instance = MagicMock()
            mock_load_xblock.return_value = mock_instance

            # Create a score event
            score = ScoreEvent(
                score_msg='{"score": 1, "max_score": 1, "correct": true}',
                course_id=str(self.course.id),
                user_id=self.anonymous_user_id,
                module_id=str(self.problem.location),
                submission_id='sub_123',
                queue_key='key_456',
                queue_name='test_queue'
            )

            # Call the handler
            handle_external_grader_score(None, None, score)

            # Assertions
            mock_load_xblock.assert_called_once()
            mock_instance.handle_ajax.assert_called_once()
            mock_instance.save.assert_called_once()

            # Verify the data structure passed to handle_ajax
            handle_ajax_args = mock_instance.handle_ajax.call_args[0]
            self.assertEqual(handle_ajax_args[0], 'score_update')

            data = handle_ajax_args[1]
            self.assertIn('xqueue_header', data)
            self.assertIn('xqueue_body', data)
            self.assertIn('queuekey', data)

            header = json.loads(data['xqueue_header'])
            self.assertEqual(header['lms_key'], 'sub_123')
            self.assertEqual(header['queue_name'], 'test_queue')

            # Verify the body is the correct JSON
            body = json.loads(data['xqueue_body'])
            self.assertEqual(body['score'], 1)
            self.assertEqual(body['max_score'], 1)
            self.assertTrue(body['correct'])
