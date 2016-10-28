"""
Unit tests for gating.signals module
"""
from mock import patch
from nose.plugins.attrib import attr
from ddt import ddt, data, unpack
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from lms.djangoapps.courseware.access import has_access
from lms.djangoapps.courseware.tests.helpers import get_request_for_user
from lms.djangoapps.grades.tests.utils import answer_problem
from lms.djangoapps.grades.new.course_grade import CourseGradeFactory
from milestones import api as milestones_api
from milestones.tests.utils import MilestonesTestCaseMixin
from openedx.core.lib.gating import api as gating_api
from request_cache.middleware import RequestCache


class GatingTestCase(ModuleStoreTestCase):
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
        grading_policy = {
            "GRADER": [{
                "type": "Homework",
                "min_count": 3,
                "drop_count": 0,
                "short_label": "HW",
                "weight": 1.0
            }]
        }
        self.course.grading_policy = grading_policy
        self.course.save()
        self.store.update_item(self.course, 0)

        # create chapter
        self.chapter1 = ItemFactory.create(
            parent_location=self.course.location,
            category='chapter',
            display_name='chapter 1'
        )

        # create sequentials
        self.seq1 = ItemFactory.create(
            parent_location=self.chapter1.location,
            category='sequential',
            display_name='gating sequential 1',
            graded=True,
            format='Homework',
        )
        self.seq2 = ItemFactory.create(
            parent_location=self.chapter1.location,
            category='sequential',
            display_name='gated sequential 2',
            graded=True,
            format='Homework',
        )
        self.seq3 = ItemFactory.create(
            parent_location=self.chapter1.location,
            category='sequential',
            display_name='sequential 3',
            graded=True,
            format='Homework',
        )

        # create problem
        self.gating_prob1 = ItemFactory.create(
            parent_location=self.seq1.location,
            category='problem',
            display_name='gating problem 1',
        )
        self.gated_prob2 = ItemFactory.create(
            parent_location=self.seq2.location,
            category='problem',
            display_name='gated problem 2',
        )
        self.prob3 = ItemFactory.create(
            parent_location=self.seq3.location,
            category='problem',
            display_name='problem 3',
        )

        # create orphan
        self.orphan = ItemFactory.create(
            parent_location=self.course.location,
            category='problem',
            display_name='orphan'
        )

        self.prereq_milestone = None

    def setup_gating_milestone(self, min_score):
        """
        Setup a gating milestone for testing.
        Gating content: seq1 (must be fulfilled before access to seq2)
        Gated content: seq2 (requires completion of seq1 before access)
        """
        gating_api.add_prerequisite(self.course.id, self.seq1.location)
        gating_api.set_required_content(self.course.id, self.seq2.location, self.seq1.location, min_score)
        self.prereq_milestone = gating_api.get_gating_milestone(self.course.id, self.seq1.location, 'fulfills')

    def verify_access_to_gated_content(self, user, expected_access):
        """
        Verifies access to gated content for the given user is as expected.
        """
        # clear the request cache to flush any cached access results
        RequestCache.clear_request_cache()

        # access to gating content (seq1) remains constant
        self.assertTrue(has_access(user, 'load', self.seq1, self.course.id))

        # access to gated content (seq2) is as expected
        self.assertEquals(bool(has_access(user, 'load', self.seq2, self.course.id)), expected_access)

    def verify_user_has_prereq_milestone(self, user, expected_has_milestone):
        """
        Verifies whether or not the user has the prereq milestone
        """
        self.assertEquals(
            milestones_api.user_has_milestone({'id': user.id}, self.prereq_milestone),
            expected_has_milestone,
        )


