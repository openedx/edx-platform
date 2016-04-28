"""
Unit tests for gating.signals module
"""
from mock import patch
from nose.plugins.attrib import attr
from ddt import ddt, data, unpack
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from courseware.tests.helpers import LoginEnrollmentTestCase

from milestones import api as milestones_api
from milestones.tests.utils import MilestonesTestCaseMixin
from openedx.core.lib.gating import api as gating_api
from gating.api import _get_xblock_parent, evaluate_prerequisite


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

        # Patch Milestones feature flag
        self.settings_patcher = patch.dict('django.conf.settings.FEATURES', {'MILESTONES_APP': True})
        self.settings_patcher.start()

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
            display_name='untitled sequential 1'
        )
        self.seq2 = ItemFactory.create(
            parent_location=self.chapter1.location,
            category='sequential',
            display_name='untitled sequential 2'
        )

        # create vertical
        self.vert1 = ItemFactory.create(
            parent_location=self.seq1.location,
            category='vertical',
            display_name='untitled vertical 1'
        )

        # create problem
        self.prob1 = ItemFactory.create(
            parent_location=self.vert1.location,
            category='problem',
            display_name='untitled problem 1'
        )

        # create orphan
        self.prob2 = ItemFactory.create(
            parent_location=self.course.location,
            category='problem',
            display_name='untitled problem 2'
        )

    def tearDown(self):
        """
        Tear down initial setup
        """
        self.settings_patcher.stop()
        super(GatingTestCase, self).tearDown()


class TestGetXBlockParent(GatingTestCase):
    """
    Tests for the get_xblock_parent function
    """

    def test_get_direct_parent(self):
        """ Test test_get_direct_parent """

        result = _get_xblock_parent(self.vert1)
        self.assertEqual(result.location, self.seq1.location)

    def test_get_parent_with_category(self):
        """ Test test_get_parent_of_category """

        result = _get_xblock_parent(self.vert1, 'sequential')
        self.assertEqual(result.location, self.seq1.location)
        result = _get_xblock_parent(self.vert1, 'chapter')
        self.assertEqual(result.location, self.chapter1.location)

    def test_get_parent_none(self):
        """ Test test_get_parent_none """

        result = _get_xblock_parent(self.vert1, 'unit')
        self.assertIsNone(result)


@attr('shard_3')
@ddt
class TestEvaluatePrerequisite(GatingTestCase, MilestonesTestCaseMixin):
    """
    Tests for the evaluate_prerequisite function
    """

    def setUp(self):
        super(TestEvaluatePrerequisite, self).setUp()
        self.user_dict = {'id': self.user.id}
        self.prereq_milestone = None

    def _setup_gating_milestone(self, min_score):
        """
        Setup a gating milestone for testing
        """

        gating_api.add_prerequisite(self.course.id, self.seq1.location)
        gating_api.set_required_content(self.course.id, self.seq2.location, self.seq1.location, min_score)
        self.prereq_milestone = gating_api.get_gating_milestone(self.course.id, self.seq1.location, 'fulfills')

    @patch('courseware.grades.get_module_score')
    @data((.5, True), (1, True), (0, False))
    @unpack
    def test_min_score_achieved(self, module_score, result, mock_module_score):
        """ Test test_min_score_achieved """

        self._setup_gating_milestone(50)

        mock_module_score.return_value = module_score
        evaluate_prerequisite(self.course, self.prob1.location, self.user.id)
        self.assertEqual(milestones_api.user_has_milestone(self.user_dict, self.prereq_milestone), result)

    @patch('gating.api.log.warning')
    @patch('courseware.grades.get_module_score')
    @data((.5, False), (1, True))
    @unpack
    def test_invalid_min_score(self, module_score, result, mock_module_score, mock_log):
        """ Test test_invalid_min_score """

        self._setup_gating_milestone(None)

        mock_module_score.return_value = module_score
        evaluate_prerequisite(self.course, self.prob1.location, self.user.id)
        self.assertEqual(milestones_api.user_has_milestone(self.user_dict, self.prereq_milestone), result)
        self.assertTrue(mock_log.called)

    @patch('courseware.grades.get_module_score')
    def test_orphaned_xblock(self, mock_module_score):
        """ Test test_orphaned_xblock """

        evaluate_prerequisite(self.course, self.prob2.location, self.user.id)
        self.assertFalse(mock_module_score.called)

    @patch('courseware.grades.get_module_score')
    def test_no_prerequisites(self, mock_module_score):
        """ Test test_no_prerequisites """

        evaluate_prerequisite(self.course, self.prob1.location, self.user.id)
        self.assertFalse(mock_module_score.called)

    @patch('courseware.grades.get_module_score')
    def test_no_gated_content(self, mock_module_score):
        """ Test test_no_gated_content """

        # Setup gating milestones data
        gating_api.add_prerequisite(self.course.id, self.seq1.location)

        evaluate_prerequisite(self.course, self.prob1.location, self.user.id)
        self.assertFalse(mock_module_score.called)
