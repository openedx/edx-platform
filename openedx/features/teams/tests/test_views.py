""" All tests for teams application views"""
import urllib

import factory
import mock
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models import signals
from django.test.client import Client
from pyquery import PyQuery
from w3lib.url import add_or_replace_parameter

from lms.djangoapps.onboarding.tests.factories import UserFactory
from lms.djangoapps.teams.tests.factories import CourseTeamMembershipFactory
from openedx.core.djangolib.testing.philu_utils import configure_philu_theme
from openedx.features.teams.tests.factories import CourseTeamFactory
from student.tests.factories import CourseEnrollmentFactory
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

TOTAL_TEAMS = 3
TOTAL_TOPICS = 1
NONE_EXISTING_TEAM_ID = 'team-not-exists'
INVALID_TOPIC_PATTERN = 'invalid'
INVALID_TOPIC_ID = '-1'
TEST_TOPIC_URL = '/topic/test-1'

TEST_USERNAME = 'test_user'
TEST_PASSWORD = 'test_password'


class TeamsTestsBaseClass(ModuleStoreTestCase):
    """Base class for all test cases of "Teams" module."""

    @classmethod
    def setUpClass(cls):
        """ Setup "philu" theme for testing. Required for testing templates that exist in the theme ."""
        super(TeamsTestsBaseClass, cls).setUpClass()
        configure_philu_theme()

    def setUp(self):
        """Setup all test data required for testing any of the test cases. """
        super(TeamsTestsBaseClass, self).setUp()
        self.topic = self._create_topic()
        self.course = self._create_course()

        self.teams = []
        for _ in range(TOTAL_TEAMS):
            self.teams.append(self._create_team(self.course.id, topic_id=self.course.teams_topics[0]['id']))

        self.user = self._create_user()
        self.team_membership = self._create_team_membership(self.teams[0], self.user)

    def _create_topic(self):
        """ Return a topic dict. """
        topic = {u'name': u'T0pic', u'description': u'The best topic!', u'id': u'0', 'url': 'example.com/topic/0'}
        return topic

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def _create_course(self, **kwargs):
        """ Create and return a course with test data """
        org = kwargs.get('org') or 'edX'
        course_number = kwargs.get('course_number') or 'CS101'
        course_run = kwargs.get('course_run') or '2015_Q1'
        display_name = kwargs.get('display_name') or 'test course 1'
        course = CourseFactory.create(
            org=org,
            number=course_number,
            run=course_run,
            display_name=display_name,
            default_store=ModuleStoreEnum.Type.split,
            teams_configuration={
                "max_team_size": 10,
                "topics": [self.topic]
            }
        )
        return course

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def _create_team(self, course_id, topic_id):
        """ Create a CourseTeam for provided course_id and topic_id """
        team = CourseTeamFactory.create(
            course_id=course_id,
            topic_id=topic_id,
            name='Test Team',
            description='Testing Testing Testing...'
        )
        return team

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def _create_user(self, username=TEST_USERNAME, password=TEST_PASSWORD, **kwargs):
        """ Create a User for provided username and password """
        user = UserFactory.create(username=username, password=password, **kwargs)
        return user

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def _create_team_membership(self, team, user):
        """Create a team membership object that is responsible for joining of a user in a team """
        membership = CourseTeamMembershipFactory.create(team=team, user=user)
        return membership

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def _enroll_user_in_course(self, user, course_id):
        """Enroll a user in a course """
        enrollment = CourseEnrollmentFactory(user=user, course_id=course_id)
        return enrollment


