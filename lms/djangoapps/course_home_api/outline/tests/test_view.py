"""
Tests for Outline Tab API in the Course Home API
"""

import itertools
from datetime import datetime, timedelta, timezone
from lms.djangoapps.grades.course_grade_factory import CourseGradeFactory
from unittest.mock import Mock, patch  # lint-amnesty, pylint: disable=wrong-import-order

import ddt  # lint-amnesty, pylint: disable=wrong-import-order
import json  # lint-amnesty, pylint: disable=wrong-import-order
from django.conf import settings  # lint-amnesty, pylint: disable=wrong-import-order
from django.urls import reverse  # lint-amnesty, pylint: disable=wrong-import-order
from edx_toggles.toggles.testutils import override_waffle_flag  # lint-amnesty, pylint: disable=wrong-import-order

from cms.djangoapps.contentstore.outlines import update_outline_from_modulestore
from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.course_modes.tests.factories import CourseModeFactory
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.roles import CourseInstructorRole
from common.djangoapps.student.tests.factories import UserFactory
from lms.djangoapps.course_home_api.tests.utils import BaseCourseHomeTests
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.content.learning_sequences.api import replace_course_outline
from openedx.core.djangoapps.content.learning_sequences.data import CourseOutlineData, CourseVisibility
from openedx.core.djangoapps.course_date_signals.utils import MIN_DURATION
from openedx.core.djangoapps.user_api.preferences.api import set_user_preference
from openedx.core.djangoapps.user_api.tests.factories import UserCourseTagFactory
from openedx.features.course_duration_limits.models import CourseDurationLimitConfig
from openedx.features.course_experience import (
    COURSE_ENABLE_UNENROLLED_ACCESS_FLAG,
    DISPLAY_COURSE_SOCK_FLAG,
    ENABLE_COURSE_GOALS
)
from openedx.features.discounts.applicability import DISCOUNT_APPLICABILITY_FLAG
from xmodule.course_block import COURSE_VISIBILITY_PUBLIC, COURSE_VISIBILITY_PUBLIC_OUTLINE  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.tests.factories import CourseFactory, BlockFactory  # lint-amnesty, pylint: disable=wrong-import-order


