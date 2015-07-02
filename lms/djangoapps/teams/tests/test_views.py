# -*- coding: utf-8 -*-
"""Tests for the teams API at the HTTP request level."""
# pylint: disable=maybe-no-member
import json

import ddt

from django.core.urlresolvers import reverse
from nose.plugins.attrib import attr
from rest_framework.test import APITestCase, APIClient

from courseware.tests.factories import StaffFactory
from student.tests.factories import UserFactory, AdminFactory, CourseEnrollmentFactory
from student.models import CourseEnrollment
from xmodule.modulestore.tests.factories import CourseFactory
from .factories import CourseTeamFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


@attr('shard_1')
class TestDashboard(ModuleStoreTestCase):
    """Tests for the Teams dashboard."""
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


class TeamAPITestCase(APITestCase, ModuleStoreTestCase):
    """Base class for Team API test cases."""

    test_password = 'password'

    def setUp(self):
        super(TeamAPITestCase, self).setUp()

        teams_configuration = {
            'topics':
            [
                {
                    'id': 'topic_{}'.format(i),
                    'name': name,
                    'description': 'Description for topic {}.'.format(i)
                } for i, name in enumerate([u'sólar power', 'Wind Power', 'Nuclear Power', 'Coal Power'])
            ]
        }
        self.topics_count = 4

        self.test_course_1 = CourseFactory.create(
            org='TestX',
            course='TS101',
            display_name='Test Course',
            teams_configuration=teams_configuration
        )
        self.test_course_2 = CourseFactory.create(org='MIT', course='6.002x', display_name='Circuits')

        self.users = {
            'student_unenrolled': UserFactory.create(password=self.test_password),
            'student_enrolled': UserFactory.create(password=self.test_password),
            'student_enrolled_not_on_team': UserFactory.create(password=self.test_password),

            # This student is enrolled in both test courses and is a member of a team in each course, but is not on the
            # same team as student_enrolled.
            'student_enrolled_both_courses_other_team': UserFactory.create(password=self.test_password),

            'staff': AdminFactory.create(password=self.test_password),
            'course_staff': StaffFactory.create(course_key=self.test_course_1.id, password=self.test_password)
        }
        # 'solar team' is intentionally lower case to test case insensitivity in name ordering
        self.test_team_1 = CourseTeamFactory.create(
            name=u'sólar team',
            course_id=self.test_course_1.id,
            topic_id='renewable'
        )
        self.test_team_2 = CourseTeamFactory.create(name='Wind Team', course_id=self.test_course_1.id)
        self.test_team_3 = CourseTeamFactory.create(name='Nuclear Team', course_id=self.test_course_1.id)
        self.test_team_4 = CourseTeamFactory.create(name='Coal Team', course_id=self.test_course_1.id, is_active=False)
        self.test_team_4 = CourseTeamFactory.create(name='Another Team', course_id=self.test_course_2.id)

        for user, course in [
                ('student_enrolled', self.test_course_1),
                ('student_enrolled_not_on_team', self.test_course_1),
                ('student_enrolled_both_courses_other_team', self.test_course_1),
                ('student_enrolled_both_courses_other_team', self.test_course_2)
        ]:
            CourseEnrollment.enroll(
                self.users[user], course.id, check_access=True
            )

        self.test_team_1.add_user(self.users['student_enrolled'])
        self.test_team_3.add_user(self.users['student_enrolled_both_courses_other_team'])
        self.test_team_4.add_user(self.users['student_enrolled_both_courses_other_team'])

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
        user = kwargs.pop('user', 'student_enrolled')
        if user:
            self.login(user)
        func = getattr(self.client, method)
        if content_type:
            response = func(url, data=data, content_type=content_type)
        else:
            response = func(url, data=data)
        self.assertEqual(expected_status, response.status_code)
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
        return self.make_call(
            reverse('team_membership_detail', args=[team_id, username]),
            expected_status,
            'delete',
            **kwargs
        )

    def verify_expanded_user(self, user):
        """Verifies that fields exist on the returned user json indicating that it is expanded."""
        for field in ['id', 'url', 'email', 'name', 'username', 'preferences']:
            self.assertIn(field, user)

    def verify_expanded_team(self, team):
        """Verifies that fields exist on the returned team json indicating that it is expanded."""
        for field in ['id', 'name', 'is_active', 'course_id', 'topic_id', 'date_created', 'description']:
            self.assertIn(field, team)


