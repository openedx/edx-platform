"""
Tests for views of adaptive_learning app.
"""

import json

from django.core.urlresolvers import reverse
from django.test import TestCase
from mock import Mock, patch

from adaptive_learning.tests.base import AdaptiveLearningTestMixin
from student.tests.factories import UserFactory


class AdaptiveLearningViewsTest(AdaptiveLearningTestMixin, TestCase):
    """
    Tests for views of adaptive_learning app.
    """

    def setUp(self):
        super(AdaptiveLearningViewsTest, self).setUp()
        password = 'password'
        self.user = UserFactory(password=password)
        self.client.login(username=self.user.username, password=password)

    def _make_revisions(self):
        """
        Return list of revisions for testing.
        """
        return [
            {
                'url': 'url-{n}'.format(n=n),
                'name': 'name-{n}'.format(n=n),
                'due_date': self.make_timestamp(self.make_due_date()),
            } for n in range(5)
        ]

    @staticmethod
    def _make_mock_modulestore(courses):
        """
        Return mock modulestore whose `get_courses` method returns `courses`.
        """
        mock_modulestore = Mock(autospec=True)
        mock_modulestore.get_courses.return_value = courses
        return mock_modulestore

    def _make_mock_courses(self, *meaningfulness):
        """
        Generate mock courses with adaptive learning configuration that is (not) meaningful.
        """
        for meaningful in meaningfulness:
            course = Mock()
            course.adaptive_learning_configuration = self._make_adaptive_learning_configuration(meaningful)
            yield course

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

    @patch('adaptive_learning.views.get_pending_revisions')
    def test_revisions(self, mock_get_pending_revisions):
        """
        Test 'revisions' view.
        """
        revisions = self._make_revisions()
        mock_get_pending_revisions.return_value = revisions
        response = self.client.get(reverse('revisions'))
        mock_get_pending_revisions.assert_called_once_with(self.user)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, json.dumps(revisions))

    @patch('adaptive_learning.views.modulestore')
    def test_revisions_course_configuration(self, mock_modulestore):
        """
        Test that 'revisions' view takes into account adaptive learning configuration of courses.

        When collecting revisions for display, the view should ignore courses
        that are not properly configured for communicating with external adaptive learning service.
        """
        regular_course, adaptive_learning_course = self._make_mock_courses(False, True)
        mock_modulestore.return_value = self._make_mock_modulestore([regular_course, adaptive_learning_course])
        with patch('adaptive_learning.views.get_pending_reviews') as patched_get_pending_reviews, \
                patch('adaptive_learning.views.get_revisions') as patched_get_revisions:
            pending_reviews = self.make_pending_reviews()
            revisions = self._make_revisions()
            patched_get_pending_reviews.return_value = pending_reviews
            patched_get_revisions.return_value = revisions
            response = self.client.get(reverse('revisions'))
            # Modulestore contains two courses, one course with a meaningful configuration,
            # and one course without a meaningful configuration.
            # So:
            # - Function for obtaining list of pending reviews should have been called once,
            #   with course that has meaningful configuration, and appropriate `user_id`.
            patched_get_pending_reviews.assert_called_once_with(adaptive_learning_course, self.user.id)  # pylint: disable=no-member
            # - Function for turning list of pending reviews into list of revisions to display
            #   should have been called once, with course that has meaningful configuration,
            #   and list of `pending_reviews`.
            patched_get_revisions.assert_called_once_with(adaptive_learning_course, pending_reviews)
            # - Content of response should be equal to return value of patched `get_revisions` function.
            self.assertEqual(response.content, json.dumps(revisions))

    @patch('adaptive_learning.views.modulestore')
    def test_revisions_no_pending_reviews(self, mock_modulestore):
        """
        Test that 'revisions' view behaves correctly when there are no pending reviews for a course.
        """
        courses = list(self._make_mock_courses(True))
        mock_modulestore.return_value = self._make_mock_modulestore(courses)
        with patch('adaptive_learning.views.get_pending_reviews') as patched_get_pending_reviews, \
                patch('adaptive_learning.views.get_revisions') as patched_get_revisions:
            patched_get_pending_reviews.return_value = {}
            response = self.client.get(reverse('revisions'))
            patched_get_pending_reviews.assert_called_once_with(courses[0], self.user.id)  # pylint: disable=no-member
            patched_get_revisions.assert_not_called()
            self.assertEqual(response.content, json.dumps([]))
