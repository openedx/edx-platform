"""
Unit tests for course_goals.api methods.
"""

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from lms.djangoapps.course_goals.models import CourseGoal
from rest_framework.test import APIClient
from student.models import CourseEnrollment
from track.tests import EventTrackingTestCase
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

TEST_PASSWORD = 'test'


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

    def test_add_valid_goal(self):
        """ Ensures a correctly formatted post succeeds. """
        response = self.post_course_goal(valid=True)
        self.assert_events_emitted()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(CourseGoal.objects.filter(user=self.user, course_key=self.course.id)), 1)

    def test_add_invalid_goal(self):
        """ Ensures a correctly formatted post succeeds. """
        response = self.post_course_goal(valid=False)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(CourseGoal.objects.filter(user=self.user, course_key=self.course.id)), 0)

    def post_course_goal(self, valid=True, goal_key='certify'):
        """
        Sends a post request to set a course goal and returns the response.
        """
        goal_key = goal_key if valid else 'invalid'
        response = self.client.post(
            self.apiUrl,
            {
                'goal_key': goal_key,
                'course_key': self.course.id,
                'user': self.user.username,
            },
        )
        return response