@ddt.ddt
class TestListTeamsAPI(TeamAPITestCase):
    """Test cases for the team listing API endpoint."""

    @ddt.data(
        (None, 401),
        ('student_inactive', 401),
        ('student_unenrolled', 403),
        ('student_enrolled', 200),
        ('staff', 200),
        ('course_staff', 200),
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
        if names:
            self.assertEqual(names, [team['name'] for team in teams['results']])

    def test_filter_invalid_course_id(self):
        self.verify_names({'course_id': 'no_such_course'}, 400)

    def test_filter_course_id(self):
        self.verify_names({'course_id': self.test_course_2.id}, 200, ['Another Team'], user='staff')

    def test_filter_topic_id(self):
        self.verify_names({'course_id': self.test_course_1.id, 'topic_id': 'renewable'}, 200, [u'sólar team'])

    def test_filter_include_inactive(self):
        self.verify_names({'include_inactive': True}, 200, ['Coal Team', 'Nuclear Team', u'sólar team', 'Wind Team'])

    # Text search is not yet implemented, so this should return HTTP
    # 400 for now
    def test_filter_text_search(self):
        self.verify_names({'text_search': 'foobar'}, 400)

    @ddt.data(
        (None, 200, ['Nuclear Team', u'sólar team', 'Wind Team']),
        ('name', 200, ['Nuclear Team', u'sólar team', 'Wind Team']),
        ('open_slots', 200, ['Wind Team', u'sólar team', 'Nuclear Team']),
        ('last_activity', 400, []),
    )
    @ddt.unpack
    def test_order_by(self, field, status, names):
        data = {'order_by': field} if field else {}
        self.verify_names(data, status, names)

    @ddt.data({'course_id': 'no/such/course'}, {'topic_id': 'no_such_topic'})
    def test_no_results(self, data):
        self.get_teams_list(404, data)

    def test_page_size(self):
        result = self.get_teams_list(200, {'page_size': 2})
        self.assertEquals(2, result['num_pages'])

    def test_page(self):
        result = self.get_teams_list(200, {'page_size': 1, 'page': 3})
        self.assertEquals(3, result['num_pages'])
        self.assertIsNone(result['next'])
        self.assertIsNotNone(result['previous'])

    def test_expand_user(self):
        result = self.get_teams_list(200, {'expand': 'user', 'topic_id': 'renewable'})
        self.verify_expanded_user(result['results'][0]['membership'][0]['user'])


@ddt.ddt
class TestCreateTeamAPI(TeamAPITestCase):
    """Test cases for the team creation endpoint."""

    @ddt.data(
        (None, 401),
        ('student_inactive', 401),
        ('student_unenrolled', 403),
        ('student_enrolled', 200),
        ('staff', 200),
        ('course_staff', 200)
    )
    @ddt.unpack
    def test_access(self, user, status):
        team = self.post_create_team(status, self.build_team_data(name="New Team"), user=user)
        if status == 200:
            self.assertEqual(team['id'], 'new-team')
            teams = self.get_teams_list(user=user)
            self.assertIn("New Team", [team['name'] for team in teams['results']])

    def test_naming(self):
        new_teams = [
            self.post_create_team(data=self.build_team_data(name=name))
            for name in ["The Best Team", "The Best Team", "The Best Team", "The Best Team 2"]
        ]
        self.assertEquals(
            [team['id'] for team in new_teams],
            ['the-best-team', 'the-best-team-2', 'the-best-team-3', 'the-best-team-2-2']
        )

    @ddt.data((400, {
        'name': 'Bad Course Id',
        'course_id': 'no_such_course',
        'description': "Filler Description"
    }), (404, {
        'name': "Non-existent course id",
        'course_id': 'no/such/course',
        'description': "Filler Description"
    }))
    @ddt.unpack
    def test_bad_course_data(self, status, data):
        self.post_create_team(status, data)

    def test_missing_name(self):
        self.post_create_team(400, {
            'course_id': str(self.test_course_1.id),
            'description': "foobar"
        })

    @ddt.data({'description': ''}, {'name': 'x' * 1000}, {'name': ''})
    def test_bad_fields(self, kwargs):
        self.post_create_team(400, self.build_team_data(**kwargs))

    def test_full(self):
        team = self.post_create_team(data=self.build_team_data(
            name="Fully specified team",
            course=self.test_course_1,
            description="Another fantastic team",
            topic_id='great-topic',
            country='CA',
            language='fr'
        ))

        # Remove date_created because it changes between test runs
        del team['date_created']
        self.assertEquals(team, {
            'name': 'Fully specified team',
            'language': 'fr',
            'country': 'CA',
            'is_active': True,
            'membership': [],
            'topic_id': 'great-topic',
            'course_id': str(self.test_course_1.id),
            'id': 'fully-specified-team',
            'description': 'Another fantastic team'
        })


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
    )
    @ddt.unpack
    def test_access(self, user, status):
        team = self.get_team_detail(self.test_team_1.team_id, status, user=user)
        if status == 200:
            self.assertEquals(team['description'], self.test_team_1.description)

    def test_does_not_exist(self):
        self.get_team_detail('no_such_team', 404)

    def test_expand_user(self):
        result = self.get_team_detail(self.test_team_1.team_id, 200, {'expand': 'user'})
        self.verify_expanded_user(result['membership'][0]['user'])


