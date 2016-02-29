# -*- coding: utf-8 -*-
"""Tests for the teams API at the HTTP request level."""
import json
from datetime import datetime

import pytz
from dateutil import parser
import ddt
from elasticsearch.exceptions import ConnectionError
from mock import patch
from search.search_engine_base import SearchEngine
from django.core.urlresolvers import reverse
from django.conf import settings
from django.db.models.signals import post_save
from django.utils import translation
from nose.plugins.attrib import attr
import unittest
from rest_framework.test import APITestCase, APIClient
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from courseware.tests.factories import StaffFactory
from common.test.utils import skip_signal
from student.tests.factories import UserFactory, AdminFactory, CourseEnrollmentFactory
from student.models import CourseEnrollment
from util.testing import EventTestMixin
from .factories import CourseTeamFactory, LAST_ACTIVITY_AT
from ..models import CourseTeamMembership
from ..search_indexes import CourseTeamIndexer, CourseTeam, course_team_post_save_callback
from django_comment_common.models import Role, FORUM_ROLE_COMMUNITY_TA
from django_comment_common.utils import seed_permissions_roles


@attr('shard_1')
class TestDashboard(SharedModuleStoreTestCase):
    """Tests for the Teams dashboard."""
    test_password = "test"

    NUM_TOPICS = 10

    @classmethod
    def setUpClass(cls):
        super(TestDashboard, cls).setUpClass()
        cls.course = CourseFactory.create(
            teams_configuration={
                "max_team_size": 10,
                "topics": [
                    {
                        "name": "Topic {}".format(topic_id),
                        "id": topic_id,
                        "description": "Description for topic {}".format(topic_id)
                    }
                    for topic_id in range(cls.NUM_TOPICS)
                ]
            }
        )

    def setUp(self):
        """
        Set up tests
        """
        super(TestDashboard, self).setUp()
        # will be assigned to self.client by default
        self.user = UserFactory.create(password=self.test_password)
        self.teams_url = reverse('teams_dashboard', args=[self.course.id])

    def test_anonymous(self):
        """Verifies that an anonymous client cannot access the team
        dashboard, and is redirected to the login page."""
        anonymous_client = APIClient()
        response = anonymous_client.get(self.teams_url)
        redirect_url = '{0}?next={1}'.format(settings.LOGIN_URL, self.teams_url)
        self.assertRedirects(response, redirect_url)

    def test_not_enrolled_not_staff(self):
        """ Verifies that a student who is not enrolled cannot access the team dashboard. """
        self.client.login(username=self.user.username, password=self.test_password)
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

    @unittest.skip("Fix this - getting unreliable query counts")
    def test_query_counts(self):
        # Enroll in the course and log in
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id)
        self.client.login(username=self.user.username, password=self.test_password)

        # Check the query count on the dashboard with no teams
        with self.assertNumQueries(18):
            self.client.get(self.teams_url)

        # Create some teams
        for topic_id in range(self.NUM_TOPICS):
            team = CourseTeamFactory.create(
                name=u"Team for topic {}".format(topic_id),
                course_id=self.course.id,
                topic_id=topic_id,
            )

        # Add the user to the last team
        team.add_user(self.user)

        # Check the query count on the dashboard again
        with self.assertNumQueries(24):
            self.client.get(self.teams_url)

    def test_bad_course_id(self):
        """
        Verifies expected behavior when course_id does not reference an existing course or is invalid.
        """
        bad_org = "badorgxxx"
        bad_team_url = self.teams_url.replace(self.course.id.org, bad_org)
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id)
        self.client.login(username=self.user.username, password=self.test_password)
        response = self.client.get(bad_team_url)
        self.assertEqual(404, response.status_code)

        bad_team_url = bad_team_url.replace(bad_org, "invalid/course/id")
        response = self.client.get(bad_team_url)
        self.assertEqual(404, response.status_code)

    def get_user_course_specific_teams_list(self):
        """Gets the list of user course specific teams."""

        # Create a course two
        course_two = CourseFactory.create(
            teams_configuration={
                "max_team_size": 1,
                "topics": [
                    {
                        "name": "Test topic for course two",
                        "id": 1,
                        "description": "Description for test topic for course two."
                    }
                ]
            }
        )

        # Login and enroll user in both course course
        self.client.login(username=self.user.username, password=self.test_password)
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id)
        CourseEnrollmentFactory.create(user=self.user, course_id=course_two.id)

        # Create teams in both courses
        course_one_team = CourseTeamFactory.create(name="Course one team", course_id=self.course.id, topic_id=1)
        course_two_team = CourseTeamFactory.create(name="Course two team", course_id=course_two.id, topic_id=1)  # pylint: disable=unused-variable

        # Check that initially list of user teams in course one is empty
        course_one_teams_url = reverse('teams_dashboard', args=[self.course.id])
        response = self.client.get(course_one_teams_url)
        self.assertIn('"teams": {"count": 0', response.content)

        # Add user to a course one team
        course_one_team.add_user(self.user)

        # Check that list of user teams in course one is not empty, it is one now
        response = self.client.get(course_one_teams_url)
        self.assertIn('"teams": {"count": 1', response.content)

        # Check that list of user teams in course two is still empty
        course_two_teams_url = reverse('teams_dashboard', args=[course_two.id])
        response = self.client.get(course_two_teams_url)
        self.assertIn('"teams": {"count": 0', response.content)


