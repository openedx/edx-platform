"""
Unit tests for gating.signals module
"""


from mock import Mock, patch

from lms.djangoapps.gating.signals import evaluate_subsection_gated_milestones
from common.djangoapps.student.tests.factories import UserFactory
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class TestHandleScoreChanged(ModuleStoreTestCase):
    """
    Test case for handle_score_changed django signal handler
    """

    def setUp(self):
        super(TestHandleScoreChanged, self).setUp()
        self.course = CourseFactory.create(org='TestX', number='TS01', run='2016_Q1')
        self.user = UserFactory.create()
        self.subsection_grade = Mock()

    @patch('lms.djangoapps.gating.api.gating_api.get_gating_milestone')
    def test_gating_enabled(self, mock_gating_milestone):
        self.course.enable_subsection_gating = True
        modulestore().update_item(self.course, 0)
        evaluate_subsection_gated_milestones(
            sender=None,
            user=self.user,
            course=self.course,
            subsection_grade=self.subsection_grade,
        )
        self.assertTrue(mock_gating_milestone.called)

    @patch('lms.djangoapps.gating.api.gating_api.get_gating_milestone')
    def test_gating_disabled(self, mock_gating_milestone):
        evaluate_subsection_gated_milestones(
            sender=None,
            user=self.user,
            course=self.course,
            subsection_grade=self.subsection_grade,
        )
        self.assertFalse(mock_gating_milestone.called)
