"""
Unit tests for gating.signals module
"""
from mock import patch, MagicMock

from opaque_keys.edx.keys import UsageKey
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.django import modulestore

from gating.signals import handle_subsection_score_updated


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
        self.course.enable_subsection_gating = True
        modulestore().update_item(self.course, 0)
        handle_subsection_score_updated(
            sender=None,
            course=self.course,
            user=self.user,
            subsection_grade=MagicMock(),
        )
        mock_evaluate.assert_called()

    @patch('gating.signals.gating_api.evaluate_prerequisite')
    def test_gating_disabled(self, mock_evaluate):
        handle_subsection_score_updated(
            sender=None,
            course=self.course,
            user=self.user,
            subsection_grade=MagicMock(),
        )
        mock_evaluate.assert_not_called()