class TeamAPITestCase(APITestCase, SharedModuleStoreTestCase):
    """Base class for Team API test cases."""

    test_password = 'password'

    @classmethod
    def setUpClass(cls):
        with super(TeamAPITestCase, cls).setUpClassAndTestData():
            teams_configuration_1 = {
                'topics':
                [
                    {
                        'id': 'topic_{}'.format(i),
                        'name': name,
                        'description': 'Description for topic {}.'.format(i)
                    } for i, name in enumerate([u'Sólar power', 'Wind Power', 'Nuclear Power', 'Coal Power'])
                ]
            }
            cls.test_course_1 = CourseFactory.create(
                org='TestX',
                course='TS101',
                display_name='Test Course',
                teams_configuration=teams_configuration_1
            )

            teams_configuration_2 = {
                'topics':
                [
                    {
                        'id': 'topic_5',
                        'name': 'Other Interests',
                        'description': 'Description for topic 5.'
                    },
                    {
                        'id': 'topic_6',
                        'name': 'Public Profiles',
                        'description': 'Description for topic 6.'
                    },
                    {
                        'id': 'Topic_6.5',
                        'name': 'Test Accessibility Topic',
                        'description': 'Description for Topic_6.5'
                    },
                ],
                'max_team_size': 1
            }
            cls.test_course_2 = CourseFactory.create(
                org='MIT',
                course='6.002x',
                display_name='Circuits',
                teams_configuration=teams_configuration_2
            )

    @classmethod
    def setUpTestData(cls):
        super(TeamAPITestCase, cls).setUpTestData()
        cls.topics_count = 4
        cls.users = {
            'staff': AdminFactory.create(password=cls.test_password),
            'course_staff': StaffFactory.create(course_key=cls.test_course_1.id, password=cls.test_password)
        }
        cls.create_and_enroll_student(username='student_enrolled')
        cls.create_and_enroll_student(username='student_enrolled_not_on_team')
        cls.create_and_enroll_student(username='student_unenrolled', courses=[])

        # Make this student a community TA.
        cls.create_and_enroll_student(username='community_ta')
        seed_permissions_roles(cls.test_course_1.id)
        community_ta_role = Role.objects.get(name=FORUM_ROLE_COMMUNITY_TA, course_id=cls.test_course_1.id)
        community_ta_role.users.add(cls.users['community_ta'])

        # This student is enrolled in both test courses and is a member of a team in each course, but is not on the
        # same team as student_enrolled.
        cls.create_and_enroll_student(
            courses=[cls.test_course_1, cls.test_course_2],
            username='student_enrolled_both_courses_other_team'
        )

        # Make this student have a public profile
        cls.create_and_enroll_student(
            courses=[cls.test_course_2],
            username='student_enrolled_public_profile'
        )
        profile = cls.users['student_enrolled_public_profile'].profile
        profile.year_of_birth = 1970
        profile.save()

        # This student is enrolled in the other course, but not yet a member of a team. This is to allow
        # course_2 to use a max_team_size of 1 without breaking other tests on course_1
        cls.create_and_enroll_student(
            courses=[cls.test_course_2],
            username='student_enrolled_other_course_not_on_team'
        )

        with skip_signal(
            post_save,
            receiver=course_team_post_save_callback,
            sender=CourseTeam,
            dispatch_uid='teams.signals.course_team_post_save_callback'
        ):
            cls.solar_team = CourseTeamFactory.create(
                name=u'Sólar team',
                course_id=cls.test_course_1.id,
                topic_id='topic_0'
            )
            cls.wind_team = CourseTeamFactory.create(name='Wind Team', course_id=cls.test_course_1.id)
            cls.nuclear_team = CourseTeamFactory.create(name='Nuclear Team', course_id=cls.test_course_1.id)
            cls.another_team = CourseTeamFactory.create(name='Another Team', course_id=cls.test_course_2.id)
            cls.public_profile_team = CourseTeamFactory.create(
                name='Public Profile Team',
                course_id=cls.test_course_2.id,
                topic_id='topic_6'
            )
            cls.search_team = CourseTeamFactory.create(
                name='Search',
                description='queryable text',
                country='GS',
                language='to',
                course_id=cls.test_course_2.id,
                topic_id='topic_7'
            )
            cls.chinese_team = CourseTeamFactory.create(
                name=u'著文企臺個',
                description=u'共樣地面較，件展冷不護者這與民教過住意，國制銀產物助音是勢一友',
                country='CN',
                language='zh_HANS',
                course_id=cls.test_course_2.id,
                topic_id='topic_7'
            )

        cls.test_team_name_id_map = {team.name: team for team in (
            cls.solar_team,
            cls.wind_team,
            cls.nuclear_team,
            cls.another_team,
            cls.public_profile_team,
            cls.search_team,
            cls.chinese_team,
        )}

        for user, course in [('staff', cls.test_course_1), ('course_staff', cls.test_course_1)]:
            CourseEnrollment.enroll(
                cls.users[user], course.id, check_access=True
            )

        # Django Rest Framework v3 requires us to pass a request to serializers
        # that have URL fields.  Since we're invoking this code outside the context
        # of a request, we need to simulate that there's a request.
        cls.solar_team.add_user(cls.users['student_enrolled'])
        cls.nuclear_team.add_user(cls.users['student_enrolled_both_courses_other_team'])
        cls.another_team.add_user(cls.users['student_enrolled_both_courses_other_team'])
        cls.public_profile_team.add_user(cls.users['student_enrolled_public_profile'])

    def build_membership_data_raw(self, username, team):
        """Assembles a membership creation payload based on the raw values provided."""
        return {'username': username, 'team_id': team}

    def build_membership_data(self, username, team):
        """Assembles a membership creation payload based on the username and team model provided."""
        return self.build_membership_data_raw(self.users[username].username, team.team_id)

    @classmethod
    def create_and_enroll_student(cls, courses=None, username=None):
        """ Creates a new student and enrolls that student in the course.

        Adds the new user to the cls.users dictionary with the username as the key.

        Returns the username once the user has been created.
        """
        if username is not None:
            user = UserFactory.create(password=cls.test_password, username=username)
        else:
            user = UserFactory.create(password=cls.test_password)
        courses = courses if courses is not None else [cls.test_course_1]
        for course in courses:
            CourseEnrollment.enroll(user, course.id, check_access=True)
        cls.users[user.username] = user

        return user.username

    def login(self, user):
        """Given a user string, logs the given user in.

        Used for testing with ddt, which does not have access to self in
        decorators. If user is 'student_inactive', then an inactive user will
        be both created and logged in.
        """
        if user == 'student_inactive':
            student_inactive = UserFactory.create(password=self.test_password)
            self.client.login(username=student_inactive.username, password=self.test_password)
            student_inactive.is_active = False
            student_inactive.save()
        else:
            self.client.login(username=self.users[user].username, password=self.test_password)

    def make_call(self, url, expected_status=200, method='get', data=None, content_type=None, **kwargs):
        """Makes a call to the Team API at the given url with method and data.

        If a user is specified in kwargs, that user is first logged in.
        """
        user = kwargs.pop('user', 'student_enrolled_not_on_team')
        if user:
            self.login(user)
        func = getattr(self.client, method)
        if content_type:
            response = func(url, data=data, content_type=content_type)
        else:
            response = func(url, data=data)

        self.assertEqual(
            expected_status,
            response.status_code,
            msg="Expected status {expected} but got {actual}: {content}".format(
                expected=expected_status,
                actual=response.status_code,
                content=response.content,
            )
        )

        if expected_status == 200:
            return json.loads(response.content)
        else:
            return response

    def get_teams_list(self, expected_status=200, data=None, no_course_id=False, **kwargs):
        """Gets the list of teams as the given user with data as query params. Verifies expected_status."""
        data = data if data else {}
        if 'course_id' not in data and not no_course_id:
            data.update({'course_id': self.test_course_1.id})
        return self.make_call(reverse('teams_list'), expected_status, 'get', data, **kwargs)

    def get_user_course_specific_teams_list(self):
        """Gets the list of user course specific teams."""

        # Create and enroll user in both courses
        user = self.create_and_enroll_student(
            courses=[self.test_course_1, self.test_course_2],
            username='test_user_enrolled_both_courses'
        )
        course_one_data = {'course_id': self.test_course_1.id, 'username': user}
        course_two_data = {'course_id': self.test_course_2.id, 'username': user}

        # Check that initially list of user teams in course one is empty
        team_list = self.get_teams_list(user=user, expected_status=200, data=course_one_data)
        self.assertEqual(team_list['count'], 0)

        # Add user to a course one team
        self.solar_team.add_user(self.users[user])

        # Check that list of user teams in course one is not empty now
        team_list = self.get_teams_list(user=user, expected_status=200, data=course_one_data)
        self.assertEqual(team_list['count'], 1)

        # Check that list of user teams in course two is still empty
        team_list = self.get_teams_list(user=user, expected_status=200, data=course_two_data)
        self.assertEqual(team_list['count'], 0)

    def build_team_data(self, name="Test team", course=None, description="Filler description", **kwargs):
        """Creates the payload for creating a team. kwargs can be used to specify additional fields."""
        data = kwargs
        course = course if course else self.test_course_1
        data.update({
            'name': name,
            'course_id': str(course.id),
            'description': description,
        })
        return data

    def post_create_team(self, expected_status=200, data=None, **kwargs):
        """Posts data to the team creation endpoint. Verifies expected_status."""
        return self.make_call(reverse('teams_list'), expected_status, 'post', data, **kwargs)

    def get_team_detail(self, team_id, expected_status=200, data=None, **kwargs):
        """Gets detailed team information for team_id. Verifies expected_status."""
        return self.make_call(reverse('teams_detail', args=[team_id]), expected_status, 'get', data, **kwargs)

    def delete_team(self, team_id, expected_status, **kwargs):
        """Delete the given team. Verifies expected_status."""
        return self.make_call(reverse('teams_detail', args=[team_id]), expected_status, 'delete', **kwargs)

    def patch_team_detail(self, team_id, expected_status, data=None, **kwargs):
        """Patches the team with team_id using data. Verifies expected_status."""
        return self.make_call(
            reverse('teams_detail', args=[team_id]),
            expected_status,
            'patch',
            json.dumps(data) if data else None,
            'application/merge-patch+json',
            **kwargs
        )

    def get_topics_list(self, expected_status=200, data=None, **kwargs):
        """Gets the list of topics, passing data as query params. Verifies expected_status."""
        return self.make_call(reverse('topics_list'), expected_status, 'get', data, **kwargs)

    def get_topic_detail(self, topic_id, course_id, expected_status=200, data=None, **kwargs):
        """Gets a single topic, passing data as query params. Verifies expected_status."""
        return self.make_call(
            reverse('topics_detail', kwargs={'topic_id': topic_id, 'course_id': str(course_id)}),
            expected_status,
            'get',
            data,
            **kwargs
        )

    def get_membership_list(self, expected_status=200, data=None, **kwargs):
        """Gets the membership list, passing data as query params. Verifies expected_status."""
        return self.make_call(reverse('team_membership_list'), expected_status, 'get', data, **kwargs)

    def post_create_membership(self, expected_status=200, data=None, **kwargs):
        """Posts data to the membership creation endpoint. Verifies expected_status."""
        return self.make_call(reverse('team_membership_list'), expected_status, 'post', data, **kwargs)

    def get_membership_detail(self, team_id, username, expected_status=200, data=None, **kwargs):
        """Gets an individual membership record, passing data as query params. Verifies expected_status."""
        return self.make_call(
            reverse('team_membership_detail', args=[team_id, username]),
            expected_status,
            'get',
            data,
            **kwargs
        )

    def delete_membership(self, team_id, username, expected_status=200, **kwargs):
        """Deletes an individual membership record. Verifies expected_status."""
        url = reverse('team_membership_detail', args=[team_id, username]) + '?admin=true'
        return self.make_call(url, expected_status, 'delete', **kwargs)

    def verify_expanded_public_user(self, user):
        """Verifies that fields exist on the returned user json indicating that it is expanded."""
        for field in ['username', 'url', 'bio', 'country', 'profile_image', 'time_zone', 'language_proficiencies']:
            self.assertIn(field, user)

    def verify_expanded_private_user(self, user):
        """Verifies that fields exist on the returned user json indicating that it is expanded."""
        for field in ['username', 'url', 'profile_image']:
            self.assertIn(field, user)
        for field in ['bio', 'country', 'time_zone', 'language_proficiencies']:
            self.assertNotIn(field, user)

    def verify_expanded_team(self, team):
        """Verifies that fields exist on the returned team json indicating that it is expanded."""
        for field in ['id', 'name', 'course_id', 'topic_id', 'date_created', 'description']:
            self.assertIn(field, team)