class BrowseTeamsTestCase(TeamsTestsBaseClass):
    """Test cases for browse_teams view."""

    def setUp(self):
        """ Initiate the test data which is required in more than one of the test cases. """
        super(BrowseTeamsTestCase, self).setUp()
        self.topic_link_selector = 'a.other-continents-widget'
        self.expexted_teams_count_text = '{} TEAMS'.format(TOTAL_TEAMS)
        self.url = reverse('teams_dashboard', args=[self.course.id])

    def test_anonymous_client_is_redirected(self):
        """Verifies that an anonymous client cannot access the team dashboard, and is redirected to the login page."""
        anonymous_client = Client()
        response = anonymous_client.get(self.url)
        redirect_url = '{0}?next={1}'.format(settings.LOGIN_URL, urllib.quote(self.url))

        self.assertRedirects(response, redirect_url)

    @mock.patch.dict("django.conf.settings.FEATURES", {'ENABLE_TEAMS': False})
    def test_404_case_teams_feature_is_disabled(self):
        """Test that 404 is returned when team feature is disabled."""

        client = Client()
        client.login(username=self.user.username, password=TEST_PASSWORD)
        response = client.get(self.url, follow=False)

        self.assertEqual(response.url, '404/')

    def test_404_case_user_not_enrolled_not_staff(self):
        """Test that 404 is returned if the user is neither enrolled in course nor a staff member."""
        client = Client()
        client.login(username=self.user.username, password=TEST_PASSWORD)
        response = client.get(self.url, follow=False)

        self.assertEqual(response.url, '404/')

    def test_case_user_is_not_enrolled_staff(self):
        """Test that valid data is rendered if user is not enrolled in a course but is a staff member."""
        client = Client()
        staff_user = self._create_user(username='staff_test_user', is_staff=True)
        client.login(username=staff_user.username, password=TEST_PASSWORD)

        response = client.get(self.url)

        content = PyQuery(response.content)
        teams_count_per_topic_exists = bool(content(':contains("{}")'.format(self.expexted_teams_count_text)))
        num_of_topics = len(content(self.topic_link_selector))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(num_of_topics, TOTAL_TOPICS)
        self.assertTrue(teams_count_per_topic_exists)

    def test_case_user_is_enrolled_not_staff(self):
        """Test that correct number of topics and teams are rendered if user is enrolled in a course but
        is not a staff member.
        """
        client = Client()
        self._enroll_user_in_course(user=self.user, course_id=self.course.id)
        client.login(username=self.user.username, password=TEST_PASSWORD)

        response = client.get(self.url)

        content = PyQuery(response.content)
        num_of_topics = len(content(self.topic_link_selector))
        teams_count_per_topic_exists = bool(content(':contains("{}")'.format(self.expexted_teams_count_text)))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(num_of_topics, TOTAL_TOPICS)
        self.assertTrue(teams_count_per_topic_exists)

    def test_case_user_is_enrolled_and_staff(self):
        """Test that correct number of topics and teams are rendered if user is enrolled in a course and
        is a staff member too.
        """
        client = Client()
        staff_user = self._create_user(username='staff_test_user', is_staff=True)
        self._enroll_user_in_course(user=staff_user, course_id=self.course.id)
        client.login(username=staff_user.username, password=TEST_PASSWORD)

        response = client.get(self.url)

        content = PyQuery(response.content)
        num_of_topics = len(content(self.topic_link_selector))
        teams_count_per_topic_exists = bool(content(':contains("{}")'.format(self.expexted_teams_count_text)))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(num_of_topics, TOTAL_TOPICS)
        self.assertTrue(teams_count_per_topic_exists)


