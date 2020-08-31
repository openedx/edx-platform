"""
Tests for Outline Tab API in the Course Home API
"""

from datetime import datetime

import ddt
from django.conf import settings
from django.urls import reverse
from mock import patch

from course_modes.models import CourseMode
from lms.djangoapps.course_home_api.tests.utils import BaseCourseHomeTests
from lms.djangoapps.course_home_api.toggles import COURSE_HOME_MICROFRONTEND, COURSE_HOME_MICROFRONTEND_OUTLINE_TAB
from openedx.core.djangoapps.user_api.preferences.api import set_user_preference
from openedx.core.djangoapps.user_api.tests.factories import UserCourseTagFactory
from openedx.features.course_experience import COURSE_ENABLE_UNENROLLED_ACCESS_FLAG, ENABLE_COURSE_GOALS
from student.models import CourseEnrollment
from student.tests.factories import UserFactory
from xmodule.course_module import COURSE_VISIBILITY_PUBLIC
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory


@ddt.ddt
class OutlineTabTestViews(BaseCourseHomeTests):
    """
    Tests for the Outline Tab API
    """

    def setUp(self):
        super().setUp()
        self.url = reverse('course-home-outline-tab', args=[self.course.id])

    @ENABLE_COURSE_GOALS.override(active=True)
    @COURSE_HOME_MICROFRONTEND.override(active=True)
    @COURSE_HOME_MICROFRONTEND_OUTLINE_TAB.override(active=True)
    @ddt.data(CourseMode.AUDIT, CourseMode.VERIFIED)
    def test_get_authenticated_enrolled_user(self, enrollment_mode):
        CourseEnrollment.enroll(self.user, self.course.id, enrollment_mode)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        course_goals = response.data.get('course_goals')
        goal_options = course_goals['goal_options']
        if enrollment_mode == CourseMode.VERIFIED:
            self.assertEqual(goal_options, [])
        else:
            self.assertGreater(len(goal_options), 0)

            selected_goal = course_goals['selected_goal']
            self.assertIsNone(selected_goal)

        course_tools = response.data.get('course_tools')
        self.assertTrue(course_tools)
        self.assertEqual(course_tools[0]['analytics_id'], 'edx.bookmarks')

        dates_widget = response.data.get('dates_widget')
        self.assertTrue(dates_widget)
        date_blocks = dates_widget.get('course_date_blocks')
        self.assertTrue(all((block.get('title') != "") for block in date_blocks))
        self.assertTrue(all(block.get('date') for block in date_blocks))

        resume_course = response.data.get('resume_course')
        resume_course_url = resume_course.get('url')
        if resume_course_url:
            self.assertIn('http://', resume_course_url)

    @COURSE_HOME_MICROFRONTEND.override(active=True)
    @COURSE_HOME_MICROFRONTEND_OUTLINE_TAB.override(active=True)
    def test_get_authenticated_user_not_enrolled(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        course_goals = response.data.get('course_goals')
        self.assertEqual(course_goals['goal_options'], [])

        course_tools = response.data.get('course_tools')
        self.assertEqual(len(course_tools), 0)

        dates_widget = response.data.get('dates_widget')
        self.assertTrue(dates_widget)
        date_blocks = dates_widget.get('course_date_blocks')
        self.assertTrue(all((block.get('title') != "") for block in date_blocks))
        self.assertTrue(all(block.get('date') for block in date_blocks))

    @COURSE_HOME_MICROFRONTEND.override(active=True)
    @COURSE_HOME_MICROFRONTEND_OUTLINE_TAB.override(active=True)
    def test_get_unauthenticated_user(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    @COURSE_HOME_MICROFRONTEND.override(active=True)
    @COURSE_HOME_MICROFRONTEND_OUTLINE_TAB.override(active=True)
    def test_masquerade(self):
        user = UserFactory()
        set_user_preference(user, 'time_zone', 'Asia/Tokyo')
        CourseEnrollment.enroll(user, self.course.id)

        self.switch_to_staff()  # needed for masquerade

        # Sanity check on our normal user
        self.assertEqual(self.client.get(self.url).data['dates_widget']['user_timezone'], None)

        # Now switch users and confirm we get a different result
        self.update_masquerade(username=user.username)
        self.assertEqual(self.client.get(self.url).data['dates_widget']['user_timezone'], 'Asia/Tokyo')

    @COURSE_HOME_MICROFRONTEND.override(active=True)
    @COURSE_HOME_MICROFRONTEND_OUTLINE_TAB.override(active=True)
    @ddt.data(
        (True, True, True, True),  # happy path
        (True, False, False, True),  # is enrolled
        (False, True, False, True),  # is staff
        (False, False, True, True),  # public visibility
        (False, False, False, False),  # no access
    )
    @ddt.unpack
    @COURSE_ENABLE_UNENROLLED_ACCESS_FLAG.override()
    def test_handouts(self, is_enrolled, is_staff, is_public, handouts_visible):
        if is_enrolled:
            CourseEnrollment.enroll(self.user, self.course.id)
        if is_staff:
            self.user.is_staff = True
            self.user.save()
        if is_public:
            self.course.course_visibility = COURSE_VISIBILITY_PUBLIC
            self.course = self.update_course(self.course, self.user.id)

        self.store.create_item(self.user.id, self.course.id, 'course_info', 'handouts', fields={'data': '<p>Hi</p>'})

        handouts_html = self.client.get(self.url).data['handouts_html']
        self.assertEqual(handouts_html, '<p>Hi</p>' if handouts_visible else '')

    @COURSE_HOME_MICROFRONTEND.override(active=True)
    @COURSE_HOME_MICROFRONTEND_OUTLINE_TAB.override(active=True)
    def test_get_unknown_course(self):
        url = reverse('course-home-outline-tab', args=['course-v1:unknown+course+2T2020'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    @COURSE_HOME_MICROFRONTEND.override(active=True)
    @COURSE_HOME_MICROFRONTEND_OUTLINE_TAB.override(active=False)
    @ddt.data(CourseMode.AUDIT, CourseMode.VERIFIED)
    def test_waffle_flag_disabled(self, enrollment_mode):
        CourseEnrollment.enroll(self.user, self.course.id, enrollment_mode)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    @COURSE_HOME_MICROFRONTEND.override(active=True)
    @COURSE_HOME_MICROFRONTEND_OUTLINE_TAB.override(active=True)
    @ddt.data(True, False)
    def test_welcome_message(self, welcome_message_is_dismissed):
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
            value=False if welcome_message_is_dismissed else True
        )
        welcome_message_html = self.client.get(self.url).data['welcome_message_html']
        self.assertEqual(welcome_message_html, None if welcome_message_is_dismissed else '<p>Welcome</p>')

    @COURSE_HOME_MICROFRONTEND.override(active=True)
    @COURSE_HOME_MICROFRONTEND_OUTLINE_TAB.override(active=True)
    def test_offer_html(self):
        with patch('lms.djangoapps.course_home_api.outline.v1.views.generate_offer_html') as gen_html:
            html = '<div>Offer HTML</div>'
            gen_html.return_value = html
            self.assertEqual(self.client.get(self.url).data['offer_html'], html)

    @COURSE_HOME_MICROFRONTEND.override(active=True)
    @COURSE_HOME_MICROFRONTEND_OUTLINE_TAB.override(active=True)
    def test_course_expired_html(self):
        with patch('lms.djangoapps.course_home_api.outline.v1.views.generate_course_expired_message') as gen_html:
            html = '<div>Course expired HTML</div>'
            gen_html.return_value = html
            self.assertEqual(self.client.get(self.url).data['course_expired_html'], html)

    @ENABLE_COURSE_GOALS.override(active=True)
    @COURSE_HOME_MICROFRONTEND.override(active=True)
    @COURSE_HOME_MICROFRONTEND_OUTLINE_TAB.override(active=True)
    def test_post_course_goal(self):
        CourseEnrollment.enroll(self.user, self.course.id, CourseMode.AUDIT)

        post_data = {
            'course_id': self.course.id,
            'goal_key': 'certify'
        }
        post_course_goal_response = self.client.post(reverse('course-home-save-course-goal'), post_data)
        self.assertEqual(post_course_goal_response.status_code, 200)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        course_goals = response.data.get('course_goals')
        selected_goal = course_goals['selected_goal']
        self.assertIsNotNone(selected_goal)
        self.assertEqual(selected_goal['key'], 'certify')

    @COURSE_HOME_MICROFRONTEND.override(active=True)
    @COURSE_HOME_MICROFRONTEND_OUTLINE_TAB.override(active=True)
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
        chapter = ItemFactory.create(parent=course, category='chapter', display_name='Test Section')
        sequence = ItemFactory.create(
            parent=chapter,
            category='sequential',
            display_name='Test Proctored Exam',
            graded=True,
            is_time_limited=True,
            default_time_limit_minutes=10,
            is_proctored_exam=True,
            is_practice_exam=True,
            due=datetime.now(),
            exam_review_rules='allow_use_of_paper',
            hide_after_due=False,
            is_onboarding_exam=False,
        )
        mock_summary.return_value = {
            'short_description': 'My Exam',
            'suggested_icon': 'fa-foo-bar',
        }
        url = reverse('course-home-outline-tab', args=[course.id])

        CourseEnrollment.enroll(self.user, course.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        exam_data = response.data['course_blocks']['blocks'][str(sequence.location)]
        self.assertFalse(exam_data['complete'])
        self.assertEqual(exam_data['description'], 'My Exam')
        self.assertEqual(exam_data['display_name'], 'Test Proctored Exam')
        self.assertIsNotNone(exam_data['due'])
        self.assertEqual(exam_data['icon'], 'fa-foo-bar')

    @COURSE_HOME_MICROFRONTEND.override(active=True)
    @COURSE_HOME_MICROFRONTEND_OUTLINE_TAB.override(active=True)
    def test_assignment(self):
        course = CourseFactory.create()
        with self.store.bulk_operations(course.id):
            chapter = ItemFactory.create(category='chapter', parent_location=course.location)
            sequential = ItemFactory.create(display_name='Test', category='sequential', graded=True, has_score=True,
                                            parent_location=chapter.location)
            problem1 = ItemFactory.create(category='problem', graded=True, has_score=True,
                                          parent_location=sequential.location)
            problem2 = ItemFactory.create(category='problem', graded=True, has_score=True,
                                          parent_location=sequential.location)
            sequential2 = ItemFactory.create(display_name='Ungraded', category='sequential',
                                             parent_location=chapter.location)
        course.children = [chapter]
        chapter.children = [sequential, sequential2]
        sequential.children = [problem1, problem2]
        url = reverse('course-home-outline-tab', args=[course.id])

        CourseEnrollment.enroll(self.user, course.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        exam_data = response.data['course_blocks']['blocks'][str(sequential.location)]
        self.assertEqual(exam_data['display_name'], 'Test (2 Questions)')
        self.assertEqual(exam_data['icon'], 'fa-pencil-square-o')

        ungraded_data = response.data['course_blocks']['blocks'][str(sequential2.location)]
        self.assertEqual(ungraded_data['display_name'], 'Ungraded')
        self.assertIsNone(ungraded_data['icon'])