@ddt.ddt
class TestListTeamsAPI(EventTestMixin, TeamAPITestCase):
    """Test cases for the team listing API endpoint."""

    def setUp(self):  # pylint: disable=arguments-differ
        super(TestListTeamsAPI, self).setUp('lms.djangoapps.teams.utils.tracker')

    @ddt.data(
        (None, 401),
        ('student_inactive', 401),
        ('student_unenrolled', 403),
        ('student_enrolled', 200),
        ('staff', 200),
        ('course_staff', 200),
        ('community_ta', 200),
    )
    @ddt.unpack
    def test_access(self, user, status):
        teams = self.get_teams_list(user=user, expected_status=status)
        if status == 200:
            self.assertEqual(3, teams['count'])

    def test_missing_course_id(self):
        self.get_teams_list(400, no_course_id=True)

    def verify_names(self, data, status, names=None, **kwargs):
        """Gets a team listing with data as query params, verifies status, and then verifies team names if specified."""
        teams = self.get_teams_list(data=data, expected_status=status, **kwargs)
        if names is not None and 200 <= status < 300:
            results = teams['results']
            self.assertEqual(names, [team['name'] for team in results])

    def test_filter_invalid_course_id(self):
        self.verify_names({'course_id': 'no_such_course'}, 400)

    def test_filter_course_id(self):
        self.verify_names(
            {'course_id': self.test_course_2.id},
            200,
            ['Another Team', 'Public Profile Team', 'Search', u'著文企臺個'],
            user='staff'
        )

    def test_filter_topic_id(self):
        self.verify_names({'course_id': self.test_course_1.id, 'topic_id': 'topic_0'}, 200, [u'Sólar team'])

    def test_filter_username(self):
        self.verify_names({'course_id': self.test_course_1.id, 'username': 'student_enrolled'}, 200, [u'Sólar team'])
        self.verify_names({'course_id': self.test_course_1.id, 'username': 'staff'}, 200, [])

    @ddt.data(
        (None, 200, ['Nuclear Team', u'Sólar team', 'Wind Team']),
        ('name', 200, ['Nuclear Team', u'Sólar team', 'Wind Team']),
        # Note that "Nuclear Team" and "Solar team" have the same open_slots.
        # "Solar team" comes first due to secondary sort by last_activity_at.
        ('open_slots', 200, ['Wind Team', u'Sólar team', 'Nuclear Team']),
        # Note that "Wind Team" and "Nuclear Team" have the same last_activity_at.
        # "Wind Team" comes first due to secondary sort by open_slots.
        ('last_activity_at', 200, [u'Sólar team', 'Wind Team', 'Nuclear Team']),
    )
    @ddt.unpack
    def test_order_by(self, field, status, names):
        # Make "Solar team" the most recently active team.
        # The CourseTeamFactory sets the last_activity_at to a fixed time (in the past), so all of the
        # other teams have the same last_activity_at.
        with skip_signal(
            post_save,
            receiver=course_team_post_save_callback,
            sender=CourseTeam,
            dispatch_uid='teams.signals.course_team_post_save_callback'
        ):
            solar_team = self.test_team_name_id_map[u'Sólar team']
            solar_team.last_activity_at = datetime.utcnow().replace(tzinfo=pytz.utc)
            solar_team.save()

        data = {'order_by': field} if field else {}
        self.verify_names(data, status, names)

    def test_order_by_with_text_search(self):
        data = {'order_by': 'name', 'text_search': 'search'}
        self.verify_names(data, 400, [])
        self.assert_no_events_were_emitted()

    @ddt.data((404, {'course_id': 'no/such/course'}), (400, {'topic_id': 'no_such_topic'}))
    @ddt.unpack
    def test_no_results(self, status, data):
        self.get_teams_list(status, data)

    def test_page_size(self):
        result = self.get_teams_list(200, {'page_size': 2})
        self.assertEquals(2, result['num_pages'])

    def test_page(self):
        result = self.get_teams_list(200, {'page_size': 1, 'page': 3})
        self.assertEquals(3, result['num_pages'])
        self.assertIsNone(result['next'])
        self.assertIsNotNone(result['previous'])

    def test_expand_private_user(self):
        # Use the default user which is already private because to year_of_birth is set
        result = self.get_teams_list(200, {'expand': 'user', 'topic_id': 'topic_0'})
        self.verify_expanded_private_user(result['results'][0]['membership'][0]['user'])

    def test_expand_public_user(self):
        result = self.get_teams_list(
            200,
            {
                'expand': 'user',
                'topic_id': 'topic_6',
                'course_id': self.test_course_2.id
            },
            user='student_enrolled_public_profile'
        )
        self.verify_expanded_public_user(result['results'][0]['membership'][0]['user'])

    @ddt.data(
        ('search', ['Search']),
        ('queryable', ['Search']),
        ('Tonga', ['Search']),
        ('Island', ['Search']),
        ('not-a-query', []),
        ('team', ['Another Team', 'Public Profile Team']),
        (u'著文企臺個', [u'著文企臺個']),
    )
    @ddt.unpack
    def test_text_search(self, text_search, expected_team_names):
        def reset_search_index():
            """Clear out the search index and reindex the teams."""
            CourseTeamIndexer.engine().destroy()
            for team in self.test_team_name_id_map.values():
                CourseTeamIndexer.index(team)

        reset_search_index()
        self.verify_names(
            {'course_id': self.test_course_2.id, 'text_search': text_search},
            200,
            expected_team_names,
            user='student_enrolled_public_profile'
        )

        self.assert_event_emitted(
            'edx.team.searched',
            search_text=text_search,
            topic_id=None,
            number_of_results=len(expected_team_names)
        )

        # Verify that the searches still work for a user from a different locale
        with translation.override('ar'):
            reset_search_index()
            self.verify_names(
                {'course_id': self.test_course_2.id, 'text_search': text_search},
                200,
                expected_team_names,
                user='student_enrolled_public_profile'
            )

    def test_delete_removed_from_search(self):
        team = CourseTeamFactory.create(
            name=u'zoinks',
            course_id=self.test_course_1.id,
            topic_id='topic_0'
        )
        self.verify_names(
            {'course_id': self.test_course_1.id, 'text_search': 'zoinks'},
            200,
            [team.name],
            user='staff'
        )
        team.delete()
        self.verify_names(
            {'course_id': self.test_course_1.id, 'text_search': 'zoinks'},
            200,
            [],
            user='staff'
        )