class BrowseTopicTeamsTestCase(TeamsTestsBaseClass):
    """Test cases for browse_topic_teams view."""

    def setUp(self):
        super(BrowseTopicTeamsTestCase, self).setUp()
        self.url = reverse('browse_topic_teams', args=[self.course.id, self.topic['id']])

    def test_anonymous_client_is_redirected(self):
        """Verifies that an anonymous client cannot access the edit_team_memberships view, and is redirected
        to the login page.
        """
        anonymous_client = Client()
        redirect_url = '{0}?next={1}'.format(settings.LOGIN_URL, urllib.quote(self.url))
        response = anonymous_client.get(self.url)

        self.assertRedirects(response, redirect_url)

    @mock.patch('openedx.features.teams.decorators.get_course_by_id', autospec=True)
    def test_cannot_access_ended_course(self, mocked_method):
        mocked_course = mocked_method.return_value
        mocked_course.has_ended.return_value = True
        mocked_course.id = self.course.id

        client = Client()
        client.login(username=self.user.username, password=TEST_PASSWORD)

        response = client.get(self.url, follow=False)
        redirect_url = reverse('teams_dashboard', args=[self.course.id])

        self.assertRedirects(response, redirect_url, target_status_code=302)

    def test_404_case_provide_invalid_topic_id(self):
        """Test that 404 is returned when invalid topic_id is provided."""
        client = Client()
        client.login(username=self.user.username, password=TEST_PASSWORD)
        invalid_topic_teams_url = reverse('browse_topic_teams', args=[self.course.id, INVALID_TOPIC_PATTERN])
        response = client.get(invalid_topic_teams_url, follow=True)

        self.assertEqual(response.status_code, 404)

    def test_case_browse_valid_topic_id_teams(self):
        """Test that correct number of teams are displayed when correct topic_id is provided."""
        client = Client()
        client.login(username=self.user.username, password=TEST_PASSWORD)

        response = client.get(self.url)

        team_cards_selector = '.community-card-lits .community-card'
        num_of_team_cards = len(PyQuery(response.content)(team_cards_selector))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(num_of_team_cards, TOTAL_TEAMS)


class CreateTeamTestCase(TeamsTestsBaseClass):
    """Test cases for create_team view."""

    def setUp(self):
        super(CreateTeamTestCase, self).setUp()
        self.url = reverse('create_team', args=[self.course.id, self.topic['id']])

    def test_anonymous_client_is_redirected(self):
        """Verifies that an anonymous client cannot access the create team page, and is redirected
        to the login page.
        """
        anonymous_client = Client()
        response = anonymous_client.get(self.url)
        redirect_url = '{0}?next={1}'.format(settings.LOGIN_URL, urllib.quote(self.url))

        self.assertRedirects(response, redirect_url)

    @mock.patch('openedx.features.teams.decorators.get_course_by_id', autospec=True)
    def test_cannot_access_ended_course(self, mocked_method):
        mocked_course = mocked_method.return_value
        mocked_course.has_ended.return_value = True
        mocked_course.id = self.course.id

        client = Client()
        client.login(username=self.user.username, password=TEST_PASSWORD)

        response = client.get(self.url, follow=False)
        redirect_url = reverse('teams_dashboard', args=[self.course.id])

        self.assertRedirects(response, redirect_url, target_status_code=302)

    def test_404_case_provide_invalid_topic(self):
        """Test that 404 is returned when invalid topic_id is provided"""
        client = Client()
        client.login(username=self.user.username, password=TEST_PASSWORD)
        invalid_team_create_url = reverse('create_team', args=[self.course.id, INVALID_TOPIC_ID])
        response = client.get(invalid_team_create_url, follow=True)

        self.assertEqual(response.status_code, 404)

    @factory.django.mute_signals(signals.post_delete)
    def test_case_create_team_when_user_is_not_joined_in_team(self):
        """Test that "Create Team" header for form is displayed if user is not already a member of
        any team of the course.
        """
        client = Client()
        client.login(username=self.user.username, password=TEST_PASSWORD)
        self.team_membership.delete()

        response = client.get(self.url)

        create_team_form_header_selector = 'div.create-team-instructions'
        is_create_team_header_exists = bool(PyQuery(response.content)(create_team_form_header_selector))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(is_create_team_header_exists)

    def test_case_create_team_when_user_has_already_joined_a_team(self):
        """Test that correct informational message is displayed instead of create team form  if user is already
        a member of any team of the course.
        """
        client = Client()
        client.login(username=self.user.username, password=TEST_PASSWORD)

        response = client.get(self.url)

        already_joined_error_msg_selector = '.screen-reader-message + div p'
        expected_error = 'You are already in a team in this course.'
        error_msg_on_page = PyQuery(response.content)(already_joined_error_msg_selector).html()

        self.assertEqual(response.status_code, 200)
        self.assertIn(expected_error, error_msg_on_page)


