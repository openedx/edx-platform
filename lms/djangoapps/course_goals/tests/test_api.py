"""
Unit tests for course_goals.api methods.
"""


import mock
from django.contrib.auth.models import User
from django.test.utils import override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from lms.djangoapps.course_goals.models import CourseGoal
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.track.tests import EventTrackingTestCase
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

TEST_PASSWORD = 'test'
EVENT_NAME_ADDED = 'edx.course.goal.added'
EVENT_NAME_UPDATED = 'edx.course.goal.updated'


class TestCourseGoalsAPI(EventTrackingTestCase, SharedModuleStoreTestCase):
    """
    Testing the Course Goals API.
    """

    def setUp(self):
        # Create a course with a verified track
        super(TestCourseGoalsAPI, self).setUp()
        self.course = CourseFactory.create(emit_signals=True)

        self.user = User.objects.create_user('john', 'lennon@thebeatles.com', 'password')
        CourseEnrollment.enroll(self.user, self.course.id)

        self.client = APIClient(enforce_csrf_checks=True)
        self.client.login(username=self.user.username, password=self.user.password)
        self.client.force_authenticate(user=self.user)

        self.apiUrl = reverse('course_goals_api:v0:course_goal-list')

    @mock.patch('lms.djangoapps.course_goals.views.segment.track')
    @override_settings(LMS_SEGMENT_KEY="foobar")
    def test_add_valid_goal(self, ga_call):
        """ Ensures a correctly formatted post succeeds."""
        response = self.post_course_goal(valid=True, goal_key='certify')
        self.assertEqual(self.get_event(-1)['name'], EVENT_NAME_ADDED)
        ga_call.assert_called_with(self.user.id, EVENT_NAME_ADDED)
        self.assertEqual(response.status_code, 201)

        current_goals = CourseGoal.objects.filter(user=self.user, course_key=self.course.id)
        self.assertEqual(len(current_goals), 1)
        self.assertEqual(current_goals[0].goal_key, 'certify')

    def test_add_invalid_goal(self):
        """ Ensures an incorrectly formatted post does not succeed. """
        response = self.post_course_goal(valid=False)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(CourseGoal.objects.filter(user=self.user, course_key=self.course.id)), 0)

    def test_add_without_goal_key(self):
        """ Ensures if no goal key provided, post does not succeed. """

        response = self.post_course_goal(goal_key=None)
        self.assertEqual(len(CourseGoal.objects.filter(user=self.user, course_key=self.course.id)), 0)
        self.assertContains(
            response=response,
            text='Please provide a valid goal key from following options.',
            status_code=400
        )

    @mock.patch('lms.djangoapps.course_goals.views.segment.track')
    @override_settings(LMS_SEGMENT_KEY="foobar")
    def test_update_goal(self, ga_call):
        """ Ensures that repeated course goal post events do not create new instances of the goal. """
        self.post_course_goal(valid=True, goal_key='explore')
        self.post_course_goal(valid=True, goal_key='certify')
        self.post_course_goal(valid=True, goal_key='unsure')
        self.assertEqual(self.get_event(-1)['name'], EVENT_NAME_UPDATED)

        ga_call.assert_called_with(self.user.id, EVENT_NAME_UPDATED)
        current_goals = CourseGoal.objects.filter(user=self.user, course_key=self.course.id)
        self.assertEqual(len(current_goals), 1)
        self.assertEqual(current_goals[0].goal_key, 'unsure')

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