@ddt.ddt
class TestCreateTeamAPI(EventTestMixin, TeamAPITestCase):
    """Test cases for the team creation endpoint."""

    def setUp(self):  # pylint: disable=arguments-differ
        super(TestCreateTeamAPI, self).setUp('lms.djangoapps.teams.utils.tracker')

    @ddt.data(
        (None, 401),
        ('student_inactive', 401),
        ('student_unenrolled', 403),
        ('student_enrolled_not_on_team', 200),
        ('staff', 200),
        ('course_staff', 200),
        ('community_ta', 200),
    )
    @ddt.unpack
    def test_access(self, user, status):
        team = self.post_create_team(status, self.build_team_data(name="New Team"), user=user)
        if status == 200:
            self.verify_expected_team_id(team, 'new-team')
            teams = self.get_teams_list(user=user)
            self.assertIn("New Team", [team['name'] for team in teams['results']])

    def _expected_team_id(self, team, expected_prefix):
        """ Return the team id that we'd expect given this team data and this prefix. """
        return expected_prefix + '-' + team['discussion_topic_id']

    def verify_expected_team_id(self, team, expected_prefix):
        """ Verifies that the team id starts with the specified prefix and ends with the discussion_topic_id """
        self.assertIn('id', team)
        self.assertIn('discussion_topic_id', team)
        self.assertEqual(team['id'], self._expected_team_id(team, expected_prefix))

    def test_naming(self):
        new_teams = [
            self.post_create_team(data=self.build_team_data(name=name), user=self.create_and_enroll_student())
            for name in ["The Best Team", "The Best Team", "A really long team name"]
        ]
        # Check that teams with the same name have unique IDs.
        self.verify_expected_team_id(new_teams[0], 'the-best-team')
        self.verify_expected_team_id(new_teams[1], 'the-best-team')
        self.assertNotEqual(new_teams[0]['id'], new_teams[1]['id'])

        # Verify expected truncation behavior with names > 20 characters.
        self.verify_expected_team_id(new_teams[2], 'a-really-long-team-n')

    @ddt.data((400, {
        'name': 'Bad Course ID',
        'course_id': 'no_such_course',
        'description': "Filler Description"
    }), (404, {
        'name': "Non-existent course ID",
        'course_id': 'no/such/course',
        'description': "Filler Description"
    }))
    @ddt.unpack
    def test_bad_course_data(self, status, data):
        self.post_create_team(status, data)

    def test_student_in_team(self):
        response = self.post_create_team(
            400,
            data=self.build_team_data(
                name="Doomed team",
                course=self.test_course_1,
                description="Overly ambitious student"
            ),
            user='student_enrolled'
        )
        self.assertEqual(
            "You are already in a team in this course.",
            json.loads(response.content)["user_message"]
        )

    @ddt.data('staff', 'course_staff', 'community_ta')
    def test_privileged_create_multiple_teams(self, user):
        """ Privileged users can create multiple teams, even if they are already in one. """
        # First add the privileged user to a team.
        self.post_create_membership(
            200,
            self.build_membership_data(user, self.solar_team),
            user=user
        )

        self.post_create_team(
            data=self.build_team_data(
                name="Another team",
                course=self.test_course_1,
                description="Privileged users are the best"
            ),
            user=user
        )

    @ddt.data({'description': ''}, {'name': 'x' * 1000}, {'name': ''})
    def test_bad_fields(self, kwargs):
        self.post_create_team(400, self.build_team_data(**kwargs))

    def test_missing_name(self):
        self.post_create_team(400, {
            'course_id': str(self.test_course_1.id),
            'description': "foobar"
        })

    def test_full_student_creator(self):
        creator = self.create_and_enroll_student()
        team = self.post_create_team(data=self.build_team_data(
            name="Fully specified team",
            course=self.test_course_1,
            description="Another fantastic team",
            topic_id='great-topic',
            country='CA',
            language='fr'
        ), user=creator)

        # Verify the id (it ends with a unique hash, which is the same as the discussion_id).
        self.verify_expected_team_id(team, 'fully-specified-team')
        del team['id']

        self.assert_event_emitted(
            'edx.team.created',
            team_id=self._expected_team_id(team, 'fully-specified-team'),
        )

        self.assert_event_emitted(
            'edx.team.learner_added',
            team_id=self._expected_team_id(team, 'fully-specified-team'),
            user_id=self.users[creator].id,
            add_method='added_on_create'
        )
        # Remove date_created and discussion_topic_id because they change between test runs
        del team['date_created']
        del team['discussion_topic_id']

        # Since membership is its own list, we want to examine this separately.
        team_membership = team['membership']
        del team['membership']

        # verify that it's been set to a time today.
        self.assertEqual(
            parser.parse(team['last_activity_at']).date(),
            datetime.utcnow().replace(tzinfo=pytz.utc).date()
        )
        del team['last_activity_at']

        # Verify that the creating user gets added to the team.
        self.assertEqual(len(team_membership), 1)
        member = team_membership[0]['user']
        self.assertEqual(member['username'], creator)

        self.assertEqual(team, {
            'name': 'Fully specified team',
            'language': 'fr',
            'country': 'CA',
            'topic_id': 'great-topic',
            'course_id': str(self.test_course_1.id),
            'description': 'Another fantastic team'
        })

    @ddt.data('staff', 'course_staff', 'community_ta')
    def test_membership_staff_creator(self, user):
        # Verify that staff do not automatically get added to a team
        # when they create one.
        team = self.post_create_team(data=self.build_team_data(
            name="New team",
            course=self.test_course_1,
            description="Another fantastic team",
        ), user=user)

        self.assertEqual(team['membership'], [])