class MyTeamTestCase(TeamsTestsBaseClass):
    """Test cases for my_teams view."""

    def setUp(self):
        super(MyTeamTestCase, self).setUp()
        self.url = reverse('my_team', args=[self.course.id])

    @mock.patch('openedx.features.teams.decorators.get_course_by_id', autospec=True)
    def test_cannot_access_ended_course(self, mocked_method):
        mocked_course = mocked_method.return_value
        mocked_course.has_ended.return_value = True
        mocked_course.id = self.course.id

        client = Client()
        client.login(username=self.user.username, password=TEST_PASSWORD)

        response = client.get(self.url, follow=False)
        redirect_url = reverse('teams_dashboard', args=[self.course.id])

        self.assertRedirects(response, redirect_url, target_status_code=302)

    def test_anonymous_client_is_redirected(self):
        """Verifies that an anonymous client cannot access the "my teams" page, and is redirected
        to the login page.
        """
        anonymous_client = Client()
        response = anonymous_client.get(self.url)
        redirect_url = '{0}?next={1}'.format(settings.LOGIN_URL, urllib.quote(self.url))
        self.assertRedirects(response, redirect_url)

    def test_case_no_course_team_exists(self):
        """Test the error response when there is no team for given course id."""
        error_msg_selector = '.teams-content .box-widget p'
        expected_error_msg = 'You are not currently a member of any team.'
        client = Client()
        client.login(username=self.user.username, password=TEST_PASSWORD)
        course_with_no_teams = self._create_course(course_number='CS-102')
        url = reverse('my_team', args=[course_with_no_teams.id])
        response = client.get(url)

        error_msg = PyQuery(response.content)(error_msg_selector).eq(1).html()

        self.assertEqual(response.status_code, 200)
        self.assertIn(expected_error_msg, error_msg)

    def test_case_course_team_exists_and_no_topic_url_is_provided(self):
        """Test that user is redirected to view_team without the topic_url when course team exists and there is no
        topic_url provided with the request
        """
        client = Client()
        client.login(username=self.user.username, password=TEST_PASSWORD)
        response = client.get(self.url, follow=True)
        redirect_url = reverse('view_team', args=[self.course.id, self.teams[0].team_id])

        self.assertRedirects(response, redirect_url)

    def test_case_course_team_exists_and_topic_url_is_provided(self):
        """Test that user is redirected to view_team with topic_url when course team exists and there is no
        topic_url provided with the request
        """
        client = Client()
        client.login(username=self.user.username, password=TEST_PASSWORD)

        response = client.get(self.url, {'topic_url': TEST_TOPIC_URL}, follow=True)

        redirect_url = reverse('view_team', args=[self.course.id, self.teams[0].team_id])
        redirect_url = add_or_replace_parameter(redirect_url, 'topic_url', TEST_TOPIC_URL)

        self.assertRedirects(response, redirect_url)


