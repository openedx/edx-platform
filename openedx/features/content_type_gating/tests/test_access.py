"""
Test audit user's access to various content based on content-gating features.
"""

import ddt
from django.conf import settings
from django.test.client import RequestFactory
from django.test.utils import override_settings
from django.urls import reverse
from mock import patch

from course_modes.tests.factories import CourseModeFactory
from lms.djangoapps.courseware.module_render import load_single_xblock
from openedx.core.djangoapps.waffle_utils.testutils import override_waffle_flag
from openedx.core.lib.url_utils import quote_slashes
from openedx.features.content_type_gating.partitions import CONTENT_GATING_PARTITION_ID
from openedx.features.course_duration_limits.config import CONTENT_TYPE_GATING_FLAG
from student.roles import CourseInstructorRole, CourseStaffRole
from student.tests.factories import (
    AdminFactory,
    CourseAccessRoleFactory,
    CourseEnrollmentFactory,
    UserFactory,
    TEST_PASSWORD
)
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory


@ddt.ddt
@override_waffle_flag(CONTENT_TYPE_GATING_FLAG, True)
@override_settings(FIELD_OVERRIDE_PROVIDERS=(
    'openedx.features.content_type_gating.field_override.ContentTypeGatingFieldOverride',
))
class TestProblemTypeAccess(SharedModuleStoreTestCase):

    PROBLEM_TYPES = ['problem', 'openassessment', 'drag-and-drop-v2', 'done', 'edx_sga']
    # 'html' is a component that just displays html, in these tests it is used to test that users who do not have access
    # to graded problems still have access to non-problems
    COMPONENT_TYPES = PROBLEM_TYPES + ['html']
    MODE_TYPES = ['credit', 'honor', 'audit', 'verified', 'professional', 'no-id-professional']

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
    def setUpClass(cls):
        super(TestProblemTypeAccess, cls).setUpClass()
        cls.factory = RequestFactory()

        cls.courses = {}

        # default course is used for most tests, it includes an audit and verified track and all the problem types
        # defined in 'PROBLEM_TYPES' and 'GRADED_SCORE_WEIGHT_TEST_CASES'
        cls.courses['default'] = cls._create_course(
            run='testcourse1',
            display_name='Test Course Title',
            modes=['audit', 'verified'],
            component_types=cls.COMPONENT_TYPES
        )
        # because default course is used for most tests self.course and self.problem_dict are set for ease of reference
        cls.course = cls.courses['default']['course']
        cls.blocks_dict = cls.courses['default']['blocks']

        # Create components with the cartesian product of possible values of
        # graded/has_score/weight for the test_graded_score_weight_values test.
        cls.graded_score_weight_blocks = {}
        for graded, has_score, weight, gated in cls.GRADED_SCORE_WEIGHT_TEST_CASES:
            case_name = ' Graded: ' + str(graded) + ' Has Score: ' + str(has_score) + ' Weight: ' + str(weight)
            block = ItemFactory.create(
                parent=cls.blocks_dict['vertical'],
                # has_score is determined by XBlock type. It is not a value set on an instance of an XBlock.
                # Therefore, we create a problem component when has_score is True
                # and an html component when has_score is False.
                category='problem' if has_score else 'html',
                display_name=case_name,
                graded=graded,
                weight=weight,
            )
            cls.graded_score_weight_blocks[(graded, has_score, weight)] = block

        # add LTI blocks to default course
        cls.blocks_dict['lti_block'] = ItemFactory.create(
            parent=cls.blocks_dict['vertical'],
            category='lti_consumer',
            display_name='lti_consumer',
            has_score=True,
            graded=True,
        )
        cls.blocks_dict['lti_block_not_scored'] = ItemFactory.create(
            parent=cls.blocks_dict['vertical'],
            category='lti_consumer',
            display_name='lti_consumer_2',
            has_score=False,
        )

        # add ungraded problem for xblock_handler test
        cls.blocks_dict['graded_problem'] = ItemFactory.create(
            parent=cls.blocks_dict['vertical'],
            category='problem',
            display_name='graded_problem',
            graded=True,
        )
        cls.blocks_dict['ungraded_problem'] = ItemFactory.create(
            parent=cls.blocks_dict['vertical'],
            category='problem',
            display_name='ungraded_problem',
            graded=False,
        )

        cls.blocks_dict['audit_visible_graded_problem'] = ItemFactory.create(
            parent=cls.blocks_dict['vertical'],
            category='problem',
            display_name='audit_visible_graded_problem',
            graded=True,
            group_access={
                CONTENT_GATING_PARTITION_ID: [
                    settings.CONTENT_TYPE_GATE_GROUP_IDS['limited_access'],
                    settings.CONTENT_TYPE_GATE_GROUP_IDS['full_access']
                ]
            },
        )

        # audit_only course only has an audit track available
        cls.courses['audit_only'] = cls._create_course(
            run='audit_only_course_run_1',
            display_name='Audit Only Test Course Title',
            modes=['audit'],
            component_types=['problem', 'html']
        )

        # all_track_types course has all track types defined in MODE_TYPES
        cls.courses['all_track_types'] = cls._create_course(
            run='all_track_types_run_1',
            display_name='All Track/Mode Types Test Course Title',
            modes=cls.MODE_TYPES,
            component_types=['problem', 'html']
        )

    def setUp(self):
        super(TestProblemTypeAccess, self).setUp()

        # enroll all users into the all track types course
        self.users = {}
        for mode_type in self.MODE_TYPES:
            self.users[mode_type] = UserFactory.create()
            CourseEnrollmentFactory.create(
                user=self.users[mode_type],
                course_id=self.courses['all_track_types']['course'].id,
                mode=mode_type
            )

        # create audit_user for ease of reference
        self.audit_user = self.users['audit']

        # enroll audit and verified users into default course
        for mode_type in ['audit', 'verified']:
            CourseEnrollmentFactory.create(
                user=self.users[mode_type],
                course_id=self.course.id,
                mode=mode_type
            )

        # enroll audit user into the audit_only course
        CourseEnrollmentFactory.create(
            user=self.audit_user,
            course_id=self.courses['audit_only']['course'].id,
            mode='audit'
        )

    @classmethod
    def _create_course(cls, run, display_name, modes, component_types):
        """
        Helper method to create a course

        Arguments:
            run (str): name of course run
            display_name (str): display name of course
            modes (list of str): list of modes/tracks this course should have
            component_types (list of str): list of problem types this course should have

        Returns:
             (dict): {
                'course': (CourseDescriptorWithMixins): course definition
                'blocks': (dict) {
                    'block_category_1': XBlock representing that block,
                    'block_category_2': XBlock representing that block,
                    ....
             }

        """
        course = CourseFactory.create(run=run, display_name=display_name)

        for mode in modes:
            CourseModeFactory.create(course_id=course.id, mode_slug=mode)

        with cls.store.bulk_operations(course.id):
            blocks_dict = {}
            chapter = ItemFactory.create(
                parent=course,
                display_name='Overview'
            )
            blocks_dict['chapter'] = ItemFactory.create(
                parent=course,
                category='chapter',
                display_name='Week 1'
            )
            blocks_dict['sequential'] = ItemFactory.create(
                parent=chapter,
                category='sequential',
                display_name='Lesson 1'
            )
            blocks_dict['vertical'] = ItemFactory.create(
                parent=blocks_dict['sequential'],
                category='vertical',
                display_name='Lesson 1 Vertical - Unit 1'
            )

            for component_type in component_types:
                block = ItemFactory.create(
                    parent=blocks_dict['vertical'],
                    category=component_type,
                    display_name=component_type,
                    graded=True,
                )
                blocks_dict[component_type] = block

            return {
                'course': course,
                'blocks': blocks_dict,
            }

    @patch("crum.get_current_request")
    def _assert_block_is_gated(self, mock_get_current_request, block, is_gated, user_id, course_id):
        """
        Asserts that a block in a specific course is gated for a specific user

        Arguments:
            block: some sort of xblock descriptor, must implement .scope_ids.usage_id
            is_gated (bool): if True, this user is expected to be gated from this block
            user_id (int): id of user
            course_id (CourseLocator): id of course
            view_name (str): type of view for the block, if not set will default to 'student_view'
        """
        fake_request = self.factory.get('')
        mock_get_current_request.return_value = fake_request

        # Load a block we know will pass access control checks
        vertical_xblock = load_single_xblock(
            request=fake_request,
            user_id=user_id,
            course_id=unicode(course_id),
            usage_key_string=unicode(self.blocks_dict['vertical'].scope_ids.usage_id),
            course=None
        )
        runtime = vertical_xblock.runtime

        # This method of fetching the block from the descriptor bypassess access checks
        problem_block = runtime.get_module(block)

        # Attempt to render the block, this should return different fragments if the content is gated or not.
        frag = runtime.render(problem_block, 'student_view')
        if is_gated:
            assert 'content-paywall' in frag.content
        else:
            assert 'content-paywall' not in frag.content

    @ddt.data(
        ('problem', True),
        ('openassessment', True),
        ('drag-and-drop-v2', True),
        ('done', True),
        ('edx_sga', True),
        ('lti_block', True),
        ('ungraded_problem', False),
        ('lti_block_not_scored', False),
        ('audit_visible_graded_problem', False),
    )
    @ddt.unpack
    def test_access_to_problems(self, prob_type, is_gated):
        self._assert_block_is_gated(
            block=self.blocks_dict[prob_type],
            user_id=self.users['audit'].id,
            course_id=self.course.id,
            is_gated=is_gated
        )
        self._assert_block_is_gated(
            block=self.blocks_dict[prob_type],
            user_id=self.users['verified'].id,
            course_id=self.course.id,
            is_gated=False
        )

    @ddt.data(
        *GRADED_SCORE_WEIGHT_TEST_CASES
    )
    @ddt.unpack
    def test_graded_score_weight_values(self, graded, has_score, weight, is_gated):
        # Verify that graded, has_score and weight must all be true for a component to be gated
        block = self.graded_score_weight_blocks[(graded, has_score, weight)]
        self._assert_block_is_gated(
            block=block,
            user_id=self.audit_user.id,
            course_id=self.course.id,
            is_gated=is_gated
        )

    @ddt.data(
        ('audit', 'problem', 'default', True),
        ('verified', 'problem', 'default', False),
        ('audit', 'html', 'default', False),
        ('verified', 'html', 'default', False),
        ('audit', 'problem', 'audit_only', False),
        ('audit', 'html', 'audit_only', False),
        ('credit', 'problem', 'all_track_types', False),
        ('credit', 'html', 'all_track_types', False),
        ('honor', 'problem', 'all_track_types', False),
        ('honor', 'html', 'all_track_types', False),
        ('audit', 'problem', 'all_track_types', True),
        ('audit', 'html', 'all_track_types', False),
        ('verified', 'problem', 'all_track_types', False),
        ('verified', 'html', 'all_track_types', False),
        ('professional', 'problem', 'all_track_types', False),
        ('professional', 'html', 'all_track_types', False),
        ('no-id-professional', 'problem', 'all_track_types', False),
        ('no-id-professional', 'html', 'all_track_types', False),
    )
    @ddt.unpack
    def test_access_based_on_track(self, user_track, component_type, course, is_gated):
        """
         If a user is enrolled as an audit user they should not have access to graded problems, unless there is no paid
         track option.  All paid type tracks should have access to all types of content.
         All users should have access to non-problem component types, the 'html' components test that.
         """
        self._assert_block_is_gated(
            block=self.courses[course]['blocks'][component_type],
            user_id=self.users[user_track].id,
            course_id=self.courses[course]['course'].id,
            is_gated=is_gated,
        )

    @ddt.data(
        ('problem', 'graded_problem', 'audit', 404),
        ('problem', 'graded_problem', 'verified', 200),
        ('problem', 'ungraded_problem', 'audit', 200),
        ('problem', 'ungraded_problem', 'verified', 200),
    )
    @ddt.unpack
    def test_xblock_handlers(self, xblock_type, xblock_name, user, status_code):
        """
        Test the ajax calls to the problem xblock to ensure the LMS is sending back
        the expected response codes on requests when content is gated for audit users
        (404) and when it is available to audit users (200). Content is always available
        to verified users.
        """
        problem_location = self.course.id.make_usage_key(xblock_type, xblock_name)
        url = reverse(
            'xblock_handler',
            kwargs={
                'course_id': unicode(self.course.id),
                'usage_id': quote_slashes(unicode(problem_location)),
                'handler': 'xmodule_handler',
                'suffix': 'problem_show',
            }
        )
        self.client.login(username=self.users[user].username, password=TEST_PASSWORD)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status_code)

    def test_access_course_team_users(self):
        """
        Test that members of the course team do not lose access to graded content
        """
        # There are two types of course team members: instructor and staff
        # they have different privileges, but for the purpose of this test the important thing is that they should both
        # have access to all graded content
        instructor = UserFactory.create()
        CourseInstructorRole(self.course.id).add_users(instructor)
        staff = UserFactory.create()
        CourseStaffRole(self.course.id).add_users(staff)

        # assert that all course team members have access to graded content
        for course_team_member in [instructor, staff]:
            self._assert_block_is_gated(
                block=self.blocks_dict['problem'],
                user_id=course_team_member.id,
                course_id=self.course.id,
                is_gated=False
            )