@ddt.ddt
class TestDetailTeamAPI(TeamAPITestCase):
    """Test cases for the team detail endpoint."""

    @ddt.data(
        (None, 401),
        ('student_inactive', 401),
        ('student_unenrolled', 403),
        ('student_enrolled', 200),
        ('staff', 200),
        ('course_staff', 200),
        ('community_ta', 200),
    )
    @ddt.unpack
    def test_access(self, user, status):
        team = self.get_team_detail(self.solar_team.team_id, status, user=user)
        if status == 200:
            self.assertEqual(team['description'], self.solar_team.description)
            self.assertEqual(team['discussion_topic_id'], self.solar_team.discussion_topic_id)
            self.assertEqual(parser.parse(team['last_activity_at']), LAST_ACTIVITY_AT)

    def test_does_not_exist(self):
        self.get_team_detail('no_such_team', 404)

    def test_expand_private_user(self):
        # Use the default user which is already private because to year_of_birth is set
        result = self.get_team_detail(self.solar_team.team_id, 200, {'expand': 'user'})
        self.verify_expanded_private_user(result['membership'][0]['user'])

    def test_expand_public_user(self):
        result = self.get_team_detail(
            self.public_profile_team.team_id,
            200,
            {'expand': 'user'},
            user='student_enrolled_public_profile'
        )
        self.verify_expanded_public_user(result['membership'][0]['user'])


@ddt.ddt
class TestDeleteTeamAPI(EventTestMixin, TeamAPITestCase):
    """Test cases for the team delete endpoint."""

    def setUp(self):  # pylint: disable=arguments-differ
        super(TestDeleteTeamAPI, self).setUp('lms.djangoapps.teams.utils.tracker')

    @ddt.data(
        (None, 401),
        ('student_inactive', 401),
        ('student_unenrolled', 403),
        ('student_enrolled', 403),
        ('staff', 204),
        ('course_staff', 204),
        ('community_ta', 204)
    )
    @ddt.unpack
    def test_access(self, user, status):
        self.delete_team(self.solar_team.team_id, status, user=user)
        if status == 204:
            self.assert_event_emitted(
                'edx.team.deleted',
                team_id=self.solar_team.team_id,
            )
            self.assert_event_emitted(
                'edx.team.learner_removed',
                team_id=self.solar_team.team_id,
                remove_method='team_deleted',
                user_id=self.users['student_enrolled'].id
            )

    def test_does_not_exist(self):
        self.delete_team('nonexistent', 404)

    def test_memberships_deleted(self):
        self.assertEqual(CourseTeamMembership.objects.filter(team=self.solar_team).count(), 1)
        self.delete_team(self.solar_team.team_id, 204, user='staff')
        self.assert_event_emitted(
            'edx.team.deleted',
            team_id=self.solar_team.team_id,
        )
        self.assert_event_emitted(
            'edx.team.learner_removed',
            team_id=self.solar_team.team_id,
            remove_method='team_deleted',
            user_id=self.users['student_enrolled'].id
        )
        self.assertEqual(CourseTeamMembership.objects.filter(team=self.solar_team).count(), 0)


