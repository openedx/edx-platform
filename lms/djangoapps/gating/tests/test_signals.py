"""
Unit tests for gating.signals module
"""
from mock import patch, MagicMock

from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.django import modulestore

from gating.signals import handle_subsection_score_changed


class TestHandleScoreChanged(ModuleStoreTestCase):
    """
    Test case for handle_score_changed django signal handler
    """
    def setUp(self):
        super(TestHandleScoreChanged, self).setUp()
        self.course = CourseFactory.create(org='TestX', number='TS01', run='2016_Q1')
        self.user = UserFactory.create()
        self.test_usage_key = self.course.location

    @patch('gating.signals.gating_api.evaluate_prerequisite')
    def test_gating_enabled(self, mock_evaluate):
        """ Test evaluate_prerequisite is called when course.enable_subsection_gating is True """
        self.course.enable_subsection_gating = True
        modulestore().update_item(self.course, 0)
        handle_subsection_score_changed(
            sender=None,
            course=self.course,
            user=self.user,
            subsection_grade=MagicMock(),
        )
        mock_evaluate.assert_called()

    @patch('gating.signals.gating_api.evaluate_prerequisite')
    def test_gating_disabled(self, mock_evaluate):
        """ Test evaluate_prerequisite is not called when course.enable_subsection_gating is False """
        handle_subsection_score_changed(
            sender=None,
            course=self.course,
            user=self.user,
            subsection_grade=MagicMock(),
        )
        mock_evaluate.assert_not_called()