@attr(shard=3)
class TestGatedContent(GatingTestCase, MilestonesTestCaseMixin):
    """
    Tests for gated content.
    """
    def setUp(self):
        super(TestGatedContent, self).setUp()
        self.setup_gating_milestone(100)
        self.non_staff_user, _ = self.create_non_staff_user()

    def test_gated_for_nonstaff(self):
        self.verify_user_has_prereq_milestone(self.non_staff_user, expected_has_milestone=False)
        self.verify_access_to_gated_content(self.non_staff_user, expected_access=False)

    def test_not_gated_for_staff(self):
        self.verify_user_has_prereq_milestone(self.user, expected_has_milestone=False)
        self.verify_access_to_gated_content(self.user, expected_access=True)

    def _verify_course_grade(self, user, expected_percent):
        """
        Verifies the given user's course grade is the expected percentage.
        Also verifies the user's grade information contains values for
        all problems in the course, whether or not they are currently
        gated.
        """
        course_grade = CourseGradeFactory(user).create(self.course)
        for prob in [self.gating_prob1, self.gated_prob2, self.prob3]:
            self.assertIn(prob.location, course_grade.locations_to_scores)
        self.assertNotIn(self.orphan.location, course_grade.locations_to_scores)

        self.assertEquals(course_grade.percent, expected_percent)

    def test_gated_content_always_in_grades(self):
        request = get_request_for_user(self.non_staff_user)

        # start with a grade from a non-gated subsection
        answer_problem(self.course, request, self.prob3, 10, 10)

        # verify gated status and overall course grade percentage
        self.verify_user_has_prereq_milestone(self.non_staff_user, expected_has_milestone=False)
        self.verify_access_to_gated_content(self.non_staff_user, expected_access=False)
        self._verify_course_grade(self.non_staff_user, .33)

        # fulfill the gated requirements
        answer_problem(self.course, request, self.gating_prob1, 10, 10)

        # verify gated status and overall course grade percentage
        self.verify_user_has_prereq_milestone(self.non_staff_user, expected_has_milestone=True)
        self.verify_access_to_gated_content(self.non_staff_user, expected_access=True)
        self._verify_course_grade(self.non_staff_user, .67)


@attr(shard=3)
@ddt
class TestHandleSubsectionGradeUpdates(GatingTestCase, MilestonesTestCaseMixin):
    """
    Tests for gated content when subsection grade is updated.
    """

    def setUp(self):
        super(TestHandleSubsectionGradeUpdates, self).setUp()
        self.user, _ = self.create_non_staff_user()  # run tests for a non-staff user
        self.request = get_request_for_user(self.user)

    def test_signal_handler_called(self):
        with patch('lms.djangoapps.gating.signals.gating_api.evaluate_prerequisite') as mock_handler:
            self.assertFalse(mock_handler.called)
            answer_problem(self.course, self.request, self.gating_prob1, 1, 1)
            self.assertTrue(mock_handler.called)

    @data((1, 2, True), (1, 1, True), (0, 1, False))
    @unpack
    def test_min_score_achieved(self, earned, max_possible, result):
        self.setup_gating_milestone(50)

        self.verify_user_has_prereq_milestone(self.user, expected_has_milestone=False)
        self.verify_access_to_gated_content(self.user, expected_access=False)

        answer_problem(self.course, self.request, self.gating_prob1, earned, max_possible)

        self.verify_user_has_prereq_milestone(self.user, expected_has_milestone=result)
        self.verify_access_to_gated_content(self.user, expected_access=result)

    @data((1, 2, False), (1, 1, True))
    @unpack
    def test_invalid_min_score(self, earned, max_possible, result):
        self.setup_gating_milestone(None)

        answer_problem(self.course, self.request, self.gating_prob1, earned, max_possible)
        self.verify_user_has_prereq_milestone(self.user, expected_has_milestone=result)

    def test_orphaned_xblock(self):
        with patch('lms.djangoapps.gating.signals.gating_api.evaluate_prerequisite') as mock_handler:
            self.assertFalse(mock_handler.called)
            answer_problem(self.course, self.request, self.orphan, 1, 1)
            self.assertFalse(mock_handler.called)

    @patch('gating.api.milestones_helpers')
    def test_no_prerequisites(self, mock_milestones):
        answer_problem(self.course, self.request, self.gating_prob1, 1, 1)
        self.assertFalse(mock_milestones.called)

    @patch('gating.api.milestones_helpers')
    def test_no_gated_content(self, mock_milestones):
        gating_api.add_prerequisite(self.course.id, self.seq1.location)
        answer_problem(self.course, self.request, self.gating_prob1, 1, 1)
        self.assertFalse(mock_milestones.called)