@ddt.ddt
class TestUpdateTeamAPI(EventTestMixin, TeamAPITestCase):
    """Test cases for the team update endpoint."""

    def setUp(self):  # pylint: disable=arguments-differ
        super(TestUpdateTeamAPI, self).setUp('lms.djangoapps.teams.utils.tracker')

    @ddt.data(
        (None, 401),
        ('student_inactive', 401),
        ('student_unenrolled', 403),
        ('student_enrolled', 403),
        ('staff', 200),
        ('course_staff', 200),
        ('community_ta', 200),
    )
    @ddt.unpack
    def test_access(self, user, status):
        prev_name = self.solar_team.name
        team = self.patch_team_detail(self.solar_team.team_id, status, {'name': 'foo'}, user=user)
        if status == 200:
            self.assertEquals(team['name'], 'foo')
            self.assert_event_emitted(
                'edx.team.changed',
                team_id=self.solar_team.team_id,
                truncated=[],
                field='name',
                old=prev_name,
                new='foo'
            )

    @ddt.data(
        (None, 401),
        ('student_inactive', 401),
        ('student_unenrolled', 404),
        ('student_enrolled', 404),
        ('staff', 404),
        ('course_staff', 404),
        ('community_ta', 404),
    )
    @ddt.unpack
    def test_access_bad_id(self, user, status):
        self.patch_team_detail("no_such_team", status, {'name': 'foo'}, user=user)

    @ddt.data(
        ('id', 'foobar'),
        ('description', ''),
        ('country', 'no_such_country'),
        ('language', 'no_such_language')
    )
    @ddt.unpack
    def test_bad_requests(self, key, value):
        self.patch_team_detail(self.solar_team.team_id, 400, {key: value}, user='staff')

    @ddt.data(('country', 'US'), ('language', 'en'), ('foo', 'bar'))
    @ddt.unpack
    def test_good_requests(self, key, value):
        if hasattr(self.solar_team, key):
            prev_value = getattr(self.solar_team, key)

        self.patch_team_detail(self.solar_team.team_id, 200, {key: value}, user='staff')

        if hasattr(self.solar_team, key):
            self.assert_event_emitted(
                'edx.team.changed',
                team_id=self.solar_team.team_id,
                truncated=[],
                field=key,
                old=prev_value,
                new=value
            )

    def test_does_not_exist(self):
        self.patch_team_detail('no_such_team', 404, user='staff')


@ddt.ddt
class TestListTopicsAPI(TeamAPITestCase):
    """Test cases for the topic listing endpoint."""

    @ddt.data(
        (None, 401),
        ('student_inactive', 401),
        ('student_unenrolled', 403),
        ('student_enrolled', 200),
        ('staff', 200),
        ('course_staff', 200),
        ('community_ta', 200),
    )
    @ddt.unpack
    def test_access(self, user, status):
        topics = self.get_topics_list(status, {'course_id': self.test_course_1.id}, user=user)
        if status == 200:
            self.assertEqual(topics['count'], self.topics_count)

    @ddt.data('A+BOGUS+COURSE', 'A/BOGUS/COURSE')
    def test_invalid_course_key(self, course_id):
        self.get_topics_list(404, {'course_id': course_id})

    def test_without_course_id(self):
        self.get_topics_list(400)

    @ddt.data(
        (None, 200, ['Coal Power', 'Nuclear Power', u'Sólar power', 'Wind Power'], 'name'),
        ('name', 200, ['Coal Power', 'Nuclear Power', u'Sólar power', 'Wind Power'], 'name'),
        # Note that "Nuclear Power" and "Solar power" both have 2 teams. "Coal Power" and "Window Power"
        # both have 0 teams. The secondary sort is alphabetical by name.
        ('team_count', 200, ['Nuclear Power', u'Sólar power', 'Coal Power', 'Wind Power'], 'team_count'),
        ('no_such_field', 400, [], None),
    )
    @ddt.unpack
    def test_order_by(self, field, status, names, expected_ordering):
        with skip_signal(
            post_save,
            receiver=course_team_post_save_callback,
            sender=CourseTeam,
            dispatch_uid='teams.signals.course_team_post_save_callback'
        ):
            # Add 2 teams to "Nuclear Power", which previously had no teams.
            CourseTeamFactory.create(
                name=u'Nuclear Team 1', course_id=self.test_course_1.id, topic_id='topic_2'
            )
            CourseTeamFactory.create(
                name=u'Nuclear Team 2', course_id=self.test_course_1.id, topic_id='topic_2'
            )
        data = {'course_id': self.test_course_1.id}
        if field:
            data['order_by'] = field
        topics = self.get_topics_list(status, data)
        if status == 200:
            self.assertEqual(names, [topic['name'] for topic in topics['results']])
            self.assertEqual(topics['sort_order'], expected_ordering)

    def test_order_by_team_count_secondary(self):
        """
        Ensure that the secondary sort (alphabetical) when primary sort is team_count
        works across pagination boundaries.
        """
        with skip_signal(
            post_save,
            receiver=course_team_post_save_callback,
            sender=CourseTeam,
            dispatch_uid='teams.signals.course_team_post_save_callback'
        ):
            # Add 2 teams to "Wind Power", which previously had no teams.
            CourseTeamFactory.create(
                name=u'Wind Team 1', course_id=self.test_course_1.id, topic_id='topic_1'
            )
            CourseTeamFactory.create(
                name=u'Wind Team 2', course_id=self.test_course_1.id, topic_id='topic_1'
            )

        topics = self.get_topics_list(data={
            'course_id': self.test_course_1.id,
            'page_size': 2,
            'page': 1,
            'order_by': 'team_count'
        })
        self.assertEqual(["Wind Power", u'Sólar power'], [topic['name'] for topic in topics['results']])

        topics = self.get_topics_list(data={
            'course_id': self.test_course_1.id,
            'page_size': 2,
            'page': 2,
            'order_by': 'team_count'
        })
        self.assertEqual(["Coal Power", "Nuclear Power"], [topic['name'] for topic in topics['results']])

    def test_pagination(self):
        response = self.get_topics_list(data={
            'course_id': self.test_course_1.id,
            'page_size': 2,
        })

        self.assertEqual(2, len(response['results']))
        self.assertIn('next', response)
        self.assertIn('previous', response)
        self.assertIsNone(response['previous'])
        self.assertIsNotNone(response['next'])

    def test_default_ordering(self):
        response = self.get_topics_list(data={'course_id': self.test_course_1.id})
        self.assertEqual(response['sort_order'], 'name')

    def test_team_count(self):
        """Test that team_count is included for each topic"""
        response = self.get_topics_list(data={'course_id': self.test_course_1.id})
        for topic in response['results']:
            self.assertIn('team_count', topic)
            if topic['id'] == u'topic_0':
                self.assertEqual(topic['team_count'], 1)
            else:
                self.assertEqual(topic['team_count'], 0)


