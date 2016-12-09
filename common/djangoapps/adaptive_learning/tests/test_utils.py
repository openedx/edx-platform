"""
Tests for utils of adaptive_learning app.
"""

from django.test import TestCase
from mock import Mock, patch

from adaptive_learning.tests.base import AdaptiveLearningTestMixin
from adaptive_learning.utils import get_pending_reviews, get_revisions


class AdaptiveLearningUtilsTest(AdaptiveLearningTestMixin, TestCase):
    """
    Tests for utils of adaptive_learning app.
    """

    @staticmethod
    def _make_mock_modulestore(adaptive_content_blocks):
        """
        Return mock modulestore whose `get_items` method returns `adaptive_content_blocks`.
        """
        mock_modulestore = Mock(autospec=True)
        mock_modulestore.get_items.return_value = adaptive_content_blocks
        return mock_modulestore

    def _make_mock_blocks(self, *pending_reviews):
        """
        Return list of mock adaptive content blocks for testing.

        List contains one adaptive content block per pending review in `pending_reviews`.

        Each adaptive content block is set up to return a list containing a child
        whose `block_id` matches the 'review_question_uid' of a pending review
        when `get_children` is called on it.
        """
        adaptive_content_blocks = []
        for block_id, dummy in pending_reviews:
            adaptive_content_block = Mock()
            relevant_child = self._make_mock_child(block_id)
            adaptive_content_block.get_children.return_value = [relevant_child]
            adaptive_content_blocks.append(adaptive_content_block)
        return adaptive_content_blocks

    @staticmethod
    def _make_mock_child(block_id):
        """
        Return mock child with `block_id` and `display_name` that includes `block_id`.
        """
        child = Mock()
        child.location.block_id = block_id
        child.display_name = 'child-{}'.format(block_id)
        return child

    @staticmethod
    def _make_mock_course(course_key):
        """
        Return mock course with `course_key`.
        """
        course = Mock()
        course.location.course_key = course_key
        return course

    @staticmethod
    def _make_mock_urls():
        """
        Return list of mock URLs to use as return values for `get_redirect_url`.
        """
        return [
            'url-{n}'.format(n=n) for n in range(5)
        ]

    @patch('adaptive_learning.utils.AdaptiveLibraryContentModule')
    def test_get_pending_reviews(self, mock_module):
        """
        Test that `get_pending_reviews` calls appropriate API for obtaining raw list of pending reviews,
        and returns the data in a new format optimized for further processing.
        """
        raw_pending_reviews = self.make_raw_pending_reviews()
        mock_module.fetch_pending_reviews.return_value = raw_pending_reviews
        mock_course = Mock()
        user_id = 23
        pending_reviews = get_pending_reviews(mock_course, user_id)
        mock_module.fetch_pending_reviews.assert_called_once_with(mock_course, user_id)
        self.assertEqual(len(pending_reviews.items()), len(raw_pending_reviews))
        for raw_pending_review in raw_pending_reviews:
            block_id = raw_pending_review['review_question_uid']
            due_date = raw_pending_review['next_review_at']
            self.assertIn(block_id, pending_reviews)
            self.assertEqual(pending_reviews[block_id], due_date)

    @patch('adaptive_learning.utils.modulestore')
    @patch('adaptive_learning.utils.get_redirect_url')
    def test_get_revisions(self, mock_get_redirect_url, mock_modulestore):
        """
        Test that `get_revisions` returns expected result.
        """
        mock_get_redirect_url.side_effect = self._make_mock_urls()

        course = self._make_mock_course('dummy-key')
        pending_reviews = self.make_pending_reviews()

        adaptive_content_blocks = self._make_mock_blocks(*pending_reviews.items())
        mock_modulestore.return_value = self._make_mock_modulestore(adaptive_content_blocks)

        expected_revisions = [
            {
                'url': 'url-{n}'.format(n=n),
                'name': 'child-{}'.format(pending_reviews.items()[n][0]),
                'due_date': self.make_timestamp(pending_reviews.items()[n][1]),
            } for n in range(5)
        ]

        revisions = get_revisions(course, pending_reviews)
        self.assertEqual(revisions, expected_revisions)
