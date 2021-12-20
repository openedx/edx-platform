"""
Unit tests for course_goals.views methods.
"""


from unittest import mock

from django.test.utils import override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.tests.factories import UserFactory
from lms.djangoapps.course_goals.models import CourseGoal
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.tests.factories import CourseFactory  # lint-amnesty, pylint: disable=wrong-import-order

EVENT_NAME_ADDED = 'edx.course.goal.added'
EVENT_NAME_UPDATED = 'edx.course.goal.updated'


class TestCourseGoalsAPI(SharedModuleStoreTestCase):
    """
    Testing the Course Goals API.
    """

    def setUp(self):
        # Create a course with a verified track
        super().setUp()
        self.course = CourseFactory.create(emit_signals=True)

        self.user = UserFactory.create(username='john', email='lennon@thebeatles.com', password='password')
        CourseEnrollment.enroll(self.user, self.course.id)

        self.client = APIClient(enforce_csrf_checks=True)
        self.client.login(username=self.user.username, password=self.user.password)
        self.client.force_authenticate(user=self.user)

        self.apiUrl = reverse('course_goals_api:v0:course_goal-list')

    @mock.patch('lms.djangoapps.course_goals.handlers.segment.track')
    @override_settings(LMS_SEGMENT_KEY="foobar")
    def test_add_valid_goal(self, segment_call):
        """ Ensures a correctly formatted post succeeds."""
        response = self.post_course_goal(valid=True, goal_key='certify')
        segment_call.assert_called_once_with(self.user.id, EVENT_NAME_ADDED, {
            'courserun_key': str(self.course.id),
            'goal_key': 'certify',
            'days_per_week': 0,
            'subscribed_to_reminders': False,
        })
        assert response.status_code == 201

        current_goals = CourseGoal.objects.filter(user=self.user, course_key=self.course.id)
        assert len(current_goals) == 1
        assert current_goals[0].goal_key == 'certify'

    def test_add_invalid_goal(self):
        """ Ensures an incorrectly formatted post does not succeed. """
        response = self.post_course_goal(valid=False)
        assert response.status_code == 400
        assert len(CourseGoal.objects.filter(user=self.user, course_key=self.course.id)) == 0

    def test_add_without_goal_key(self):
        """ Ensures if no goal key provided, post does not succeed. """
        response = self.post_course_goal(goal_key=None)
        assert len(CourseGoal.objects.filter(user=self.user, course_key=self.course.id)) == 0
        self.assertContains(
            response=response,
            text='Please provide a valid goal key from following options.',
            status_code=400
        )

    @mock.patch('lms.djangoapps.course_goals.handlers.segment.track')
    @override_settings(LMS_SEGMENT_KEY="foobar")
    def test_update_goal(self, segment_call):
        """ Ensures that repeated course goal post events do not create new instances of the goal. """
        self.post_course_goal(valid=True, goal_key='explore')
        self.post_course_goal(valid=True, goal_key='certify')
        self.post_course_goal(valid=True, goal_key='unsure')

        segment_call.assert_any_call(self.user.id, EVENT_NAME_ADDED, {
            'courserun_key': str(self.course.id), 'goal_key': 'explore',
            'days_per_week': 0,
            'subscribed_to_reminders': False,
        })
        segment_call.assert_any_call(self.user.id, EVENT_NAME_UPDATED, {
            'courserun_key': str(self.course.id), 'goal_key': 'certify',
            'days_per_week': 0,
            'subscribed_to_reminders': False,
        })
        segment_call.assert_any_call(self.user.id, EVENT_NAME_UPDATED, {
            'courserun_key': str(self.course.id), 'goal_key': 'unsure',
            'days_per_week': 0,
            'subscribed_to_reminders': False,
        })
        current_goals = CourseGoal.objects.filter(user=self.user, course_key=self.course.id)
        assert len(current_goals) == 1
        assert current_goals[0].goal_key == 'unsure'

    def post_course_goal(self, valid=True, goal_key='certify'):
        """
        Sends a post request to set a course goal and returns the response.
        """
        goal_key = goal_key if valid else 'invalid'
        post_data = {
            'course_key': self.course.id,
            'user': self.user.username,
        }
        if goal_key:
            post_data['goal_key'] = goal_key

        response = self.client.post(self.apiUrl, post_data)
        return response