@ddt.ddt
class TestDetailTopicAPI(TeamAPITestCase):
    """Test cases for the topic detail endpoint."""

    @ddt.data(
        (None, 401),
        ('student_inactive', 401),
        ('student_unenrolled', 403),
        ('student_enrolled', 200),
        ('staff', 200),
        ('course_staff', 200),
        ('community_ta', 200),
    )
    @ddt.unpack
    def test_access(self, user, status):
        topic = self.get_topic_detail('topic_0', self.test_course_1.id, status, user=user)
        if status == 200:
            for field in ('id', 'name', 'description'):
                self.assertIn(field, topic)

    @ddt.data('A+BOGUS+COURSE', 'A/BOGUS/COURSE')
    def test_invalid_course_id(self, course_id):
        self.get_topic_detail('topic_0', course_id, 404)

    def test_invalid_topic_id(self):
        self.get_topic_detail('no_such_topic', self.test_course_1.id, 404)

    def test_topic_detail_with_caps_and_dot_in_id(self):
        self.get_topic_detail('Topic_6.5', self.test_course_2.id, user='student_enrolled_public_profile')

    def test_team_count(self):
        """Test that team_count is included with a topic"""
        topic = self.get_topic_detail(topic_id='topic_0', course_id=self.test_course_1.id)
        self.assertEqual(topic['team_count'], 1)
        topic = self.get_topic_detail(topic_id='topic_1', course_id=self.test_course_1.id)
        self.assertEqual(topic['team_count'], 0)


@ddt.ddt
class TestListMembershipAPI(TeamAPITestCase):
    """Test cases for the membership list endpoint."""

    @ddt.data(
        (None, 401),
        ('student_inactive', 401),
        ('student_unenrolled', 404),
        ('student_enrolled', 200),
        ('student_enrolled_both_courses_other_team', 200),
        ('staff', 200),
        ('course_staff', 200),
        ('community_ta', 200),
    )
    @ddt.unpack
    def test_access(self, user, status):
        membership = self.get_membership_list(status, {'team_id': self.solar_team.team_id}, user=user)
        if status == 200:
            self.assertEqual(membership['count'], 1)
            self.assertEqual(membership['results'][0]['user']['username'], self.users['student_enrolled'].username)

    @ddt.data(
        (None, 401, False),
        ('student_inactive', 401, False),
        ('student_unenrolled', 200, False),
        ('student_enrolled', 200, True),
        ('student_enrolled_both_courses_other_team', 200, True),
        ('staff', 200, True),
        ('course_staff', 200, True),
        ('community_ta', 200, True),
    )
    @ddt.unpack
    def test_access_by_username(self, user, status, has_content):
        membership = self.get_membership_list(status, {'username': self.users['student_enrolled'].username}, user=user)
        if status == 200:
            if has_content:
                self.assertEqual(membership['count'], 1)
                self.assertEqual(membership['results'][0]['team']['team_id'], self.solar_team.team_id)
            else:
                self.assertEqual(membership['count'], 0)

    @ddt.data(
        ('student_enrolled_both_courses_other_team', 'TestX/TS101/Test_Course', 200, 'Nuclear Team'),
        ('student_enrolled_both_courses_other_team', 'MIT/6.002x/Circuits', 200, 'Another Team'),
        ('student_enrolled', 'TestX/TS101/Test_Course', 200, u'Sólar team'),
        ('student_enrolled', 'MIT/6.002x/Circuits', 400, ''),
    )
    @ddt.unpack
    def test_course_filter_with_username(self, user, course_id, status, team_name):
        membership = self.get_membership_list(
            status,
            {
                'username': self.users[user],
                'course_id': course_id
            },
            user=user
        )
        if status == 200:
            self.assertEqual(membership['count'], 1)
            self.assertEqual(membership['results'][0]['team']['team_id'], self.test_team_name_id_map[team_name].team_id)

    @ddt.data(
        ('TestX/TS101/Test_Course', 200),
        ('MIT/6.002x/Circuits', 400),
    )
    @ddt.unpack
    def test_course_filter_with_team_id(self, course_id, status):
        membership = self.get_membership_list(status, {'team_id': self.solar_team.team_id, 'course_id': course_id})
        if status == 200:
            self.assertEqual(membership['count'], 1)
            self.assertEqual(membership['results'][0]['team']['team_id'], self.solar_team.team_id)

    def test_bad_course_id(self):
        self.get_membership_list(404, {'course_id': 'no_such_course'})

    def test_no_username_or_team_id(self):
        self.get_membership_list(400, {})

    def test_bad_team_id(self):
        self.get_membership_list(404, {'team_id': 'no_such_team'})

    def test_expand_private_user(self):
        # Use the default user which is already private because to year_of_birth is set
        result = self.get_membership_list(200, {'team_id': self.solar_team.team_id, 'expand': 'user'})
        self.verify_expanded_private_user(result['results'][0]['user'])

    def test_expand_public_user(self):
        result = self.get_membership_list(
            200,
            {'team_id': self.public_profile_team.team_id, 'expand': 'user'},
            user='student_enrolled_public_profile'
        )
        self.verify_expanded_public_user(result['results'][0]['user'])

    def test_expand_team(self):
        result = self.get_membership_list(200, {'team_id': self.solar_team.team_id, 'expand': 'team'})
        self.verify_expanded_team(result['results'][0]['team'])


@ddt.ddt
class TestCreateMembershipAPI(EventTestMixin, TeamAPITestCase):
    """Test cases for the membership creation endpoint."""

    def setUp(self):  # pylint: disable=arguments-differ
        super(TestCreateMembershipAPI, self).setUp('lms.djangoapps.teams.utils.tracker')

    @ddt.data(
        (None, 401),
        ('student_inactive', 401),
        ('student_unenrolled', 404),
        ('student_enrolled_not_on_team', 200),
        ('student_enrolled', 404),
        ('student_enrolled_both_courses_other_team', 404),
        ('staff', 200),
        ('course_staff', 200),
        ('community_ta', 200),
    )
    @ddt.unpack
    def test_access(self, user, status):
        membership = self.post_create_membership(
            status,
            self.build_membership_data('student_enrolled_not_on_team', self.solar_team),
            user=user
        )
        if status == 200:
            self.assertEqual(membership['user']['username'], self.users['student_enrolled_not_on_team'].username)
            self.assertEqual(membership['team']['team_id'], self.solar_team.team_id)
            memberships = self.get_membership_list(200, {'team_id': self.solar_team.team_id})
            self.assertEqual(memberships['count'], 2)

            add_method = 'joined_from_team_view' if user == 'student_enrolled_not_on_team' else 'added_by_another_user'

            self.assert_event_emitted(
                'edx.team.learner_added',
                team_id=self.solar_team.team_id,
                user_id=self.users['student_enrolled_not_on_team'].id,
                add_method=add_method
            )
        else:
            self.assert_no_events_were_emitted()

    def test_no_username(self):
        response = self.post_create_membership(400, {'team_id': self.solar_team.team_id})
        self.assertIn('username', json.loads(response.content)['field_errors'])

    def test_no_team(self):
        response = self.post_create_membership(400, {'username': self.users['student_enrolled_not_on_team'].username})
        self.assertIn('team_id', json.loads(response.content)['field_errors'])

    def test_bad_team(self):
        self.post_create_membership(
            404,
            self.build_membership_data_raw(self.users['student_enrolled'].username, 'no_such_team')
        )

    def test_bad_username(self):
        self.post_create_membership(
            404,
            self.build_membership_data_raw('no_such_user', self.solar_team.team_id),
            user='staff'
        )

    @ddt.data('student_enrolled', 'staff', 'course_staff')
    def test_join_twice(self, user):
        response = self.post_create_membership(
            400,
            self.build_membership_data('student_enrolled', self.solar_team),
            user=user
        )
        self.assertIn('already a member', json.loads(response.content)['developer_message'])

    def test_join_second_team_in_course(self):
        response = self.post_create_membership(
            400,
            self.build_membership_data('student_enrolled_both_courses_other_team', self.solar_team),
            user='student_enrolled_both_courses_other_team'
        )
        self.assertIn('already a member', json.loads(response.content)['developer_message'])

    @ddt.data('staff', 'course_staff')
    def test_not_enrolled_in_team_course(self, user):
        response = self.post_create_membership(
            400,
            self.build_membership_data('student_unenrolled', self.solar_team),
            user=user
        )
        self.assertIn('not enrolled', json.loads(response.content)['developer_message'])

    def test_over_max_team_size_in_course_2(self):
        response = self.post_create_membership(
            400,
            self.build_membership_data('student_enrolled_other_course_not_on_team', self.another_team),
            user='student_enrolled_other_course_not_on_team'
        )
        self.assertIn('full', json.loads(response.content)['developer_message'])