class ViewTeamTestCase(TeamsTestsBaseClass):
    """Test cases for view_team view."""

    def setUp(self):
        super(ViewTeamTestCase, self).setUp()
        self.url = reverse('view_team', args=[self.course.id, self.teams[0].team_id])

    def test_anonymous_client_is_redirected(self):
        """Verifies that an anonymous client cannot view any team and is redirected to the login page."""
        anonymous_client = Client()
        response = anonymous_client.get(self.url)
        redirect_url = '{0}?next={1}'.format(settings.LOGIN_URL, urllib.quote(self.url))

        self.assertRedirects(response, redirect_url)

    @mock.patch('openedx.features.teams.decorators.get_course_by_id', autospec=True)
    def test_cannot_access_ended_course(self, mocked_method):
        mocked_course = mocked_method.return_value
        mocked_course.has_ended.return_value = True
        mocked_course.id = self.course.id

        client = Client()
        client.login(username=self.user.username, password=TEST_PASSWORD)

        response = client.get(self.url, follow=False)
        redirect_url = reverse('teams_dashboard', args=[self.course.id])

        self.assertRedirects(response, redirect_url, target_status_code=302)

    def test_404_case_no_team_exists_for_provided_team_id(self):
        """Test that 404 is returned when there is no team with provided team id."""
        client = Client()
        url = reverse('view_team', args=[self.course.id, NONE_EXISTING_TEAM_ID])
        client.login(username=self.user.username, password=TEST_PASSWORD)
        response = client.get(url, follow=True)

        self.assertEqual(response.status_code, 404)

    def test_404_case_team_exists_but_no_team_group_chat_exists_for_provided_team_id(self):
        """Test that 404 is returned when there is no team_group_chat for team with provided team id."""
        client = Client()
        team_without_group_chat = self._create_team(self.course.id, self.course.teams_topics[0]['id'])
        team_without_group_chat.team.all().delete()
        url = reverse('view_team', args=[self.course.id, team_without_group_chat.team_id])
        client.login(username=self.user.username, password=TEST_PASSWORD)
        response = client.get(url, follow=True)

        self.assertEqual(response.status_code, 404)

    def test_case_team_and_team_group_chat_exist_for_provided_team_id(self):
        """Test that iframe for team group chat exists and "Edit Membership" button does not exist (which
        only exists for administrator of the team) when Team and TeamGroupChat exists for provided team_id.
        """
        team_edit_button_selector = 'action-edit-team'
        team_iframe_selector = 'div.team-iframe iframe'
        client = Client()
        client.login(username=self.user.username, password=TEST_PASSWORD)

        response = client.get(self.url, follow=True)

        content = PyQuery(response.content)
        team_edit_button_exists = bool(content(team_edit_button_selector))
        team_iframe_exists = bool(content(team_iframe_selector))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(team_edit_button_exists)
        self.assertTrue(team_iframe_exists)


class UpdateTeamTestCase(TeamsTestsBaseClass):
    """Test cases for update_team view."""

    def setUp(self):
        super(UpdateTeamTestCase, self).setUp()
        self.url = reverse('update_team', args=[self.course.id, self.teams[0].team_id])

    def test_anonymous_client_is_redirected(self):
        """Verifies that an anonymous client cannot access the update_team view, and is redirected to
        the login page.
        """
        anonymous_client = Client()
        response = anonymous_client.get(self.url)
        redirect_url = '{0}?next={1}'.format(settings.LOGIN_URL, urllib.quote(self.url))

        self.assertRedirects(response, redirect_url)

    @mock.patch('openedx.features.teams.decorators.get_course_by_id', autospec=True)
    def test_cannot_access_ended_course(self, mocked_method):
        mocked_course = mocked_method.return_value
        mocked_course.has_ended.return_value = True
        mocked_course.id = self.course.id

        client = Client()
        client.login(username=self.user.username, password=TEST_PASSWORD)

        response = client.get(self.url, follow=False)
        redirect_url = reverse('teams_dashboard', args=[self.course.id])

        self.assertRedirects(response, redirect_url, target_status_code=302)

    def test_404_case_user_is_not_staff(self):
        """Test that 404 is returned when current user is not staff member."""
        client = Client()
        client.login(username=self.user.username, password=TEST_PASSWORD)
        response = client.get(self.url, follow=True)

        self.assertEqual(response.status_code, 404)

    def test_404_case_user_is_staff_but_no_team_exists_for_provided_team_id(self):
        """Test that 404 is returned when current user is staff but there is no team with provided team id."""
        client = Client()
        staff_user = self._create_user(username='staff_test_user', is_staff=True)
        client.login(username=staff_user.username, password=TEST_PASSWORD)
        url = reverse('update_team', args=[self.course.id, NONE_EXISTING_TEAM_ID])
        response = client.get(url, follow=True)

        self.assertEqual(response.status_code, 404)

    def test_case_user_is_staff_and_team_exists_for_provided_team_id(self):
        """Test that "Edit Membership" and "Update Team" form buttons are displayed when current user is staff
        and there is existing team for provided team_id
        """
        edit_membership_button_selector = '.action-edit-members'
        update_team_button_selector = 'div.create-team.form-actions span.sr'
        expected_update_team_button_text = 'Update team'
        client = Client()
        staff_user = self._create_user(username='staff_test_user', is_staff=True)
        client.login(username=staff_user.username, password=TEST_PASSWORD)

        response = client.get(self.url)

        content = PyQuery(response.content)
        edit_membership_button_exists = bool(content(edit_membership_button_selector))
        update_team_button_text = content(update_team_button_selector).eq(0).html()

        self.assertEqual(response.status_code, 200)
        self.assertIn(expected_update_team_button_text, update_team_button_text)
        self.assertTrue(edit_membership_button_exists)


