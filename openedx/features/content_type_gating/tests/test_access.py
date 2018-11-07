"""
Test audit user's access to various content based on content-gating features.
"""

import ddt
from django.http import Http404
from django.test.client import RequestFactory
from django.test.utils import override_settings
from mock import Mock, patch

from course_modes.tests.factories import CourseModeFactory
from courseware.access_response import IncorrectPartitionGroupError
from lms.djangoapps.courseware.module_render import load_single_xblock
from openedx.core.djangoapps.waffle_utils.testutils import override_waffle_flag
from openedx.features.course_duration_limits.config import CONTENT_TYPE_GATING_FLAG
from student.tests.factories import AdminFactory, CourseEnrollmentFactory, UserFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory


@ddt.ddt
@override_waffle_flag(CONTENT_TYPE_GATING_FLAG, True)
@override_settings(FIELD_OVERRIDE_PROVIDERS=(
    'openedx.features.content_type_gating.field_override.ContentTypeGatingFieldOverride',
))
class TestProblemTypeAccess(SharedModuleStoreTestCase):

    PROBLEM_TYPES = ['problem', 'openassessment', 'drag-and-drop-v2', 'done', 'edx_sga', ]

    GRADED_SCORE_WEIGHT_TEST_CASES = [
        # graded, has_score, weight, is_gated
        (False, False, 0, False),
        (False, True, 0, False),
        (False, False, 1, False),
        (False, True, 1, False),
        (True, False, 0, False),
        (True, True, 0, False),
        (True, False, 1, False),
        (True, True, 1, True)
    ]

    @classmethod
    def setUpClass(self):
        super(TestProblemTypeAccess, self).setUpClass()
        self.factory = RequestFactory()
        self.course = CourseFactory.create(run='testcourse1', display_name='Test Course Title')
        CourseModeFactory.create(course_id=self.course.id, mode_slug='audit')
        CourseModeFactory.create(course_id=self.course.id, mode_slug='verified')
        with self.store.bulk_operations(self.course.id):
            self.chapter = ItemFactory.create(
                parent=self.course,
                display_name='Overview'
            )
            self.welcome = ItemFactory.create(
                parent=self.chapter,
                display_name='Welcome'
            )
            ItemFactory.create(
                parent=self.course,
                category='chapter',
                display_name='Week 1'
            )
            self.chapter_subsection = ItemFactory.create(
                parent=self.chapter,
                category='sequential',
                display_name='Lesson 1'
            )
            self.vertical = ItemFactory.create(
                parent=self.chapter_subsection,
                category='vertical',
                display_name='Lesson 1 Vertical - Unit 1'
            )
            self.lti_block = ItemFactory.create(
                parent=self.vertical,
                category='lti_consumer',
                display_name='lti_consumer',
                has_score=True,
                graded=True,
            )
            self.lti_block_not_scored = ItemFactory.create(
                parent=self.vertical,
                category='lti_consumer',
                display_name='lti_consumer_2',
                has_score=False,
            )
            self.problem_dict = {}
            for prob_type in self.PROBLEM_TYPES:
                block = ItemFactory.create(
                    parent=self.vertical,
                    category=prob_type,
                    display_name=prob_type,
                    graded=True,
                )
                self.problem_dict[prob_type] = block

            '''
            Create components with the cartesian product of possible values of
            graded/has_score/weight for the test_graded_score_weight_values test.
            '''
            self.graded_score_weight_blocks = {}
            for graded, has_score, weight, gated in self.GRADED_SCORE_WEIGHT_TEST_CASES:
                case_name = ' Graded: ' + str(graded) + ' Has Score: ' + str(has_score) + ' Weight: ' + str(weight)
                block = ItemFactory.create(
                    parent=self.vertical,
                    # has_score is determined by XBlock type. It is not a value set on an instance of an XBlock.
                    # Therefore, we create a problem component when has_score is True
                    # and an html component when has_score is False.
                    category='problem' if has_score else 'html',
                    display_name=case_name,
                    graded=graded,
                    weight=weight,
                )
                self.graded_score_weight_blocks[(graded, has_score, weight)] = block

    def setUp(self):
        super(TestProblemTypeAccess, self).setUp()
        self.audit_user = UserFactory.create()
        self.enrollment = CourseEnrollmentFactory.create(user=self.audit_user, course_id=self.course.id, mode='audit')

    def assert_block_is_gated(self, block, is_gated):
        '''
        This functions asserts whether the passed in block is gated by content type gating.
        This is determined by checking whether the has_access method called the IncorrectPartitionGroupError.
        This error gets swallowed up and is raised as a 404, which is why we are checking for a 404 being raised.
        However, the 404 could also be caused by other errors, which is why the actual assertion is checking
        whether the IncorrectPartitionGroupError was called.
        '''
        fake_request = Mock()

        with patch.object(IncorrectPartitionGroupError, '__init__',
                          wraps=IncorrectPartitionGroupError.__init__) as mock_access_error:
            if is_gated:
                with self.assertRaises(Http404):
                    block = load_single_xblock(fake_request, self.audit_user.id, unicode(self.course.id),
                                               unicode(block.scope_ids.usage_id), course=None)
                # check that has_access raised the IncorrectPartitionGroupError in order to gate the block
                self.assertTrue(mock_access_error.called)
            else:
                block = load_single_xblock(fake_request, self.audit_user.id, unicode(self.course.id),
                                           unicode(block.scope_ids.usage_id), course=None)
                # check that has_access did not raise the IncorrectPartitionGroupError thereby not gating the block
                self.assertFalse(mock_access_error.called)

    def test_lti_audit_access(self):
        """
        LTI stands for learning tools interoperability and is a 3rd party iframe that pulls in learning content from
        outside sources. This tests that audit users cannot see LTI components with graded content but can see the LTI
        components which do not have graded content.
        """
        self.assert_block_is_gated(self.lti_block, True)
        self.assert_block_is_gated(self.lti_block_not_scored, False)

    @ddt.data(
        *PROBLEM_TYPES
    )
    def test_audit_fails_access_graded_problems(self, prob_type):
        block = self.problem_dict[prob_type]
        is_gated = True
        self.assert_block_is_gated(block, is_gated)

    @ddt.data(
        *GRADED_SCORE_WEIGHT_TEST_CASES
    )
    @ddt.unpack
    def test_graded_score_weight_values(self, graded, has_score, weight, is_gated):
        # Verify that graded, has_score and weight must all be true for a component to be gated
        block = self.graded_score_weight_blocks[(graded, has_score, weight)]
        self.assert_block_is_gated(block, is_gated)