@ddt.ddt
class TestDetailMembershipAPI(TeamAPITestCase):
    """Test cases for the membership detail endpoint."""

    @ddt.data(
        (None, 401),
        ('student_inactive', 401),
        ('student_unenrolled', 404),
        ('student_enrolled_not_on_team', 200),
        ('student_enrolled', 200),
        ('staff', 200),
        ('course_staff', 200),
        ('community_ta', 200),
    )
    @ddt.unpack
    def test_access(self, user, status):
        self.get_membership_detail(
            self.solar_team.team_id,
            self.users['student_enrolled'].username,
            status,
            user=user
        )

    def test_bad_team(self):
        self.get_membership_detail('no_such_team', self.users['student_enrolled'].username, 404)

    def test_bad_username(self):
        self.get_membership_detail(self.solar_team.team_id, 'no_such_user', 404)

    def test_no_membership(self):
        self.get_membership_detail(
            self.solar_team.team_id,
            self.users['student_enrolled_not_on_team'].username,
            404
        )

    def test_expand_private_user(self):
        # Use the default user which is already private because to year_of_birth is set
        result = self.get_membership_detail(
            self.solar_team.team_id,
            self.users['student_enrolled'].username,
            200,
            {'expand': 'user'}
        )
        self.verify_expanded_private_user(result['user'])

    def test_expand_public_user(self):
        result = self.get_membership_detail(
            self.public_profile_team.team_id,
            self.users['student_enrolled_public_profile'].username,
            200,
            {'expand': 'user'},
            user='student_enrolled_public_profile'
        )
        self.verify_expanded_public_user(result['user'])

    def test_expand_team(self):
        result = self.get_membership_detail(
            self.solar_team.team_id,
            self.users['student_enrolled'].username,
            200,
            {'expand': 'team'}
        )
        self.verify_expanded_team(result['team'])


@ddt.ddt
class TestDeleteMembershipAPI(EventTestMixin, TeamAPITestCase):
    """Test cases for the membership deletion endpoint."""

    def setUp(self):  # pylint: disable=arguments-differ
        super(TestDeleteMembershipAPI, self).setUp('lms.djangoapps.teams.utils.tracker')

    @ddt.data(
        (None, 401),
        ('student_inactive', 401),
        ('student_unenrolled', 404),
        ('student_enrolled_not_on_team', 404),
        ('student_enrolled', 204),
        ('staff', 204),
        ('course_staff', 204),
        ('community_ta', 204),
    )
    @ddt.unpack
    def test_access(self, user, status):
        self.delete_membership(
            self.solar_team.team_id,
            self.users['student_enrolled'].username,
            status,
            user=user
        )

        if status == 204:
            self.assert_event_emitted(
                'edx.team.learner_removed',
                team_id=self.solar_team.team_id,
                user_id=self.users['student_enrolled'].id,
                remove_method='removed_by_admin'
            )
        else:
            self.assert_no_events_were_emitted()

    def test_leave_team(self):
        """
        The key difference between this test and test_access above is that
        removal via "Edit Membership" and "Leave Team" emit different events
        despite hitting the same API endpoint, due to the 'admin' query string.
        """
        url = reverse('team_membership_detail', args=[self.solar_team.team_id, self.users['student_enrolled'].username])
        self.make_call(url, 204, 'delete', user='student_enrolled')
        self.assert_event_emitted(
            'edx.team.learner_removed',
            team_id=self.solar_team.team_id,
            user_id=self.users['student_enrolled'].id,
            remove_method='self_removal'
        )

    def test_bad_team(self):
        self.delete_membership('no_such_team', self.users['student_enrolled'].username, 404)

    def test_bad_username(self):
        self.delete_membership(self.solar_team.team_id, 'no_such_user', 404)

    def test_missing_membership(self):
        self.delete_membership(self.wind_team.team_id, self.users['student_enrolled'].username, 404)


class TestElasticSearchErrors(TeamAPITestCase):
    """Test that the Team API is robust to Elasticsearch connection errors."""

    ES_ERROR = ConnectionError('N/A', 'connection error', {})

    @patch.object(SearchEngine, 'get_search_engine', side_effect=ES_ERROR)
    def test_list_teams(self, __):
        """Test that text searches return a 503 when Elasticsearch is down.

        The endpoint should still return 200 when a search is not supplied."""
        self.get_teams_list(
            expected_status=503,
            data={'course_id': self.test_course_1.id, 'text_search': 'zoinks'},
            user='staff'
        )
        self.get_teams_list(
            expected_status=200,
            data={'course_id': self.test_course_1.id},
            user='staff'
        )

    @patch.object(SearchEngine, 'get_search_engine', side_effect=ES_ERROR)
    def test_create_team(self, __):
        """Test that team creation is robust to Elasticsearch errors."""
        self.post_create_team(
            expected_status=200,
            data=self.build_team_data(name='zoinks'),
            user='staff'
        )

    @patch.object(SearchEngine, 'get_search_engine', side_effect=ES_ERROR)
    def test_delete_team(self, __):
        """Test that team deletion is robust to Elasticsearch errors."""
        self.delete_team(self.wind_team.team_id, 204, user='staff')

    @patch.object(SearchEngine, 'get_search_engine', side_effect=ES_ERROR)
    def test_patch_team(self, __):
        """Test that team updates are robust to Elasticsearch errors."""
        self.patch_team_detail(
            self.wind_team.team_id,
            200,
            data={'description': 'new description'},
            user='staff'
        )
