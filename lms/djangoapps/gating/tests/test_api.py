"""
Unit tests for gating.signals module
"""
from mock import patch, Mock
from nose.plugins.attrib import attr
from ddt import ddt, data, unpack
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from courseware.tests.helpers import LoginEnrollmentTestCase

from milestones import api as milestones_api
from milestones.tests.utils import MilestonesTestCaseMixin
from openedx.core.lib.gating import api as gating_api
from gating.api import evaluate_prerequisite


class GatingTestCase(LoginEnrollmentTestCase, ModuleStoreTestCase):
    """
    Base TestCase class for setting up a basic course structure
    and testing the gating feature
    """

    def setUp(self):
        """
        Initial data setup
        """
        super(GatingTestCase, self).setUp()

        # create course
        self.course = CourseFactory.create(
            org='edX',
            number='EDX101',
            run='EDX101_RUN1',
            display_name='edX 101'
        )
        self.course.enable_subsection_gating = True
        self.course.save()
        self.store.update_item(self.course, 0)

        # create chapter
        self.chapter1 = ItemFactory.create(
            parent_location=self.course.location,
            category='chapter',
            display_name='untitled chapter 1'
        )

        # create sequentials
        self.seq1 = ItemFactory.create(
            parent_location=self.chapter1.location,
            category='sequential',
            display_name='gating sequential'
        )
        self.seq2 = ItemFactory.create(
            parent_location=self.chapter1.location,
            category='sequential',
            display_name='gated sequential'
        )


@attr(shard=3)
@ddt
class TestEvaluatePrerequisite(GatingTestCase, MilestonesTestCaseMixin):
    """
    Tests for the evaluate_prerequisite function
    """

    def setUp(self):
        super(TestEvaluatePrerequisite, self).setUp()
        self.user_dict = {'id': self.user.id}
        self.prereq_milestone = None
        self.subsection_grade = Mock(location=self.seq1.location)

    def _setup_gating_milestone(self, min_score):
        """
        Setup a gating milestone for testing
        """
        gating_api.add_prerequisite(self.course.id, self.seq1.location)
        gating_api.set_required_content(self.course.id, self.seq2.location, self.seq1.location, min_score)
        self.prereq_milestone = gating_api.get_gating_milestone(self.course.id, self.seq1.location, 'fulfills')

    @patch('gating.api._get_subsection_percentage')
    @data((50, True), (100, True), (0, False))
    @unpack
    def test_min_score_achieved(self, module_score, result, mock_score):
        self._setup_gating_milestone(50)
        mock_score.return_value = module_score

        evaluate_prerequisite(self.course, self.subsection_grade, self.user)
        self.assertEqual(milestones_api.user_has_milestone(self.user_dict, self.prereq_milestone), result)

    @patch('gating.api.log.warning')
    @patch('gating.api._get_subsection_percentage')
    @data((50, False), (100, True))
    @unpack
    def test_invalid_min_score(self, module_score, result, mock_score, mock_log):
        self._setup_gating_milestone(None)
        mock_score.return_value = module_score

        evaluate_prerequisite(self.course, self.subsection_grade, self.user)
        self.assertEqual(milestones_api.user_has_milestone(self.user_dict, self.prereq_milestone), result)
        self.assertTrue(mock_log.called)

    @patch('gating.api._get_subsection_percentage')
    def test_no_prerequisites(self, mock_score):
        evaluate_prerequisite(self.course, self.subsection_grade, self.user)
        self.assertFalse(mock_score.called)

    @patch('gating.api._get_subsection_percentage')
    def test_no_gated_content(self, mock_score):
        gating_api.add_prerequisite(self.course.id, self.seq1.location)

        evaluate_prerequisite(self.course, self.subsection_grade, self.user)
        self.assertFalse(mock_score.called)