class EditTeamMembershitTestCase(TeamsTestsBaseClass):
    """Test cases for edit_team_memberships view."""

    def setUp(self):
        super(EditTeamMembershitTestCase, self).setUp()
        self.url = reverse('edit_team_memberships', args=[self.course.id, self.teams[0].team_id])

    def test_anonymous_client_is_redirected(self):
        """Verifies that an anonymous client cannot access the edit_team_memberships view, and is redirected
        to the login page.
        """
        anonymous_client = Client()
        redirect_url = '{0}?next={1}'.format(settings.LOGIN_URL, urllib.quote(self.url))
        response = anonymous_client.get(self.url)

        self.assertRedirects(response, redirect_url)

    @mock.patch('openedx.features.teams.decorators.get_course_by_id', autospec=True)
    def test_cannot_access_ended_course(self, mocked_method):
        mocked_course = mocked_method.return_value
        mocked_course.has_ended.return_value = True
        mocked_course.id = self.course.id

        client = Client()
        client.login(username=self.user.username, password=TEST_PASSWORD)

        response = client.get(self.url, follow=False)
        redirect_url = reverse('teams_dashboard', args=[self.course.id])

        self.assertRedirects(response, redirect_url, target_status_code=302)

    def test_404_case_user_is_not_staff(self):
        """Test that 404 is returned when current user is not a staff member"""
        client = Client()
        client.login(username=self.user.username, password=TEST_PASSWORD)
        response = client.get(self.url, follow=True)

        self.assertEqual(response.status_code, 404)

    def test_404_case_user_is_staff_but_no_team_exists_for_provided_team_id(self):
        """Test that 404 is returned when current user is staff user but there is no team with provided team id."""
        client = Client()
        staff_user = self._create_user(username='staff_test_user', is_staff=True)
        client.login(username=staff_user.username, password=TEST_PASSWORD)
        url = reverse('edit_team_memberships', args=[self.course.id, NONE_EXISTING_TEAM_ID])
        response = client.get(url, follow=True)

        self.assertEqual(response.status_code, 404)

    def test_case_user_is_staff_and_team_exists_for_provided_team_id(self):
        """Test that correct number of team members are displayed for their membership to be edited when current user
        is a staff user and there is existing team for provided team_id
        """
        team_member_selector = 'li.team-member'
        expected_team_members_count = 1
        client = Client()
        staff_user = self._create_user(username='staff_test_user', is_staff=True)
        client.login(username=staff_user.username, password=TEST_PASSWORD)

        response = client.get(self.url, follow=True)
        team_members_count = len(PyQuery(response.content)(team_member_selector))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(team_members_count, expected_team_members_count)
