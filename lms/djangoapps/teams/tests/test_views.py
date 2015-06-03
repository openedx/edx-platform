"""
Tests for views.py
"""
from nose.plugins.attrib import attr
from student.tests.factories import (
    CourseEnrollmentFactory,
    UserFactory,
)
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from django.http import Http404
from django.core.urlresolvers import reverse
from rest_framework.test import APIClient


@attr('shard_1')
class TestDashboard(ModuleStoreTestCase):
    test_password = "test"

    def setUp(self):
        """
        Set up tests
        """
        super(TestDashboard, self).setUp()
        self.course = CourseFactory.create(
            teams_configuration={"max_team_size": 10, "topics": [{"name": "foo", "id": 0, "description": "test topic"}]}
        )
        # will be assigned to self.client by default
        self.user = UserFactory.create(password=self.test_password)
        self.teams_url = reverse('teams_dashboard', args=[self.course.id])

    def test_anonymous(self):
        """ Verifies that an anonymous client cannot access the team dashboard. """
        anonymous_client = APIClient()
        response = anonymous_client.get(self.teams_url)
        self.assertEqual(404, response.status_code)

    def test_not_enrolled_not_staff(self):
        """ Verifies that a student who is not enrolled cannot access the team dashboard. """
        response = self.client.get(self.teams_url)
        self.assertEqual(404, response.status_code)

    def test_not_enrolled_staff(self):
        """
        Verifies that a user with global access who is not enrolled in the course can access the team dashboard.
        """
        staff_user = UserFactory(is_staff=True, password=self.test_password)
        staff_client = APIClient()
        staff_client.login(username=staff_user.username, password=self.test_password)
        response = staff_client.get(self.teams_url)
        self.assertContains(response, "TeamsTabFactory", status_code=200)

    def test_enrolled_not_staff(self):
        """
        Verifies that a user without global access who is enrolled in the course can access the team dashboard.
        """
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id)
        self.client.login(username=self.user.username, password=self.test_password)
        response = self.client.get(self.teams_url)
        self.assertContains(response, "TeamsTabFactory", status_code=200)

    def test_enrolled_teams_not_enabled(self):
        """
        Verifies that a user without global access who is enrolled in the course cannot access the team dashboard
        if the teams feature is not enabled.
        """
        course = CourseFactory.create()
        teams_url = reverse('teams_dashboard', args=[course.id])
        CourseEnrollmentFactory.create(user=self.user, course_id=course.id)
        self.client.login(username=self.user.username, password=self.test_password)
        response = self.client.get(teams_url)
        self.assertEqual(404, response.status_code)

    def test_bad_course_id(self):
        """
        Verifies expected behavior when course_id does not reference an existing course or is invalid.
        """
        bad_org = "badorgxxx"
        bad_team_url = self.teams_url.replace(self.course.id.org, bad_org)
        response = self.client.get(bad_team_url)
        self.assertEqual(404, response.status_code)

        bad_team_url = bad_team_url.replace(bad_org, "invalid/course/id")
        response = self.client.get(bad_team_url)
        self.assertEqual(404, response.status_code)