@ddt.ddt
class OutlineTabTestViews(BaseCourseHomeTests):
    """
    Tests for the Outline Tab API
    """

    def setUp(self):
        super().setUp()
        self.url = reverse('course-home:outline-tab', args=[self.course.id])

    def update_course_and_overview(self):
        self.update_course(self.course, self.user.id)
        CourseOverview.load_from_module_store(self.course.id)

    @override_waffle_flag(ENABLE_COURSE_GOALS, active=True)
    @ddt.data(CourseMode.AUDIT, CourseMode.VERIFIED)
    def test_get_authenticated_enrolled_user(self, enrollment_mode):
        CourseEnrollment.enroll(self.user, self.course.id, enrollment_mode)
        response = self.client.get(self.url)
        assert response.status_code == 200

        course_tools = response.data.get('course_tools')
        assert course_tools
        assert course_tools[0]['analytics_id'] == 'edx.bookmarks'

        dates_widget = response.data.get('dates_widget')
        assert dates_widget
        date_blocks = dates_widget.get('course_date_blocks')
        assert all((block.get('title') != '') for block in date_blocks)
        assert all(block.get('date') for block in date_blocks)

        resume_course = response.data.get('resume_course')
        resume_course_url = resume_course.get('url')
        if resume_course_url:
            assert 'http://' in resume_course_url

    @ddt.data(True, False)
    def test_get_authenticated_user_not_enrolled(self, has_previously_enrolled):
        if has_previously_enrolled:
            # Create an enrollment, then unenroll to set is_active to False
            CourseEnrollment.enroll(self.user, self.course.id)
            CourseEnrollment.unenroll(self.user, self.course.id)
        response = self.client.get(self.url)
        assert response.status_code == 200

        course_tools = response.data.get('course_tools')
        assert len(course_tools) == 0

        dates_widget = response.data.get('dates_widget')
        assert dates_widget
        date_blocks = dates_widget.get('course_date_blocks')
        assert all((block.get('title') != '') for block in date_blocks)
        assert all(block.get('date') for block in date_blocks)

    def test_get_unauthenticated_user(self):
        self.client.logout()
        response = self.client.get(self.url)
        assert response.status_code == 200

        course_blocks = response.data.get('course_blocks')
        assert course_blocks is None

        course_tools = response.data.get('course_tools')
        assert len(course_tools) == 0

        dates_widget = response.data.get('dates_widget')
        assert dates_widget
        date_blocks = dates_widget.get('course_date_blocks')
        assert len(date_blocks) == 0

    def test_masquerade(self):
        user = UserFactory()
        set_user_preference(user, 'time_zone', 'Asia/Tokyo')
        CourseEnrollment.enroll(user, self.course.id)

        self.switch_to_staff()  # needed for masquerade

        # Sanity check on our normal user
        assert self.client.get(self.url).data['dates_widget']['user_timezone'] is None

        # Now switch users and confirm we get a different result
        self.update_masquerade(username=user.username)
        assert self.client.get(self.url).data['dates_widget']['user_timezone'] == 'Asia/Tokyo'

    def test_course_staff_can_see_non_user_specific_content_in_masquerade(self):
        """
        Test that course staff can see the outline and other non-user-specific content when masquerading as a learner
        """
        self.store.create_item(
            self.user.id, self.course.id, 'course_info', 'handouts', fields={'data': '<p>Handouts</p>'}
        )

        instructor = UserFactory(
            username='instructor',
            email='instructor@example.com',
            password='foo',
            is_staff=False
        )
        CourseInstructorRole(self.course.id).add_users(instructor)
        self.client.login(username=instructor, password='foo')
        self.update_masquerade(role="student")
        response = self.client.get(self.url)
        assert response.data['course_blocks'] is not None
        assert response.data['handouts_html'] is not None

    @override_waffle_flag(COURSE_ENABLE_UNENROLLED_ACCESS_FLAG, active=True)
    def test_handouts(self):
        CourseEnrollment.enroll(self.user, self.course.id)
        self.store.create_item(self.user.id, self.course.id, 'course_info', 'handouts', fields={'data': '<p>Hi</p>'})
        assert self.client.get(self.url).data['handouts_html'] == '<p>Hi</p>'

    def test_get_unknown_course(self):
        url = reverse('course-home:outline-tab', args=['course-v1:unknown+course+2T2020'])
        response = self.client.get(url)
        assert response.status_code == 404

    @ddt.data(True, False)
    def test_welcome_message(self, welcome_message_is_dismissed):
        CourseEnrollment.enroll(self.user, self.course.id)
        self.store.create_item(
            self.user.id, self.course.id,
            'course_info',
            'updates',
            fields={
                'items': [{
                    'content': '<p>Welcome</p>',
                    'status': 'visible',
                    'date': 'July 23, 2020',
                    'id': 1
                }]
            }
        )
        UserCourseTagFactory(
            user=self.user,
            course_id=self.course.id,
            key='view-welcome-message',
            value=not welcome_message_is_dismissed
        )
        welcome_message_html = self.client.get(self.url).data['welcome_message_html']
        assert welcome_message_html == (None if welcome_message_is_dismissed else '<p>Welcome</p>')

    def test_offer(self):
        CourseEnrollment.enroll(self.user, self.course.id)

        response = self.client.get(self.url)
        assert response.data['offer'] is None

        with override_waffle_flag(DISCOUNT_APPLICABILITY_FLAG, active=True):
            response = self.client.get(self.url)

            # Just a quick spot check that the dictionary looks like what we expect
            assert response.data['offer']['code'] == 'EDXWELCOME'

    def test_access_expiration(self):
        enrollment = CourseEnrollment.enroll(self.user, self.course.id, CourseMode.VERIFIED)
        CourseDurationLimitConfig.objects.create(enabled=True, enabled_as_of=datetime(2018, 1, 1))

        response = self.client.get(self.url)
        assert response.data['access_expiration'] is None

        enrollment.update_enrollment(CourseMode.AUDIT)
        response = self.client.get(self.url)

        # Just a quick spot check that the dictionary looks like what we expect
        deadline = enrollment.created + MIN_DURATION
        assert response.data['access_expiration']['expiration_date'] == deadline

    @override_waffle_flag(ENABLE_COURSE_GOALS, active=True)
    def test_post_course_goal(self):
        """ Test that the api returns the correct response when saving a goal """
        CourseEnrollment.enroll(self.user, self.course.id, CourseMode.AUDIT)

        post_data = json.dumps({
            'course_id': str(self.course.id),
            'days_per_week': 1,
            'subscribed_to_reminders': True,
        })
        post_course_goal_response = self.client.post(
            reverse('course-home:save-course-goal'),
            post_data,
            content_type='application/json',
        )
        assert post_course_goal_response.status_code == 200

        response = self.client.get(self.url)
        assert response.status_code == 200

        course_goals = response.json()['course_goals']
        expected_course_goals = {
            'selected_goal': {
                'days_per_week': 1,
                'subscribed_to_reminders': True,
            },
            'weekly_learning_goal_enabled': True,
        }
        assert course_goals == expected_course_goals

    @patch.dict('django.conf.settings.FEATURES', {'ENABLE_SPECIAL_EXAMS': True})
    @patch('lms.djangoapps.course_api.blocks.transformers.milestones.get_attempt_status_summary')
    def test_proctored_exam(self, mock_summary):
        course = CourseFactory.create(
            org='edX',
            course='900',
            run='test_run',
            enable_proctored_exams=True,
            proctoring_provider=settings.PROCTORING_BACKENDS['DEFAULT'],
        )
        chapter = BlockFactory.create(parent=course, category='chapter', display_name='Test Section')
        sequence = BlockFactory.create(
            parent=chapter,
            category='sequential',
            display_name='Test Proctored Exam',
            graded=True,
            is_time_limited=True,
            default_time_limit_minutes=10,
            is_practice_exam=True,
            due=datetime.now(),
            exam_review_rules='allow_use_of_paper',
            hide_after_due=False,
            is_onboarding_exam=False,
        )
        sequence.is_proctored_exam = True
        update_outline_from_modulestore(course.id)
        mock_summary.return_value = {
            'short_description': 'My Exam',
            'suggested_icon': 'fa-foo-bar',
        }
        url = reverse('course-home:outline-tab', args=[course.id])

        CourseEnrollment.enroll(self.user, course.id)
        response = self.client.get(url)
        assert response.status_code == 200

        exam_data = response.data['course_blocks']['blocks'][str(sequence.location)]
        assert not exam_data['complete']
        assert exam_data['description'] == 'My Exam'
        assert exam_data['display_name'] == 'Test Proctored Exam'
        assert exam_data['due'] is not None
        assert exam_data['icon'] == 'fa-foo-bar'

    def test_assignment(self):
        course = CourseFactory.create()
        with self.store.bulk_operations(course.id):
            chapter = BlockFactory.create(category='chapter', parent_location=course.location)
            sequential = BlockFactory.create(display_name='Test', category='sequential', graded=True, has_score=True,
                                             parent_location=chapter.location)
            BlockFactory.create(category='problem', graded=True, has_score=True, parent_location=sequential.location)
            BlockFactory.create(category='problem', graded=True, has_score=True, parent_location=sequential.location)
            sequential2 = BlockFactory.create(display_name='Ungraded', category='sequential',
                                              parent_location=chapter.location)
            BlockFactory.create(category='problem', parent_location=sequential2.location)
        update_outline_from_modulestore(course.id)
        url = reverse('course-home:outline-tab', args=[course.id])

        CourseEnrollment.enroll(self.user, course.id)
        response = self.client.get(url)
        assert response.status_code == 200

        exam_data = response.data['course_blocks']['blocks'][str(sequential.location)]
        assert exam_data['display_name'] == 'Test (2 Questions)'
        assert exam_data['icon'] == 'fa-pencil-square-o'

        ungraded_data = response.data['course_blocks']['blocks'][str(sequential2.location)]
        assert ungraded_data['display_name'] == 'Ungraded'
        assert ungraded_data['icon'] is None

    @override_waffle_flag(COURSE_ENABLE_UNENROLLED_ACCESS_FLAG, active=True)
    @patch('lms.djangoapps.course_home_api.outline.views.generate_offer_data', new=Mock(return_value={'a': 1}))
    @patch('lms.djangoapps.course_home_api.outline.views.get_access_expiration_data', new=Mock(return_value={'b': 1}))
    @ddt.data(*itertools.product([True, False], [True, False],
                                 [None, COURSE_VISIBILITY_PUBLIC, COURSE_VISIBILITY_PUBLIC_OUTLINE]))
    @ddt.unpack
    def test_visibility(self, is_enrolled, is_staff, course_visibility):
        if is_enrolled:
            CourseEnrollment.enroll(self.user, self.course.id)
        if is_staff:
            self.user.is_staff = True
            self.user.save()
        if course_visibility:
            self.course.course_visibility = course_visibility
            self.update_course_and_overview()

        self.store.create_item(
            self.user.id, self.course.id, 'course_info', 'handouts', fields={'data': '<p>Handouts</p>'}
        )
        self.store.create_item(self.user.id, self.course.id, 'course_info', 'updates', fields={
            'items': [{
                'content': '<p>Welcome</p>',
                'status': 'visible',
                'date': 'July 23, 2020',
                'id': 1,
            }]
        })

        show_enrolled = is_enrolled or is_staff
        is_public = course_visibility == COURSE_VISIBILITY_PUBLIC
        is_public_outline = course_visibility == COURSE_VISIBILITY_PUBLIC_OUTLINE

        data = self.client.get(self.url).data
        assert (data['course_blocks'] is not None) == (show_enrolled or is_public or is_public_outline)
        assert (data['handouts_html'] is not None) == (show_enrolled or is_public)
        assert (data['offer'] is not None) == show_enrolled
        assert (data['access_expiration'] is not None) == show_enrolled
        assert (data['resume_course']['url'] is not None) == show_enrolled

    @ddt.data(True, False)
    def test_can_show_upgrade_sock(self, sock_enabled):
        with override_waffle_flag(DISPLAY_COURSE_SOCK_FLAG, active=sock_enabled):
            response = self.client.get(self.url)
            assert response.data['can_show_upgrade_sock'] == sock_enabled

    def test_verified_mode(self):
        enrollment = CourseEnrollment.enroll(self.user, self.course.id)
        CourseDurationLimitConfig.objects.create(enabled=True, enabled_as_of=datetime(2018, 1, 1))

        response = self.client.get(self.url)
        assert response.data['verified_mode'] == {
            'access_expiration_date': (enrollment.created + MIN_DURATION),
            'currency': 'USD',
            'currency_symbol': '$',
            'price': 149,
            'sku': 'ABCD1234',
            'upgrade_url': '/dashboard'
        }

    def test_hide_learning_sequences(self):
        """
        Check that Learning Sequences filters out sequences.
        """
        CourseEnrollment.enroll(self.user, self.course.id, CourseMode.VERIFIED)

        # Normal behavior: the sequence exists
        response = self.client.get(self.url)
        assert response.status_code == 200
        blocks = response.data['course_blocks']['blocks']
        seq_block_id = next(
            block_id
            for block_id, block in blocks.items()
            if block['type'] == 'sequential'
        )

        # With a course outline loaded, the same sequence is removed.
        new_learning_seq_outline = CourseOutlineData(
            course_key=self.course.id,
            title="Test Course Outline!",
            published_at=datetime(2021, 6, 14, tzinfo=timezone.utc),
            published_version="5ebece4b69dd593d82fe2022",
            entrance_exam_id=None,
            days_early_for_beta=None,
            sections=[],
            self_paced=False,
            course_visibility=CourseVisibility.PRIVATE  # pylint: disable=protected-access
        )
        replace_course_outline(new_learning_seq_outline)
        response = self.client.get(self.url)
        blocks = response.data['course_blocks']['blocks']
        assert seq_block_id not in blocks

    def test_user_has_passing_grade(self):
        CourseEnrollment.enroll(self.user, self.course.id)
        self.course._grading_policy['GRADE_CUTOFFS']['Pass'] = 0  # pylint: disable=protected-access
        self.update_course_and_overview()
        CourseGradeFactory().update(self.user, self.course)
        response = self.client.get(self.url)
        assert response.status_code == 200
        assert response.data['user_has_passing_grade'] is True

    def assert_can_enroll(self, can_enroll):
        response = self.client.get(self.url)
        assert response.status_code == 200
        assert response.data['enroll_alert']['can_enroll'] == can_enroll

    def test_can_enroll_basic(self):
        self.assert_can_enroll(True)

    def test_cannot_enroll_invitation_only(self):
        self.course.invitation_only = True
        self.update_course_and_overview()
        self.assert_can_enroll(False)

    def test_cannot_enroll_masters_only(self):
        CourseMode.objects.all().delete()
        CourseModeFactory(course_id=self.course.id, mode_slug=CourseMode.MASTERS)
        self.assert_can_enroll(False)

    def test_cannot_enroll_before_enrollment(self):
        self.course.enrollment_start = datetime.now(timezone.utc) + timedelta(days=1)
        self.update_course_and_overview()
        self.assert_can_enroll(False)

    def test_cannot_enroll_after_enrollment(self):
        self.course.enrollment_end = datetime.now(timezone.utc) - timedelta(days=1)
        self.update_course_and_overview()
        self.assert_can_enroll(False)

    def test_cannot_enroll_if_full(self):
        self.course.max_student_enrollments_allowed = 1
        self.update_course_and_overview()
        CourseEnrollment.enroll(UserFactory(), self.course.id)  # grr, some rando took our spot!
        self.assert_can_enroll(False)