@ddt.ddt
class TestUpdateTeamAPI(TeamAPITestCase):
    """Test cases for the team update endpoint."""

    @ddt.data(
        (None, 401),
        ('student_inactive', 401),
        ('student_unenrolled', 403),
        ('student_enrolled', 403),
        ('staff', 200),
        ('course_staff', 200),
    )
    @ddt.unpack
    def test_access(self, user, status):
        team = self.patch_team_detail(self.test_team_1.team_id, status, {'name': 'foo'}, user=user)
        if status == 200:
            self.assertEquals(team['name'], 'foo')

    @ddt.data(
        (None, 401),
        ('student_inactive', 401),
        ('student_unenrolled', 404),
        ('student_enrolled', 404),
        ('staff', 404),
        ('course_staff', 404),
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
        self.patch_team_detail(self.test_team_1.team_id, 400, {key: value}, user='staff')

    @ddt.data(('country', 'US'), ('language', 'en'), ('foo', 'bar'))
    @ddt.unpack
    def test_good_requests(self, key, value):
        self.patch_team_detail(self.test_team_1.team_id, 200, {key: value}, user='staff')

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
        (None, 200, ['Coal Power', 'Nuclear Power', u'sólar power', 'Wind Power'], 'name'),
        ('name', 200, ['Coal Power', 'Nuclear Power', u'sólar power', 'Wind Power'], 'name'),
        ('no_such_field', 400, [], None),
    )
    @ddt.unpack
    def test_order_by(self, field, status, names, expected_ordering):
        data = {'course_id': self.test_course_1.id}
        if field:
            data['order_by'] = field
        topics = self.get_topics_list(status, data)
        if status == 200:
            self.assertEqual(names, [topic['name'] for topic in topics['results']])
            self.assertEqual(topics['sort_order'], expected_ordering)

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
    )
    @ddt.unpack
    def test_access(self, user, status):
        membership = self.get_membership_list(status, {'team_id': self.test_team_1.team_id}, user=user)
        if status == 200:
            self.assertEqual(membership['count'], 1)
            self.assertEqual(membership['results'][0]['user']['id'], self.users['student_enrolled'].username)

    @ddt.data(
        (None, 401, False),
        ('student_inactive', 401, False),
        ('student_unenrolled', 200, False),
        ('student_enrolled', 200, True),
        ('student_enrolled_both_courses_other_team', 200, True),
        ('staff', 200, True),
        ('course_staff', 200, True),
    )
    @ddt.unpack
    def test_access_by_username(self, user, status, has_content):
        membership = self.get_membership_list(status, {'username': self.users['student_enrolled'].username}, user=user)
        if status == 200:
            if has_content:
                self.assertEqual(membership['count'], 1)
                self.assertEqual(membership['results'][0]['team']['id'], self.test_team_1.team_id)
            else:
                self.assertEqual(membership['count'], 0)

    def test_no_username_or_team_id(self):
        self.get_membership_list(400, {})

    def test_bad_team_id(self):
        self.get_membership_list(404, {'team_id': 'no_such_team'})

    def test_expand_user(self):
        result = self.get_membership_list(200, {'team_id': self.test_team_1.team_id, 'expand': 'user'})
        self.verify_expanded_user(result['results'][0]['user'])

    def test_expand_team(self):
        result = self.get_membership_list(200, {'team_id': self.test_team_1.team_id, 'expand': 'team'})
        self.verify_expanded_team(result['results'][0]['team'])


