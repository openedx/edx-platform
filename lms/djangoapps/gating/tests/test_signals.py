"""
Unit tests for gating.signals module
"""
from mock import patch

from opaque_keys.edx.keys import UsageKey
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.django import modulestore

from gating.signals import handle_score_changed


class TestHandleScoreChanged(ModuleStoreTestCase):
    """
    Test case for handle_score_changed django signal handler
    """
    def setUp(self):
        super(TestHandleScoreChanged, self).setUp()
        self.course = CourseFactory.create(org='TestX', number='TS01', run='2016_Q1')
        self.user = UserFactory()
        self.test_usage_key = UsageKey.from_string('i4x://the/content/key/12345678')

    @patch('gating.signals.gating_api.evaluate_prerequisite')
    def test_gating_enabled(self, mock_evaluate):
        """ Test evaluate_prerequisite is called when course.enable_subsection_gating is True """
        self.course.enable_subsection_gating = True
        modulestore().update_item(self.course, 0)
        handle_score_changed(
            sender=None,
            points_possible=1,
            points_earned=1,
            user=self.user,
            course_id=unicode(self.course.id),
            usage_id=unicode(self.test_usage_key)
        )
        mock_evaluate.assert_called_with(self.course, self.test_usage_key, self.user.id)  # pylint: disable=no-member

    @patch('gating.signals.gating_api.evaluate_prerequisite')
    def test_gating_disabled(self, mock_evaluate):
        """ Test evaluate_prerequisite is not called when course.enable_subsection_gating is False """
        handle_score_changed(
            sender=None,
            points_possible=1,
            points_earned=1,
            user=self.user,
            course_id=unicode(self.course.id),
            usage_id=unicode(self.test_usage_key)
        )
        mock_evaluate.assert_not_called()