@ddt.ddt
class TestCreateMembershipAPI(TeamAPITestCase):
    """Test cases for the membership creation endpoint."""

    def build_membership_data_raw(self, username, team):
        """Assembles a membership creation payload based on the raw values provided."""
        return {'username': username, 'team_id': team}

    def build_membership_data(self, username, team):
        """Assembles a membership creation payload based on the username and team model provided."""
        return self.build_membership_data_raw(self.users[username].username, team.team_id)

    @ddt.data(
        (None, 401),
        ('student_inactive', 401),
        ('student_unenrolled', 404),
        ('student_enrolled_not_on_team', 200),
        ('student_enrolled', 404),
        ('student_enrolled_both_courses_other_team', 404),
        ('staff', 200),
        ('course_staff', 200),
    )
    @ddt.unpack
    def test_access(self, user, status):
        membership = self.post_create_membership(
            status,
            self.build_membership_data('student_enrolled_not_on_team', self.test_team_1),
            user=user
        )
        if status == 200:
            self.assertEqual(membership['user']['id'], self.users['student_enrolled_not_on_team'].username)
            self.assertEqual(membership['team']['id'], self.test_team_1.team_id)
            memberships = self.get_membership_list(200, {'team_id': self.test_team_1.team_id})
            self.assertEqual(memberships['count'], 2)

    def test_no_username(self):
        response = self.post_create_membership(400, {'team_id': self.test_team_1.team_id})
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
            self.build_membership_data_raw('no_such_user', self.test_team_1.team_id),
            user='staff'
        )

    @ddt.data('student_enrolled', 'staff', 'course_staff')
    def test_join_twice(self, user):
        response = self.post_create_membership(
            400,
            self.build_membership_data('student_enrolled', self.test_team_1),
            user=user
        )
        self.assertIn('already a member', json.loads(response.content)['developer_message'])

    def test_join_second_team_in_course(self):
        response = self.post_create_membership(
            400,
            self.build_membership_data('student_enrolled_both_courses_other_team', self.test_team_1),
            user='student_enrolled_both_courses_other_team'
        )
        self.assertIn('already a member', json.loads(response.content)['developer_message'])

    @ddt.data('staff', 'course_staff')
    def test_not_enrolled_in_team_course(self, user):
        response = self.post_create_membership(
            400,
            self.build_membership_data('student_unenrolled', self.test_team_1),
            user=user
        )
        self.assertIn('not enrolled', json.loads(response.content)['developer_message'])


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
    )
    @ddt.unpack
    def test_access(self, user, status):
        self.get_membership_detail(
            self.test_team_1.team_id,
            self.users['student_enrolled'].username,
            status,
            user=user
        )

    def test_bad_team(self):
        self.get_membership_detail('no_such_team', self.users['student_enrolled'].username, 404)

    def test_bad_username(self):
        self.get_membership_detail(self.test_team_1.team_id, 'no_such_user', 404)

    def test_no_membership(self):
        self.get_membership_detail(
            self.test_team_1.team_id,
            self.users['student_enrolled_not_on_team'].username,
            404
        )

    def test_expand_user(self):
        result = self.get_membership_detail(
            self.test_team_1.team_id,
            self.users['student_enrolled'].username,
            200,
            {'expand': 'user'}
        )
        self.verify_expanded_user(result['user'])

    def test_expand_team(self):
        result = self.get_membership_detail(
            self.test_team_1.team_id,
            self.users['student_enrolled'].username,
            200,
            {'expand': 'team'}
        )
        self.verify_expanded_team(result['team'])


@ddt.ddt
class TestDeleteMembershipAPI(TeamAPITestCase):
    """Test cases for the membership deletion endpoint."""

    @ddt.data(
        (None, 401),
        ('student_inactive', 401),
        ('student_unenrolled', 404),
        ('student_enrolled_not_on_team', 404),
        ('student_enrolled', 204),
        ('staff', 204),
        ('course_staff', 204),
    )
    @ddt.unpack
    def test_access(self, user, status):
        self.delete_membership(
            self.test_team_1.team_id,
            self.users['student_enrolled'].username,
            status,
            user=user
        )

    def test_bad_team(self):
        self.delete_membership('no_such_team', self.users['student_enrolled'].username, 404)

    def test_bad_username(self):
        self.delete_membership(self.test_team_1.team_id, 'no_such_user', 404)

    def test_missing_membership(self):
        self.delete_membership(self.test_team_2.team_id, self.users['student_enrolled'].username, 404)
