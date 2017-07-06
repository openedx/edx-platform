"""
Acceptance tests for the teams feature.
"""
import json
import random
import time

from dateutil.parser import parse
import ddt
from nose.plugins.attrib import attr
from selenium.common.exceptions import TimeoutException
from uuid import uuid4

from common.test.acceptance.tests.helpers import get_modal_alert, EventsTestMixin, UniqueCourseTest
from common.test.acceptance.fixtures import LMS_BASE_URL
from common.test.acceptance.fixtures.course import CourseFixture
from common.test.acceptance.fixtures.discussion import (
    Thread,
    MultipleThreadFixture
)
from common.test.acceptance.pages.lms.auto_auth import AutoAuthPage
from common.test.acceptance.pages.lms.course_info import CourseInfoPage
from common.test.acceptance.pages.lms.learner_profile import LearnerProfilePage
from common.test.acceptance.pages.lms.tab_nav import TabNavPage
from common.test.acceptance.pages.lms.teams import (
    TeamsPage,
    MyTeamsPage,
    BrowseTopicsPage,
    BrowseTeamsPage,
    TeamManagementPage,
    EditMembershipPage,
    TeamPage
)
from common.test.acceptance.pages.common.utils import confirm_prompt


TOPICS_PER_PAGE = 12


class TeamsTabBase(EventsTestMixin, UniqueCourseTest):
    """Base class for Teams Tab tests"""
    def setUp(self):
        super(TeamsTabBase, self).setUp()
        self.tab_nav = TabNavPage(self.browser)
        self.course_info_page = CourseInfoPage(self.browser, self.course_id)
        self.teams_page = TeamsPage(self.browser, self.course_id)
        # TODO: Refactor so resetting events database is not necessary
        self.reset_event_tracking()

    def create_topics(self, num_topics):
        """Create `num_topics` test topics."""
        return [{u"description": i, u"name": i, u"id": i} for i in map(str, xrange(num_topics))]

    def create_teams(self, topic, num_teams, time_between_creation=0):
        """Create `num_teams` teams belonging to `topic`."""
        teams = []
        for i in xrange(num_teams):
            team = {
                'course_id': self.course_id,
                'topic_id': topic['id'],
                'name': 'Team {}'.format(i),
                'description': 'Description {}'.format(i),
                'language': 'aa',
                'country': 'AF'
            }
            teams.append(self.post_team_data(team))
            # Sadly, this sleep is necessary in order to ensure that
            # sorting by last_activity_at works correctly when running
            # in Jenkins.
            time.sleep(time_between_creation)
        return teams

    def post_team_data(self, team_data):
        """Given a JSON representation of a team, post it to the server."""
        response = self.course_fixture.session.post(
            LMS_BASE_URL + '/api/team/v0/teams/',
            data=json.dumps(team_data),
            headers=self.course_fixture.headers
        )
        self.assertEqual(response.status_code, 200)
        return json.loads(response.text)

    def create_memberships(self, num_memberships, team_id):
        """Create `num_memberships` users and assign them to `team_id`. The
        last user created becomes the current user."""
        memberships = []
        for __ in xrange(num_memberships):
            user_info = AutoAuthPage(self.browser, course_id=self.course_id).visit().user_info
            memberships.append(user_info)
            self.create_membership(user_info['username'], team_id)
        #pylint: disable=attribute-defined-outside-init
        self.user_info = memberships[-1]
        return memberships

    def create_membership(self, username, team_id):
        """Assign `username` to `team_id`."""
        response = self.course_fixture.session.post(
            LMS_BASE_URL + '/api/team/v0/team_membership/',
            data=json.dumps({'username': username, 'team_id': team_id}),
            headers=self.course_fixture.headers
        )
        return json.loads(response.text)

    def set_team_configuration(self, configuration, enroll_in_course=True, global_staff=False):
        """
        Sets team configuration on the course and calls auto-auth on the user.
        """
        #pylint: disable=attribute-defined-outside-init
        self.course_fixture = CourseFixture(**self.course_info)
        if configuration:
            self.course_fixture.add_advanced_settings(
                {u"teams_configuration": {u"value": configuration}}
            )
        self.course_fixture.install()

        enroll_course_id = self.course_id if enroll_in_course else None
        #pylint: disable=attribute-defined-outside-init
        self.user_info = AutoAuthPage(self.browser, course_id=enroll_course_id, staff=global_staff).visit().user_info
        self.course_info_page.visit()

    def verify_teams_present(self, present):
        """
        Verifies whether or not the teams tab is present. If it should be present, also
        checks the text on the page (to ensure view is working).
        """
        if present:
            self.assertIn("Teams", self.tab_nav.tab_names)
            self.teams_page.visit()
            self.assertEqual(self.teams_page.active_tab(), 'browse')
        else:
            self.assertNotIn("Teams", self.tab_nav.tab_names)

    def verify_teams(self, page, expected_teams):
        """Verify that the list of team cards on the current page match the expected teams in order."""

        def assert_team_equal(expected_team, team_card_name, team_card_description):
            """
            Helper to assert that a single team card has the expected name and
            description.
            """
            self.assertEqual(expected_team['name'], team_card_name)
            self.assertEqual(expected_team['description'], team_card_description)

        team_card_names = page.team_names
        team_card_descriptions = page.team_descriptions
        map(assert_team_equal, expected_teams, team_card_names, team_card_descriptions)

    def verify_my_team_count(self, expected_number_of_teams):
        """ Verify the number of teams shown on "My Team". """

        # We are doing these operations on this top-level page object to avoid reloading the page.
        self.teams_page.verify_my_team_count(expected_number_of_teams)

    def only_team_events(self, event):
        """Filter out all non-team events."""
        return event['event_type'].startswith('edx.team.')


@ddt.ddt
@attr('shard_5')
class TeamsTabTest(TeamsTabBase):
    """
    Tests verifying when the Teams tab is present.
    """
    def test_teams_not_enabled(self):
        """
        Scenario: teams tab should not be present if no team configuration is set
        Given I am enrolled in a course without team configuration
        When I view the course info page
        Then I should not see the Teams tab
        """
        self.set_team_configuration(None)
        self.verify_teams_present(False)

    def test_teams_not_enabled_no_topics(self):
        """
        Scenario: teams tab should not be present if team configuration does not specify topics
        Given I am enrolled in a course with no topics in the team configuration
        When I view the course info page
        Then I should not see the Teams tab
        """
        self.set_team_configuration({u"max_team_size": 10, u"topics": []})
        self.verify_teams_present(False)

    def test_teams_not_enabled_not_enrolled(self):
        """
        Scenario: teams tab should not be present if student is not enrolled in the course
        Given there is a course with team configuration and topics

        And I am not enrolled in that course, and am not global staff
        When I view the course info page
        Then I should not see the Teams tab
        """
        self.set_team_configuration(
            {u"max_team_size": 10, u"topics": self.create_topics(1)},
            enroll_in_course=False
        )
        self.verify_teams_present(False)

    def test_teams_enabled(self):
        """
        Scenario: teams tab should be present if user is enrolled in the course and it has team configuration
        Given I am enrolled in a course with team configuration and topics
        When I view the course info page
        Then I should see the Teams tab
        And the correct content should be on the page
        """
        self.set_team_configuration({u"max_team_size": 10, u"topics": self.create_topics(1)})
        self.verify_teams_present(True)

    def test_teams_enabled_global_staff(self):
        """
        Scenario: teams tab should be present if user is not enrolled in the course, but is global staff
        Given there is a course with team configuration
        And I am not enrolled in that course, but am global staff
        When I view the course info page
        Then I should see the Teams tab
        And the correct content should be on the page
        """
        self.set_team_configuration(
            {u"max_team_size": 10, u"topics": self.create_topics(1)},
            enroll_in_course=False,
            global_staff=True
        )
        self.verify_teams_present(True)

    @ddt.data(
        'topics/{topic_id}',
        'topics/{topic_id}/search',
        'teams/{topic_id}/{team_id}/edit-team',
        'teams/{topic_id}/{team_id}'
    )
    def test_unauthorized_error_message(self, route):
        """Ensure that an error message is shown to the user if they attempt
        to take an action which makes an AJAX request while not signed
        in.
        """
        topics = self.create_topics(1)
        topic = topics[0]
        self.set_team_configuration(
            {u'max_team_size': 10, u'topics': topics},
            global_staff=True
        )
        team = self.create_teams(topic, 1)[0]
        self.teams_page.visit()
        self.browser.delete_cookie('sessionid')
        url = self.browser.current_url.split('#')[0]
        self.browser.get(
            '{url}#{route}'.format(
                url=url,
                route=route.format(
                    topic_id=topic['id'],
                    team_id=team['id']
                )
            )
        )
        self.teams_page.wait_for_ajax()
        self.assertEqual(
            self.teams_page.warning_message,
            u"Your request could not be completed. Reload the page and try again."
        )

    @ddt.data(
        ('browse', '.topics-list'),
        # TODO: find a reliable way to match the "My Teams" tab
        # ('my-teams', 'div.teams-list'),
        ('teams/{topic_id}/{team_id}', 'div.discussion-module'),
        ('topics/{topic_id}/create-team', 'div.create-team-instructions'),
        ('topics/{topic_id}', '.teams-list'),
        ('not-a-real-route', 'div.warning')
    )
    @ddt.unpack
    def test_url_routing(self, route, selector):
        """Ensure that navigating to a URL route correctly updates the page
        content.
        """
        topics = self.create_topics(1)
        topic = topics[0]
        self.set_team_configuration({
            u'max_team_size': 10,
            u'topics': topics
        })
        team = self.create_teams(topic, 1)[0]
        self.teams_page.visit()

        # Get the base URL (the URL without any trailing fragment)
        url = self.browser.current_url
        fragment_index = url.find('#')
        if fragment_index >= 0:
            url = url[0:fragment_index]

        self.browser.get(
            '{url}#{route}'.format(
                url=url,
                route=route.format(
                    topic_id=topic['id'],
                    team_id=team['id']
                ))
        )
        self.teams_page.wait_for_page()
        self.teams_page.wait_for_ajax()
        self.assertTrue(self.teams_page.q(css=selector).present)
        self.assertTrue(self.teams_page.q(css=selector).visible)


@attr('shard_5')
class MyTeamsTest(TeamsTabBase):
    """
    Tests for the "My Teams" tab of the Teams page.
    """

    def setUp(self):
        super(MyTeamsTest, self).setUp()
        self.topic = {u"name": u"Example Topic", u"id": "example_topic", u"description": "Description"}
        self.set_team_configuration({'course_id': self.course_id, 'max_team_size': 10, 'topics': [self.topic]})
        self.my_teams_page = MyTeamsPage(self.browser, self.course_id)
        self.page_viewed_event = {
            'event_type': 'edx.team.page_viewed',
            'event': {
                'page_name': 'my-teams',
                'topic_id': None,
                'team_id': None
            }
        }

    def test_not_member_of_any_teams(self):
        """
        Scenario: Visiting the My Teams page when user is not a member of any team should not display any teams.
        Given I am enrolled in a course with a team configuration and a topic but am not a member of a team
        When I visit the My Teams page
        And I should see no teams
        And I should see a message that I belong to no teams.
        """
        with self.assert_events_match_during(self.only_team_events, expected_events=[self.page_viewed_event]):
            self.my_teams_page.visit()
        self.assertEqual(len(self.my_teams_page.team_cards), 0, msg='Expected to see no team cards')
        self.assertEqual(
            self.my_teams_page.q(css='.page-content-main').text,
            [u'You are not currently a member of any team.']
        )

    def test_member_of_a_team(self):
        """
        Scenario: Visiting the My Teams page when user is a member of a team should display the teams.
        Given I am enrolled in a course with a team configuration and a topic and am a member of a team
        When I visit the My Teams page
        Then I should see a pagination header showing the number of teams
        And I should see all the expected team cards
        And I should not see a pagination footer
        """
        teams = self.create_teams(self.topic, 1)
        self.create_membership(self.user_info['username'], teams[0]['id'])
        with self.assert_events_match_during(self.only_team_events, expected_events=[self.page_viewed_event]):
            self.my_teams_page.visit()
        self.verify_teams(self.my_teams_page, teams)

    def test_multiple_team_members(self):
        """
        Scenario: Visiting the My Teams page when user is a member of a team should display the teams.
        Given I am a member of a team with multiple members
        When I visit the My Teams page
        Then I should see the correct number of team members on my membership
        """
        teams = self.create_teams(self.topic, 1)
        self.create_memberships(4, teams[0]['id'])
        self.my_teams_page.visit()
        self.assertEqual(self.my_teams_page.team_memberships[0], '4 / 10 Members')


@attr('shard_5')
@ddt.ddt
class BrowseTopicsTest(TeamsTabBase):
    """
    Tests for the Browse tab of the Teams page.
    """

    def setUp(self):
        super(BrowseTopicsTest, self).setUp()
        self.topics_page = BrowseTopicsPage(self.browser, self.course_id)

    @ddt.data(('name', False), ('team_count', True))
    @ddt.unpack
    def test_sort_topics(self, sort_order, reverse):
        """
        Scenario: the user should be able to sort the list of topics by name or team count
        Given I am enrolled in a course with team configuration and topics
        When I visit the Teams page
        And I browse topics
        Then I should see a list of topics for the course
        When I choose a sort order
        Then I should see the paginated list of topics in that order
        """
        topics = self.create_topics(TOPICS_PER_PAGE + 1)
        self.set_team_configuration({u"max_team_size": 100, u"topics": topics})
        for i, topic in enumerate(random.sample(topics, len(topics))):
            self.create_teams(topic, i)
            topic['team_count'] = i
        self.topics_page.visit()
        self.topics_page.sort_topics_by(sort_order)
        topic_names = self.topics_page.topic_names
        self.assertEqual(len(topic_names), TOPICS_PER_PAGE)
        self.assertEqual(
            topic_names,
            [t['name'] for t in sorted(topics, key=lambda t: t[sort_order], reverse=reverse)][:TOPICS_PER_PAGE]
        )

    def test_sort_topics_update(self):
        """
        Scenario: the list of topics should remain sorted after updates
        Given I am enrolled in a course with team configuration and topics
        When I visit the Teams page
        And I browse topics and choose a sort order
        Then I should see the paginated list of topics in that order
        When I create a team in one of those topics
        And I return to the topics list
        Then I should see the topics in the correct sorted order
        """
        topics = self.create_topics(3)
        self.set_team_configuration({u"max_team_size": 100, u"topics": topics})
        self.topics_page.visit()
        self.topics_page.sort_topics_by('team_count')
        topic_name = self.topics_page.topic_names[-1]
        topic = [t for t in topics if t['name'] == topic_name][0]
        self.topics_page.browse_teams_for_topic(topic_name)
        browse_teams_page = BrowseTeamsPage(self.browser, self.course_id, topic)
        self.assertTrue(browse_teams_page.is_browser_on_page())
        browse_teams_page.click_create_team_link()
        create_team_page = TeamManagementPage(self.browser, self.course_id, topic)
        create_team_page.value_for_text_field(field_id='name', value='Team Name', press_enter=False)
        create_team_page.set_value_for_textarea_field(
            field_id='description',
            value='Team description.'
        )
        create_team_page.submit_form()
        team_page = TeamPage(self.browser, self.course_id)
        self.assertTrue(team_page.is_browser_on_page())
        team_page.click_all_topics()
        self.assertTrue(self.topics_page.is_browser_on_page())
        self.topics_page.wait_for_ajax()
        self.assertEqual(topic_name, self.topics_page.topic_names[0])

    def test_list_topics(self):
        """
        Scenario: a list of topics should be visible in the "Browse" tab
        Given I am enrolled in a course with team configuration and topics
        When I visit the Teams page
        And I browse topics
        Then I should see a list of topics for the course
        """
        self.set_team_configuration({u"max_team_size": 10, u"topics": self.create_topics(2)})
        self.topics_page.visit()
        self.assertEqual(len(self.topics_page.topic_cards), 2)
        self.assertTrue(self.topics_page.get_pagination_header_text().startswith('Showing 1-2 out of 2 total'))
        self.assertFalse(self.topics_page.pagination_controls_visible())
        self.assertFalse(self.topics_page.is_previous_page_button_enabled())
        self.assertFalse(self.topics_page.is_next_page_button_enabled())

    def test_topic_pagination(self):
        """
        Scenario: a list of topics should be visible in the "Browse" tab, paginated 12 per page
        Given I am enrolled in a course with team configuration and topics
        When I visit the Teams page
        And I browse topics
        Then I should see only the first 12 topics
        """
        self.set_team_configuration({u"max_team_size": 10, u"topics": self.create_topics(20)})
        self.topics_page.visit()
        self.assertEqual(len(self.topics_page.topic_cards), TOPICS_PER_PAGE)
        self.assertTrue(self.topics_page.get_pagination_header_text().startswith('Showing 1-12 out of 20 total'))
        self.assertTrue(self.topics_page.pagination_controls_visible())
        self.assertFalse(self.topics_page.is_previous_page_button_enabled())
        self.assertTrue(self.topics_page.is_next_page_button_enabled())

    def test_go_to_numbered_page(self):
        """
        Scenario: topics should be able to be navigated by page number
        Given I am enrolled in a course with team configuration and topics
        When I visit the Teams page
        And I browse topics
        And I enter a valid page number in the page number input
        Then I should see that page of topics
        """
        self.set_team_configuration({u"max_team_size": 10, u"topics": self.create_topics(25)})
        self.topics_page.visit()
        self.topics_page.go_to_page(3)
        self.assertEqual(len(self.topics_page.topic_cards), 1)
        self.assertTrue(self.topics_page.is_previous_page_button_enabled())
        self.assertFalse(self.topics_page.is_next_page_button_enabled())

    def test_go_to_invalid_page(self):
        """
        Scenario: browsing topics should not respond to invalid page numbers
        Given I am enrolled in a course with team configuration and topics
        When I visit the Teams page
        And I browse topics
        And I enter an invalid page number in the page number input
        Then I should stay on the current page
        """
        self.set_team_configuration({u"max_team_size": 10, u"topics": self.create_topics(13)})
        self.topics_page.visit()
        self.topics_page.go_to_page(3)
        self.assertEqual(self.topics_page.get_current_page_number(), 1)

    def test_page_navigation_buttons(self):
        """
        Scenario: browsing topics should not respond to invalid page numbers
        Given I am enrolled in a course with team configuration and topics
        When I visit the Teams page
        And I browse topics
        When I press the next page button
        Then I should move to the next page
        When I press the previous page button
        Then I should move to the previous page
        """
        self.set_team_configuration({u"max_team_size": 10, u"topics": self.create_topics(13)})
        self.topics_page.visit()
        self.topics_page.press_next_page_button()
        self.assertEqual(len(self.topics_page.topic_cards), 1)
        self.assertTrue(self.topics_page.get_pagination_header_text().startswith('Showing 13-13 out of 13 total'))
        self.topics_page.press_previous_page_button()
        self.assertEqual(len(self.topics_page.topic_cards), TOPICS_PER_PAGE)
        self.assertTrue(self.topics_page.get_pagination_header_text().startswith('Showing 1-12 out of 13 total'))

    def test_topic_pagination_one_page(self):
        """
        Scenario: Browsing topics when there are fewer topics than the page size i.e. 12
            all topics should show on one page
        Given I am enrolled in a course with team configuration and topics
        When I visit the Teams page
        And I browse topics
        And I should see corrected number of topic cards
        And I should see the correct page header
        And I should not see a pagination footer
        """
        self.set_team_configuration({u"max_team_size": 10, u"topics": self.create_topics(10)})
        self.topics_page.visit()
        self.assertEqual(len(self.topics_page.topic_cards), 10)
        self.assertTrue(self.topics_page.get_pagination_header_text().startswith('Showing 1-10 out of 10 total'))
        self.assertFalse(self.topics_page.pagination_controls_visible())

    def test_topic_description_truncation(self):
        """
        Scenario: excessively long topic descriptions should be truncated so
            as to fit within a topic card.
        Given I am enrolled in a course with a team configuration and a topic
            with a long description
        When I visit the Teams page
        And I browse topics
        Then I should see a truncated topic description
        """
        initial_description = "A" + " really" * 50 + " long description"
        self.set_team_configuration(
            {u"max_team_size": 1, u"topics": [{"name": "", "id": "", "description": initial_description}]}
        )
        self.topics_page.visit()
        truncated_description = self.topics_page.topic_descriptions[0]
        self.assertLess(len(truncated_description), len(initial_description))
        self.assertTrue(truncated_description.endswith('...'))
        self.assertIn(truncated_description.split('...')[0], initial_description)

    def test_go_to_teams_list(self):
        """
        Scenario: Clicking on a Topic Card should take you to the
            teams list for that Topic.
        Given I am enrolled in a course with a team configuration and a topic
        When I visit the Teams page
        And I browse topics
        And I click on the arrow link to view teams for the first topic
        Then I should be on the browse teams page
        """
        topic = {u"name": u"Example Topic", u"id": u"example_topic", u"description": "Description"}
        self.set_team_configuration(
            {u"max_team_size": 1, u"topics": [topic]}
        )
        self.topics_page.visit()
        self.topics_page.browse_teams_for_topic('Example Topic')
        browse_teams_page = BrowseTeamsPage(self.browser, self.course_id, topic)
        self.assertTrue(browse_teams_page.is_browser_on_page())
        self.assertEqual(browse_teams_page.header_name, 'Example Topic')
        self.assertEqual(browse_teams_page.header_description, 'Description')

    def test_page_viewed_event(self):
        """
        Scenario: Visiting the browse topics page should fire a page viewed event.
        Given I am enrolled in a course with a team configuration and a topic
        When I visit the browse topics page
        Then my browser should post a page viewed event
        """
        topic = {u"name": u"Example Topic", u"id": u"example_topic", u"description": "Description"}
        self.set_team_configuration(
            {u"max_team_size": 1, u"topics": [topic]}
        )
        events = [{
            'event_type': 'edx.team.page_viewed',
            'event': {
                'page_name': 'browse',
                'topic_id': None,
                'team_id': None
            }
        }]
        with self.assert_events_match_during(self.only_team_events, expected_events=events):
            self.topics_page.visit()


@attr('shard_5')
@ddt.ddt
class BrowseTeamsWithinTopicTest(TeamsTabBase):
    """
    Tests for browsing Teams within a Topic on the Teams page.
    """
    TEAMS_PAGE_SIZE = 10

    def setUp(self):
        super(BrowseTeamsWithinTopicTest, self).setUp()
        self.topic = {u"name": u"Example Topic", u"id": "example_topic", u"description": "Description"}
        self.max_team_size = 10
        self.set_team_configuration({
            'course_id': self.course_id,
            'max_team_size': self.max_team_size,
            'topics': [self.topic]
        })
        self.browse_teams_page = BrowseTeamsPage(self.browser, self.course_id, self.topic)
        self.topics_page = BrowseTopicsPage(self.browser, self.course_id)

    def teams_with_default_sort_order(self, teams):
        """Return a list of teams sorted according to the default ordering
        (last_activity_at, with a secondary sort by open slots).
        """
        return sorted(
            sorted(teams, key=lambda t: len(t['membership']), reverse=True),
            key=lambda t: parse(t['last_activity_at']).replace(microsecond=0),
            reverse=True
        )

    def verify_page_header(self):
        """Verify that the page header correctly reflects the current topic's name and description."""
        self.assertEqual(self.browse_teams_page.header_name, self.topic['name'])
        self.assertEqual(self.browse_teams_page.header_description, self.topic['description'])

    def verify_search_header(self, search_results_page, search_query):
        """Verify that the page header correctly reflects the current topic's name and description."""
        self.assertEqual(search_results_page.header_name, 'Team Search')
        self.assertEqual(
            search_results_page.header_description,
            'Showing results for "{search_query}"'.format(search_query=search_query)
        )

    def verify_on_page(self, teams_page, page_num, total_teams, pagination_header_text, footer_visible):
        """
        Verify that we are on the correct team list page.

        Arguments:
            teams_page (BaseTeamsPage): The teams page object that should be the current page.
            page_num (int): The one-indexed page number that we expect to be on
            total_teams (list): An unsorted list of all the teams for the
                current topic
            pagination_header_text (str): Text we expect to see in the
                pagination header.
            footer_visible (bool): Whether we expect to see the pagination
                footer controls.
        """
        sorted_teams = self.teams_with_default_sort_order(total_teams)
        self.assertTrue(teams_page.get_pagination_header_text().startswith(pagination_header_text))
        self.verify_teams(
            teams_page,
            sorted_teams[(page_num - 1) * self.TEAMS_PAGE_SIZE:page_num * self.TEAMS_PAGE_SIZE]
        )
        self.assertEqual(
            teams_page.pagination_controls_visible(),
            footer_visible,
            msg='Expected paging footer to be ' + 'visible' if footer_visible else 'invisible'
        )

    @ddt.data(
        ('open_slots', 'last_activity_at', True),
        ('last_activity_at', 'open_slots', True)
    )
    @ddt.unpack
    def test_sort_teams(self, sort_order, secondary_sort_order, reverse):
        """
        Scenario: the user should be able to sort the list of teams by open slots or last activity
        Given I am enrolled in a course with team configuration and topics
        When I visit the Teams page
        And I browse teams within a topic
        Then I should see a list of teams for that topic
        When I choose a sort order
        Then I should see the paginated list of teams in that order
        """
        teams = self.create_teams(self.topic, self.TEAMS_PAGE_SIZE + 1)
        for i, team in enumerate(random.sample(teams, len(teams))):
            for _ in range(i):
                user_info = AutoAuthPage(self.browser, course_id=self.course_id).visit().user_info
                self.create_membership(user_info['username'], team['id'])
            team['open_slots'] = self.max_team_size - i

        # Re-authenticate as staff after creating users
        AutoAuthPage(
            self.browser,
            course_id=self.course_id,
            staff=True
        ).visit()
        self.browse_teams_page.visit()
        self.browse_teams_page.sort_teams_by(sort_order)
        team_names = self.browse_teams_page.team_names
        self.assertEqual(len(team_names), self.TEAMS_PAGE_SIZE)
        sorted_teams = [
            team['name']
            for team in sorted(
                sorted(teams, key=lambda t: t[secondary_sort_order], reverse=reverse),
                key=lambda t: t[sort_order],
                reverse=reverse
            )
        ][:self.TEAMS_PAGE_SIZE]
        self.assertEqual(team_names, sorted_teams)

    def test_default_sort_order(self):
        """
        Scenario: the list of teams should be sorted by last activity by default
        Given I am enrolled in a course with team configuration and topics
        When I visit the Teams page
        And I browse teams within a topic
        Then I should see a list of teams for that topic, sorted by last activity
        """
        self.create_teams(self.topic, self.TEAMS_PAGE_SIZE + 1)
        self.browse_teams_page.visit()
        self.assertEqual(self.browse_teams_page.sort_order, 'last activity')

    def test_no_teams(self):
        """
        Scenario: Visiting a topic with no teams should not display any teams.
        Given I am enrolled in a course with a team configuration and a topic
        When I visit the Teams page for that topic
        Then I should see the correct page header
        And I should see a pagination header showing no teams
        And I should see no teams
        And I should see a button to add a team
        And I should not see a pagination footer
        """
        self.browse_teams_page.visit()
        self.verify_page_header()
        self.assertTrue(self.browse_teams_page.get_pagination_header_text().startswith('Showing 0 out of 0 total'))
        self.assertEqual(len(self.browse_teams_page.team_cards), 0, msg='Expected to see no team cards')
        self.assertFalse(
            self.browse_teams_page.pagination_controls_visible(),
            msg='Expected paging footer to be invisible'
        )

    def test_teams_one_page(self):
        """
        Scenario: Visiting a topic with fewer teams than the page size should
            all those teams on one page.
        Given I am enrolled in a course with a team configuration and a topic
        When I visit the Teams page for that topic
        Then I should see the correct page header
        And I should see a pagination header showing the number of teams
        And I should see all the expected team cards
        And I should see a button to add a team
        And I should not see a pagination footer
        """
        teams = self.teams_with_default_sort_order(
            self.create_teams(self.topic, self.TEAMS_PAGE_SIZE, time_between_creation=1)
        )
        self.browse_teams_page.visit()
        self.verify_page_header()
        self.assertTrue(self.browse_teams_page.get_pagination_header_text().startswith('Showing 1-10 out of 10 total'))
        self.verify_teams(self.browse_teams_page, teams)
        self.assertFalse(
            self.browse_teams_page.pagination_controls_visible(),
            msg='Expected paging footer to be invisible'
        )

    def test_teams_navigation_buttons(self):
        """
        Scenario: The user should be able to page through a topic's team list
            using navigation buttons when it is longer than the page size.
        Given I am enrolled in a course with a team configuration and a topic
        When I visit the Teams page for that topic
        Then I should see the correct page header
        And I should see that I am on the first page of results
        When I click on the next page button
        Then I should see that I am on the second page of results
        And when I click on the previous page button
        Then I should see that I am on the first page of results
        """
        teams = self.create_teams(self.topic, self.TEAMS_PAGE_SIZE + 1, time_between_creation=1)
        self.browse_teams_page.visit()
        self.verify_page_header()
        self.verify_on_page(self.browse_teams_page, 1, teams, 'Showing 1-10 out of 11 total', True)
        self.browse_teams_page.press_next_page_button()
        self.verify_on_page(self.browse_teams_page, 2, teams, 'Showing 11-11 out of 11 total', True)
        self.browse_teams_page.press_previous_page_button()
        self.verify_on_page(self.browse_teams_page, 1, teams, 'Showing 1-10 out of 11 total', True)

    def test_teams_page_input(self):
        """
        Scenario: The user should be able to page through a topic's team list
            using the page input when it is longer than the page size.
        Given I am enrolled in a course with a team configuration and a topic
        When I visit the Teams page for that topic
        Then I should see the correct page header
        And I should see that I am on the first page of results
        When I input the second page
        Then I should see that I am on the second page of results
        When I input the first page
        Then I should see that I am on the first page of results
        """
        teams = self.create_teams(self.topic, self.TEAMS_PAGE_SIZE + 10, time_between_creation=1)
        self.browse_teams_page.visit()
        self.verify_page_header()
        self.verify_on_page(self.browse_teams_page, 1, teams, 'Showing 1-10 out of 20 total', True)
        self.browse_teams_page.go_to_page(2)
        self.verify_on_page(self.browse_teams_page, 2, teams, 'Showing 11-20 out of 20 total', True)
        self.browse_teams_page.go_to_page(1)
        self.verify_on_page(self.browse_teams_page, 1, teams, 'Showing 1-10 out of 20 total', True)

    def test_browse_team_topics(self):
        """
        Scenario: User should be able to navigate to "browse all teams" and "search team description" links.
        Given I am enrolled in a course with teams enabled
        When I visit the Teams page for a topic
        Then I should see the correct page header
        And I should see the link to "browse teams in other topics"
        When I should navigate to that link
        Then I should see the topic browse page
        """
        self.browse_teams_page.visit()
        self.verify_page_header()

        self.browse_teams_page.click_browse_all_teams_link()
        self.assertTrue(self.topics_page.is_browser_on_page())

    def test_search(self):
        """
        Scenario: User should be able to search for a team
        Given I am enrolled in a course with teams enabled
        When I visit the Teams page for that topic
        And I search for 'banana'
        Then I should see the search result page
        And the search header should be shown
        And 0 results should be shown
        And my browser should fire a page viewed event for the search page
        And a searched event should have been fired
        """
        # Note: all searches will return 0 results with the mock search server
        # used by Bok Choy.
        search_text = 'banana'
        self.create_teams(self.topic, 5)
        self.browse_teams_page.visit()
        events = [{
            'event_type': 'edx.team.page_viewed',
            'event': {
                'page_name': 'search-teams',
                'topic_id': self.topic['id'],
                'team_id': None
            }
        }, {
            'event_type': 'edx.team.searched',
            'event': {
                'search_text': search_text,
                'topic_id': self.topic['id'],
                'number_of_results': 0
            }
        }]
        with self.assert_events_match_during(self.only_team_events, expected_events=events, in_order=False):
            search_results_page = self.browse_teams_page.search(search_text)
        self.verify_search_header(search_results_page, search_text)
        self.assertTrue(search_results_page.get_pagination_header_text().startswith('Showing 0 out of 0 total'))

    def test_page_viewed_event(self):
        """
        Scenario: Visiting the browse page should fire a page viewed event.
        Given I am enrolled in a course with a team configuration and a topic
        When I visit the Teams page
        Then my browser should post a page viewed event for the teams page
        """
        self.create_teams(self.topic, 5)
        events = [{
            'event_type': 'edx.team.page_viewed',
            'event': {
                'page_name': 'single-topic',
                'topic_id': self.topic['id'],
                'team_id': None
            }
        }]
        with self.assert_events_match_during(self.only_team_events, expected_events=events):
            self.browse_teams_page.visit()

    def test_team_name_xss(self):
        """
        Scenario: Team names should be HTML-escaped on the teams page
        Given I am enrolled in a course with teams enabled
        When I visit the Teams page for a topic, with a team name containing JS code
        Then I should not see any alerts
        """
        self.post_team_data({
            'course_id': self.course_id,
            'topic_id': self.topic['id'],
            'name': '<script>alert("XSS")</script>',
            'description': 'Description',
            'language': 'aa',
            'country': 'AF'
        })
        with self.assertRaises(TimeoutException):
            self.browser.get(self.browse_teams_page.url)
            alert = get_modal_alert(self.browser)
            alert.accept()


@attr('shard_5')
class TeamFormActions(TeamsTabBase):
    """
    Base class for create, edit, and delete team.
    """
    TEAM_DESCRIPTION = 'The Avengers are a fictional team of superheroes.'

    topic = {'name': 'Example Topic', 'id': 'example_topic', 'description': 'Description'}
    TEAMS_NAME = 'Avengers'

    def setUp(self):
        super(TeamFormActions, self).setUp()
        self.team_management_page = TeamManagementPage(self.browser, self.course_id, self.topic)

    def verify_page_header(self, title, description, breadcrumbs):
        """
        Verify that the page header correctly reflects the
        create team header, description and breadcrumb.
        """
        self.assertEqual(self.team_management_page.header_page_name, title)
        self.assertEqual(self.team_management_page.header_page_description, description)
        self.assertEqual(self.team_management_page.header_page_breadcrumbs, breadcrumbs)

    def verify_and_navigate_to_create_team_page(self):
        """Navigates to the create team page and verifies."""
        self.browse_teams_page.click_create_team_link()
        self.verify_page_header(
            title='Create a New Team',
            description='Create a new team if you can\'t find an existing team to join, '
                        'or if you would like to learn with friends you know.',
            breadcrumbs='All Topics {topic_name}'.format(topic_name=self.topic['name'])
        )

    def verify_and_navigate_to_edit_team_page(self):
        """Navigates to the edit team page and verifies."""
        # pylint: disable=no-member
        self.assertEqual(self.team_page.team_name, self.team['name'])
        self.assertTrue(self.team_page.edit_team_button_present)

        self.team_page.click_edit_team_button()

        self.team_management_page.wait_for_page()

        # Edit page header.
        self.verify_page_header(
            title='Edit Team',
            description='If you make significant changes, make sure you notify '
                        'members of the team before making these changes.',
            breadcrumbs='All Topics {topic_name} {team_name}'.format(
                topic_name=self.topic['name'],
                team_name=self.team['name']
            )
        )

    def verify_team_info(self, name, description, location, language):
        """Verify the team information on team page."""
        # pylint: disable=no-member
        self.assertEqual(self.team_page.team_name, name)
        self.assertEqual(self.team_page.team_description, description)
        self.assertEqual(self.team_page.team_location, location)
        self.assertEqual(self.team_page.team_language, language)

    def fill_create_or_edit_form(self):
        """Fill the create/edit team form fields with appropriate values."""
        self.team_management_page.value_for_text_field(
            field_id='name',
            value=self.TEAMS_NAME,
            press_enter=False
        )
        self.team_management_page.set_value_for_textarea_field(
            field_id='description',
            value=self.TEAM_DESCRIPTION
        )
        self.team_management_page.value_for_dropdown_field(field_id='language', value='English')
        self.team_management_page.value_for_dropdown_field(field_id='country', value='Pakistan')

    def verify_all_fields_exist(self):
        """
        Verify the fields for create/edit page.
        """
        self.assertEqual(
            self.team_management_page.message_for_field('name'),
            'A name that identifies your team (maximum 255 characters).'
        )
        self.assertEqual(
            self.team_management_page.message_for_textarea_field('description'),
            'A short description of the team to help other learners understand '
            'the goals or direction of the team (maximum 300 characters).'
        )
        self.assertEqual(
            self.team_management_page.message_for_field('country'),
            'The country that team members primarily identify with.'
        )
        self.assertEqual(
            self.team_management_page.message_for_field('language'),
            'The language that team members primarily use to communicate with each other.'
        )


@ddt.ddt
class CreateTeamTest(TeamFormActions):
    """
    Tests for creating a new Team within a Topic on the Teams page.
    """

    def setUp(self):
        super(CreateTeamTest, self).setUp()
        self.set_team_configuration({'course_id': self.course_id, 'max_team_size': 10, 'topics': [self.topic]})

        self.browse_teams_page = BrowseTeamsPage(self.browser, self.course_id, self.topic)
        self.browse_teams_page.visit()

    def test_user_can_see_create_team_page(self):
        """
        Scenario: The user should be able to see the create team page via teams list page.
        Given I am enrolled in a course with a team configuration and a topic
        When I visit the Teams page for that topic
        Then I should see the Create Team page link on bottom
        And When I click create team link
        Then I should see the create team page.
        And I should see the create team header
        And I should also see the help messages for fields.
        """
        self.verify_and_navigate_to_create_team_page()
        self.verify_all_fields_exist()

    def test_user_can_see_error_message_for_missing_data(self):
        """
        Scenario: The user should be able to see error message in case of missing required field.
        Given I am enrolled in a course with a team configuration and a topic
        When I visit the Create Team page for that topic
        Then I should see the Create Team header and form
        And When I click create team button without filling required fields
        Then I should see the error message and highlighted fields.
        """
        self.verify_and_navigate_to_create_team_page()
        self.team_management_page.submit_form()

        self.assertEqual(
            self.team_management_page.validation_message_text,
            'Check the highlighted fields below and try again.'
        )
        self.assertTrue(self.team_management_page.error_for_field(field_id='name'))
        self.assertTrue(self.team_management_page.error_for_field(field_id='description'))

    def test_user_can_see_error_message_for_incorrect_data(self):
        """
        Scenario: The user should be able to see error message in case of increasing length for required fields.
        Given I am enrolled in a course with a team configuration and a topic
        When I visit the Create Team page for that topic
        Then I should see the Create Team header and form
        When I add text > than 255 characters for name field
        And I click Create button
        Then I should see the error message for exceeding length.
        """
        self.verify_and_navigate_to_create_team_page()

        # Fill the name field with >255 characters to see validation message.
        self.team_management_page.value_for_text_field(
            field_id='name',
            value='EdX is a massive open online course (MOOC) provider and online learning platform. '
                  'It hosts online university-level courses in a wide range of disciplines to a worldwide '
                  'audience, some at no charge. It also conducts research into learning based on how '
                  'people use its platform. EdX was created for students and institutions that seek to'
                  'transform themselves through cutting-edge technologies, innovative pedagogy, and '
                  'rigorous courses. More than 70 schools, nonprofits, corporations, and international'
                  'organizations offer or plan to offer courses on the edX website. As of 22 October 2014,'
                  'edX has more than 4 million users taking more than 500 courses online.',
            press_enter=False
        )
        self.team_management_page.submit_form()

        self.assertEqual(
            self.team_management_page.validation_message_text,
            'Check the highlighted fields below and try again.'
        )
        self.assertTrue(self.team_management_page.error_for_field(field_id='name'))

    def test_user_can_create_new_team_successfully(self):
        """
        Scenario: The user should be able to create new team.
        Given I am enrolled in a course with a team configuration and a topic
        When I visit the Create Team page for that topic
        Then I should see the Create Team header and form
        When I fill all the fields present with appropriate data
        And I click Create button
        Then I expect analytics events to be emitted
        And I should see the page for my team
        And I should see the message that says "You are member of this team"
        And the new team should be added to the list of teams within the topic
        And the number of teams should be updated on the topic card
        And if I switch to "My Team", the newly created team is displayed
        """
        AutoAuthPage(self.browser, course_id=self.course_id).visit()
        self.browse_teams_page.visit()

        self.verify_and_navigate_to_create_team_page()

        self.fill_create_or_edit_form()

        expected_events = [
            {
                'event_type': 'edx.team.created'
            },
            {
                'event_type': 'edx.team.learner_added',
                'event': {
                    'add_method': 'added_on_create',
                }
            }
        ]
        with self.assert_events_match_during(event_filter=self.only_team_events, expected_events=expected_events):
            self.team_management_page.submit_form()

        # Verify that the page is shown for the new team
        team_page = TeamPage(self.browser, self.course_id)
        team_page.wait_for_page()
        self.assertEqual(team_page.team_name, self.TEAMS_NAME)
        self.assertEqual(team_page.team_description, self.TEAM_DESCRIPTION)
        self.assertEqual(team_page.team_user_membership_text, 'You are a member of this team.')

        # Verify the new team was added to the topic list
        self.teams_page.click_specific_topic("Example Topic")
        self.teams_page.verify_topic_team_count(1)

        self.teams_page.click_all_topics()
        self.teams_page.verify_team_count_in_first_topic(1)

        # Verify that if one switches to "My Team" without reloading the page, the newly created team is shown.
        self.verify_my_team_count(1)

    def test_user_can_cancel_the_team_creation(self):
        """
        Scenario: The user should be able to cancel the creation of new team.
        Given I am enrolled in a course with a team configuration and a topic
        When I visit the Create Team page for that topic
        Then I should see the Create Team header and form
        When I click Cancel button
        Then I should see teams list page without any new team.
        And if I switch to "My Team", it shows no teams
        """
        self.assertTrue(self.browse_teams_page.get_pagination_header_text().startswith('Showing 0 out of 0 total'))

        self.verify_and_navigate_to_create_team_page()
        self.team_management_page.cancel_team()

        self.assertTrue(self.browse_teams_page.is_browser_on_page())
        self.assertTrue(self.browse_teams_page.get_pagination_header_text().startswith('Showing 0 out of 0 total'))

        self.teams_page.click_all_topics()
        self.teams_page.verify_team_count_in_first_topic(0)

        self.verify_my_team_count(0)

    def test_page_viewed_event(self):
        """
        Scenario: Visiting the create team page should fire a page viewed event.
        Given I am enrolled in a course with a team configuration and a topic
        When I visit the create team page
        Then my browser should post a page viewed event
        """
        events = [{
            'event_type': 'edx.team.page_viewed',
            'event': {
                'page_name': 'new-team',
                'topic_id': self.topic['id'],
                'team_id': None
            }
        }]
        with self.assert_events_match_during(self.only_team_events, expected_events=events):
            self.verify_and_navigate_to_create_team_page()


@ddt.ddt
class DeleteTeamTest(TeamFormActions):
    """
    Tests for deleting teams.
    """

    def setUp(self):
        super(DeleteTeamTest, self).setUp()

        self.set_team_configuration(
            {'course_id': self.course_id, 'max_team_size': 10, 'topics': [self.topic]},
            global_staff=True
        )

        self.team = self.create_teams(self.topic, num_teams=1)[0]
        self.team_page = TeamPage(self.browser, self.course_id, team=self.team)

        #need to have a membership to confirm it gets deleted as well
        self.create_membership(self.user_info['username'], self.team['id'])

        self.team_page.visit()

    def test_cancel_delete(self):
        """
        Scenario: The user should be able to cancel the Delete Team dialog
        Given I am staff user for a course with a team
        When I visit the Team profile page
        Then I should see the Edit Team button
        And When I click edit team button
        Then I should see the Delete Team button
        When I click the delete team button
        And I cancel the prompt
        And I refresh the page
        Then I should still see the team
        """
        self.delete_team(cancel=True)
        self.assertTrue(self.team_management_page.is_browser_on_page())
        self.browser.refresh()
        self.team_management_page.wait_for_page()
        self.assertEqual(
            ' '.join(('All Topics', self.topic['name'], self.team['name'])),
            self.team_management_page.header_page_breadcrumbs
        )

    @ddt.data('Moderator', 'Community TA', 'Administrator', None)
    def test_delete_team(self, role):
        """
        Scenario: The user should be able to see and navigate to the delete team page.
        Given I am staff user for a course with a team
        When I visit the Team profile page
        Then I should see the Edit Team button
        And When I click edit team button
        Then I should see the Delete Team button
        When I click the delete team button
        And I confirm the prompt
        Then I should see the browse teams page
        And the team should not be present
        """
        # If role is None, remain logged in as global staff
        if role is not None:
            AutoAuthPage(
                self.browser,
                course_id=self.course_id,
                staff=False,
                roles=role
            ).visit()
        self.team_page.visit()
        self.delete_team(require_notification=False)
        browse_teams_page = BrowseTeamsPage(self.browser, self.course_id, self.topic)
        self.assertTrue(browse_teams_page.is_browser_on_page())
        self.assertNotIn(self.team['name'], browse_teams_page.team_names)

    def delete_team(self, **kwargs):
        """
        Delete a team. Passes `kwargs` to `confirm_prompt`.
        Expects edx.team.deleted event to be emitted, with correct course_id.
        Also expects edx.team.learner_removed event to be emitted for the
        membership that is removed as a part of the delete operation.
        """

        self.team_page.click_edit_team_button()
        self.team_management_page.wait_for_page()
        self.team_management_page.delete_team_button.click()

        if 'cancel' in kwargs and kwargs['cancel'] is True:
            confirm_prompt(self.team_management_page, **kwargs)
        else:
            expected_events = [
                {
                    'event_type': 'edx.team.deleted',
                    'event': {
                        'team_id': self.team['id']
                    }
                },
                {
                    'event_type': 'edx.team.learner_removed',
                    'event': {
                        'team_id': self.team['id'],
                        'remove_method': 'team_deleted',
                        'user_id': self.user_info['user_id']
                    }
                }
            ]
            with self.assert_events_match_during(
                event_filter=self.only_team_events, expected_events=expected_events
            ):
                confirm_prompt(self.team_management_page, **kwargs)

    def test_delete_team_updates_topics(self):
        """
        Scenario: Deleting a team should update the team count on the topics page
        Given I am staff user for a course with a team
        And I delete a team
        When I navigate to the browse topics page
        Then the team count for the deletd team's topic should be updated
        """
        self.delete_team(require_notification=False)
        BrowseTeamsPage(self.browser, self.course_id, self.topic).click_all_topics()
        topics_page = BrowseTopicsPage(self.browser, self.course_id)
        self.assertTrue(topics_page.is_browser_on_page())
        self.teams_page.verify_topic_team_count(0)


@ddt.ddt
class EditTeamTest(TeamFormActions):
    """
    Tests for editing the team.
    """

    def setUp(self):
        super(EditTeamTest, self).setUp()

        self.set_team_configuration(
            {'course_id': self.course_id, 'max_team_size': 10, 'topics': [self.topic]},
            global_staff=True
        )

        self.team = self.create_teams(self.topic, num_teams=1)[0]
        self.team_page = TeamPage(self.browser, self.course_id, team=self.team)
        self.team_page.visit()

    def test_staff_can_navigate_to_edit_team_page(self):
        """
        Scenario: The user should be able to see and navigate to the edit team page.
        Given I am staff user for a course with a team
        When I visit the Team profile page
        Then I should see the Edit Team button
        And When I click edit team button
        Then I should see the edit team page
        And I should see the edit team header
        And I should also see the help messages for fields
        """
        self.verify_and_navigate_to_edit_team_page()
        self.verify_all_fields_exist()

    def test_staff_can_edit_team_successfully(self):
        """
        Scenario: The staff should be able to edit team successfully.
        Given I am staff user for a course with a team
        When I visit the Team profile page
        Then I should see the Edit Team button
        And When I click edit team button
        Then I should see the edit team page
        And an analytics event should be fired
        When I edit all the fields with appropriate data
        And I click Update button
        Then I should see the page for my team with updated data
        """
        self.verify_team_info(
            name=self.team['name'],
            description=self.team['description'],
            location='Afghanistan',
            language='Afar'
        )
        self.verify_and_navigate_to_edit_team_page()

        self.fill_create_or_edit_form()

        expected_events = [
            {
                'event_type': 'edx.team.changed',
                'event': {
                    'team_id': self.team['id'],
                    'field': 'country',
                    'old': 'AF',
                    'new': 'PK',
                    'truncated': [],
                }
            },
            {
                'event_type': 'edx.team.changed',
                'event': {
                    'team_id': self.team['id'],
                    'field': 'name',
                    'old': self.team['name'],
                    'new': self.TEAMS_NAME,
                    'truncated': [],
                }
            },
            {
                'event_type': 'edx.team.changed',
                'event': {
                    'team_id': self.team['id'],
                    'field': 'language',
                    'old': 'aa',
                    'new': 'en',
                    'truncated': [],
                }
            },
            {
                'event_type': 'edx.team.changed',
                'event': {
                    'team_id': self.team['id'],
                    'field': 'description',
                    'old': self.team['description'],
                    'new': self.TEAM_DESCRIPTION,
                    'truncated': [],
                }
            },
        ]
        with self.assert_events_match_during(
            event_filter=self.only_team_events,
            expected_events=expected_events,
        ):
            self.team_management_page.submit_form()

        self.team_page.wait_for_page()

        self.verify_team_info(
            name=self.TEAMS_NAME,
            description=self.TEAM_DESCRIPTION,
            location='Pakistan',
            language='English'
        )

    def test_staff_can_cancel_the_team_edit(self):
        """
        Scenario: The user should be able to cancel the editing of team.
        Given I am staff user for a course with a team
        When I visit the Team profile page
        Then I should see the Edit Team button
        And When I click edit team button
        Then I should see the edit team page
        Then I should see the Edit Team header
        When I click Cancel button
        Then I should see team page page without changes.
        """
        self.verify_team_info(
            name=self.team['name'],
            description=self.team['description'],
            location='Afghanistan',
            language='Afar'
        )

        self.verify_and_navigate_to_edit_team_page()

        self.fill_create_or_edit_form()
        self.team_management_page.cancel_team()

        self.team_page.wait_for_page()

        self.verify_team_info(
            name=self.team['name'],
            description=self.team['description'],
            location='Afghanistan',
            language='Afar'
        )

    def test_student_cannot_see_edit_button(self):
        """
        Scenario: The student should not see the edit team button.
        Given I am student for a course with a team
        When I visit the Team profile page
        Then I should not see the Edit Team button
        """
        AutoAuthPage(self.browser, course_id=self.course_id).visit()
        self.team_page.visit()
        self.assertFalse(self.team_page.edit_team_button_present)

    @ddt.data('Moderator', 'Community TA', 'Administrator')
    def test_discussion_privileged_user_can_edit_team(self, role):
        """
        Scenario: The user with specified role should see the edit team button.
        Given I am user with privileged role for a course with a team
        When I visit the Team profile page
        Then I should see the Edit Team button
        """
        kwargs = {
            'course_id': self.course_id,
            'staff': False
        }
        if role is not None:
            kwargs['roles'] = role

        AutoAuthPage(self.browser, **kwargs).visit()

        self.team_page.visit()
        self.teams_page.wait_for_page()
        self.assertTrue(self.team_page.edit_team_button_present)

        self.verify_team_info(
            name=self.team['name'],
            description=self.team['description'],
            location='Afghanistan',
            language='Afar'
        )
        self.verify_and_navigate_to_edit_team_page()

        self.fill_create_or_edit_form()
        self.team_management_page.submit_form()

        self.team_page.wait_for_page()

        self.verify_team_info(
            name=self.TEAMS_NAME,
            description=self.TEAM_DESCRIPTION,
            location='Pakistan',
            language='English'
        )

    def test_page_viewed_event(self):
        """
        Scenario: Visiting the edit team page should fire a page viewed event.
        Given I am enrolled in a course with a team configuration and a topic
        When I visit the edit team page
        Then my browser should post a page viewed event
        """
        events = [{
            'event_type': 'edx.team.page_viewed',
            'event': {
                'page_name': 'edit-team',
                'topic_id': self.topic['id'],
                'team_id': self.team['id']
            }
        }]
        with self.assert_events_match_during(self.only_team_events, expected_events=events):
            self.verify_and_navigate_to_edit_team_page()


@ddt.ddt
class EditMembershipTest(TeamFormActions):
    """
    Tests for administrating from the team membership page
    """

    def setUp(self):
        super(EditMembershipTest, self).setUp()

        self.set_team_configuration(
            {'course_id': self.course_id, 'max_team_size': 10, 'topics': [self.topic]},
            global_staff=True
        )
        self.team_management_page = TeamManagementPage(self.browser, self.course_id, self.topic)
        self.team = self.create_teams(self.topic, num_teams=1)[0]

        #make sure a user exists on this team so we can edit the membership
        self.create_membership(self.user_info['username'], self.team['id'])

        self.edit_membership_page = EditMembershipPage(self.browser, self.course_id, self.team)
        self.team_page = TeamPage(self.browser, self.course_id, team=self.team)

    def edit_membership_helper(self, role, cancel=False):
        """
        Helper for common functionality in edit membership tests.
        Checks for all relevant assertions about membership being removed,
        including verify edx.team.learner_removed events are emitted.
        """
        if role is not None:
            AutoAuthPage(
                self.browser,
                course_id=self.course_id,
                staff=False,
                roles=role
            ).visit()

        self.team_page.visit()
        self.team_page.click_edit_team_button()
        self.team_management_page.wait_for_page()

        self.assertTrue(
            self.team_management_page.membership_button_present
        )

        self.team_management_page.click_membership_button()
        self.edit_membership_page.wait_for_page()
        self.edit_membership_page.click_first_remove()
        if cancel:
            self.edit_membership_page.cancel_delete_membership_dialog()
            self.assertEqual(self.edit_membership_page.team_members, 1)
        else:
            expected_events = [
                {
                    'event_type': 'edx.team.learner_removed',
                    'event': {
                        'team_id': self.team['id'],
                        'remove_method': 'removed_by_admin',
                        'user_id': self.user_info['user_id']
                    }
                }
            ]
            with self.assert_events_match_during(
                event_filter=self.only_team_events, expected_events=expected_events
            ):
                self.edit_membership_page.confirm_delete_membership_dialog()
            self.assertEqual(self.edit_membership_page.team_members, 0)
        self.assertTrue(self.edit_membership_page.is_browser_on_page)

    @ddt.data('Moderator', 'Community TA', 'Administrator', None)
    def test_remove_membership(self, role):
        """
        Scenario: The user should be able to remove a membership
        Given I am staff user for a course with a team
        When I visit the Team profile page
        Then I should see the Edit Team button
        And When I click edit team button
        Then I should see the Edit Membership button
        And When I click the edit membership button
        Then I should see the edit membership page
        And When I click the remove button and confirm the dialog
        Then my membership should be removed, and I should remain on the page
        """
        self.edit_membership_helper(role, cancel=False)

    @ddt.data('Moderator', 'Community TA', 'Administrator', None)
    def test_cancel_remove_membership(self, role):
        """
        Scenario: The user should be able to remove a membership
        Given I am staff user for a course with a team
        When I visit the Team profile page
        Then I should see the Edit Team button
        And When I click edit team button
        Then I should see the Edit Membership button
        And When I click the edit membership button
        Then I should see the edit membership page
        And When I click the remove button and cancel the dialog
        Then my membership should not be removed, and I should remain on the page
        """
        self.edit_membership_helper(role, cancel=True)


@attr('shard_5')
@ddt.ddt
class TeamPageTest(TeamsTabBase):
    """Tests for viewing a specific team"""

    SEND_INVITE_TEXT = 'Send this link to friends so that they can join too.'

    def setUp(self):
        super(TeamPageTest, self).setUp()
        self.topic = {u"name": u"Example Topic", u"id": "example_topic", u"description": "Description"}

    def _set_team_configuration_and_membership(
            self,
            max_team_size=10,
            membership_team_index=0,
            visit_team_index=0,
            create_membership=True,
            another_user=False):
        """
        Set team configuration.

        Arguments:
            max_team_size (int): number of users a team can have
            membership_team_index (int): index of team user will join
            visit_team_index (int): index of team user will visit
            create_membership (bool): whether to create membership or not
            another_user (bool): another user to visit a team
        """
        #pylint: disable=attribute-defined-outside-init
        self.set_team_configuration(
            {'course_id': self.course_id, 'max_team_size': max_team_size, 'topics': [self.topic]}
        )
        self.teams = self.create_teams(self.topic, 2)

        if create_membership:
            self.create_membership(self.user_info['username'], self.teams[membership_team_index]['id'])

        if another_user:
            AutoAuthPage(self.browser, course_id=self.course_id).visit()

        self.team_page = TeamPage(self.browser, self.course_id, self.teams[visit_team_index])

    def setup_thread(self):
        """
        Create and return a thread for this test's discussion topic.
        """
        thread = Thread(
            id="test_thread_{}".format(uuid4().hex),
            commentable_id=self.teams[0]['discussion_topic_id'],
            body="Dummy text body."
        )
        thread_fixture = MultipleThreadFixture([thread])
        thread_fixture.push()
        return thread

    def setup_discussion_user(self, role=None, staff=False):
        """Set this test's user to have the given role in its
        discussions. Role is one of 'Community TA', 'Moderator',
        'Administrator', or 'Student'.
        """
        kwargs = {
            'course_id': self.course_id,
            'staff': staff
        }
        if role is not None:
            kwargs['roles'] = role
        #pylint: disable=attribute-defined-outside-init
        self.user_info = AutoAuthPage(self.browser, **kwargs).visit().user_info

    def verify_teams_discussion_permissions(self, should_have_permission):
        """Verify that the teams discussion component is in the correct state
        for the test user. If `should_have_permission` is True, assert that
        the user can see controls for posting replies, voting, editing, and
        deleting. Otherwise, assert that those controls are hidden.
        """
        thread = self.setup_thread()
        self.team_page.visit()
        self.assertEqual(self.team_page.discussion_id, self.teams[0]['discussion_topic_id'])
        discussion = self.team_page.discussion_page
        self.assertTrue(discussion.is_browser_on_page())
        self.assertTrue(discussion.is_discussion_expanded())
        self.assertEqual(discussion.get_num_displayed_threads(), 1)
        self.assertTrue(discussion.has_thread(thread['id']))
        assertion = self.assertTrue if should_have_permission else self.assertFalse
        assertion(discussion.q(css='.post-header-actions').present)
        assertion(discussion.q(css='.add-response').present)
        assertion(discussion.q(css='.new-post-btn').present)

    def test_discussion_on_my_team_page(self):
        """
        Scenario: Team Page renders a discussion for a team to which I belong.
        Given I am enrolled in a course with a team configuration, a topic,
            and a team belonging to that topic of which I am a member
        When the team has a discussion with a thread
        And I visit the Team page for that team
        Then I should see a discussion with the correct discussion_id
        And I should see the existing thread
        And I should see controls to change the state of the discussion
        """
        self._set_team_configuration_and_membership()
        self.verify_teams_discussion_permissions(True)

    @ddt.data(True, False)
    def test_discussion_on_other_team_page(self, is_staff):
        """
        Scenario: Team Page renders a team discussion for a team to which I do
            not belong.
        Given I am enrolled in a course with a team configuration, a topic,
            and a team belonging to that topic of which I am not a member
        When the team has a discussion with a thread
        And I visit the Team page for that team
        Then I should see a discussion with the correct discussion_id
        And I should see the team's thread
        And I should not see controls to change the state of the discussion
        """
        self._set_team_configuration_and_membership(create_membership=False)
        self.setup_discussion_user(staff=is_staff)
        self.verify_teams_discussion_permissions(False)

    @ddt.data('Moderator', 'Community TA', 'Administrator')
    def test_discussion_privileged(self, role):
        self._set_team_configuration_and_membership(create_membership=False)
        self.setup_discussion_user(role=role)
        self.verify_teams_discussion_permissions(True)

    def assert_team_details(self, num_members, is_member=True, max_size=10):
        """
        Verifies that user can see all the information, present on detail page according to their membership status.

        Arguments:
            num_members (int): number of users in a team
            is_member (bool) default True: True if request user is member else False
            max_size (int): number of users a team can have
        """
        self.assertEqual(
            self.team_page.team_capacity_text,
            self.team_page.format_capacity_text(num_members, max_size)
        )
        self.assertEqual(self.team_page.team_location, 'Afghanistan')
        self.assertEqual(self.team_page.team_language, 'Afar')
        self.assertEqual(self.team_page.team_members, num_members)

        if num_members > 0:
            self.assertTrue(self.team_page.team_members_present)
        else:
            self.assertFalse(self.team_page.team_members_present)

        if is_member:
            self.assertEqual(self.team_page.team_user_membership_text, 'You are a member of this team.')
            self.assertTrue(self.team_page.team_leave_link_present)
            self.assertTrue(self.team_page.new_post_button_present)
        else:
            self.assertEqual(self.team_page.team_user_membership_text, '')
            self.assertFalse(self.team_page.team_leave_link_present)
            self.assertFalse(self.team_page.new_post_button_present)

    def test_team_member_can_see_full_team_details(self):
        """
        Scenario: Team member can see full info for team.
        Given I am enrolled in a course with a team configuration, a topic,
            and a team belonging to that topic of which I am a member
        When I visit the Team page for that team
        Then I should see the full team detail
        And I should see the team members
        And I should see my team membership text
        And I should see the language & country
        And I should see the Leave Team and Invite Team
        """
        self._set_team_configuration_and_membership()
        self.team_page.visit()

        self.assert_team_details(
            num_members=1,
        )

    def test_other_users_can_see_limited_team_details(self):
        """
        Scenario: Users who are not member of this team can only see limited info for this team.
        Given I am enrolled in a course with a team configuration, a topic,
            and a team belonging to that topic of which I am not a member
        When I visit the Team page for that team
        Then I should not see full team detail
        And I should see the team members
        And I should not see my team membership text
        And I should not see the Leave Team and Invite Team links
        """
        self._set_team_configuration_and_membership(create_membership=False)
        self.team_page.visit()

        self.assert_team_details(is_member=False, num_members=0)

    def test_user_can_navigate_to_members_profile_page(self):
        """
        Scenario: User can navigate to profile page via team member profile image.
        Given I am enrolled in a course with a team configuration, a topic,
            and a team belonging to that topic of which I am a member
        When I visit the Team page for that team
        Then I should see profile images for the team members
        When I click on the first profile image
        Then I should be taken to the user's profile page
        And I should see the username on profile page
        """
        self._set_team_configuration_and_membership()
        self.team_page.visit()

        learner_name = self.team_page.first_member_username

        self.team_page.click_first_profile_image()

        learner_profile_page = LearnerProfilePage(self.browser, learner_name)
        learner_profile_page.wait_for_page()
        learner_profile_page.wait_for_field('username')
        self.assertTrue(learner_profile_page.field_is_visible('username'))

    def test_join_team(self):
        """
        Scenario: User can join a Team if not a member already..

        Given I am enrolled in a course with a team configuration, a topic,
            and a team belonging to that topic
        And I visit the Team page for that team
        Then I should see Join Team button
        And I should not see New Post button
        When I click on Join Team button
        Then there should be no Join Team button and no message
        And an analytics event should be emitted
        And I should see the updated information under Team Details
        And I should see New Post button
        And if I switch to "My Team", the team I have joined is displayed
        """
        self._set_team_configuration_and_membership(create_membership=False)
        teams_page = BrowseTeamsPage(self.browser, self.course_id, self.topic)
        teams_page.visit()
        teams_page.view_first_team()
        self.assertTrue(self.team_page.join_team_button_present)
        expected_events = [
            {
                'event_type': 'edx.team.learner_added',
                'event': {
                    'add_method': 'joined_from_team_view'
                }
            }
        ]
        with self.assert_events_match_during(event_filter=self.only_team_events, expected_events=expected_events):
            self.team_page.click_join_team_button()
        self.assertFalse(self.team_page.join_team_button_present)
        self.assertFalse(self.team_page.join_team_message_present)
        self.assert_team_details(num_members=1, is_member=True)

        # Verify that if one switches to "My Team" without reloading the page, the newly joined team is shown.
        self.teams_page.click_all_topics()
        self.verify_my_team_count(1)

    def test_already_member_message(self):
        """
        Scenario: User should see `You are already in a team` if user is a
            member of other team.

        Given I am enrolled in a course with a team configuration, a topic,
            and a team belonging to that topic
        And I am already a member of a team
        And I visit a team other than mine
        Then I should see `You are already in a team` message
        """
        self._set_team_configuration_and_membership(membership_team_index=0, visit_team_index=1)
        self.team_page.visit()
        self.assertEqual(self.team_page.join_team_message, 'You already belong to another team.')
        self.assert_team_details(num_members=0, is_member=False)

    def test_team_full_message(self):
        """
        Scenario: User should see `Team is full` message when team is full.

        Given I am enrolled in a course with a team configuration, a topic,
            and a team belonging to that topic
        And team has no space left
        And I am not a member of any team
        And I visit the team
        Then I should see `Team is full` message
        """
        self._set_team_configuration_and_membership(
            create_membership=True,
            max_team_size=1,
            membership_team_index=0,
            visit_team_index=0,
            another_user=True
        )
        self.team_page.visit()
        self.assertEqual(self.team_page.join_team_message, 'This team is full.')
        self.assert_team_details(num_members=1, is_member=False, max_size=1)

    def test_leave_team(self):
        """
        Scenario: User can leave a team.

        Given I am enrolled in a course with a team configuration, a topic,
            and a team belonging to that topic
        And I am a member of team
        And I visit the team
        And I should not see Join Team button
        And I should see New Post button
        Then I should see Leave Team link
        When I click on Leave Team link
        Then user should be removed from team
        And an analytics event should be emitted
        And I should see Join Team button
        And I should not see New Post button
        And if I switch to "My Team", the team I have left is not displayed
        """
        self._set_team_configuration_and_membership()
        self.team_page.visit()
        self.assertFalse(self.team_page.join_team_button_present)
        self.assert_team_details(num_members=1)
        expected_events = [
            {
                'event_type': 'edx.team.learner_removed',
                'event': {
                    'remove_method': 'self_removal'
                }
            }
        ]
        with self.assert_events_match_during(event_filter=self.only_team_events, expected_events=expected_events):
            self.team_page.click_leave_team_link()
        self.assert_team_details(num_members=0, is_member=False)
        self.assertTrue(self.team_page.join_team_button_present)

        # Verify that if one switches to "My Team" without reloading the page, the old team no longer shows.
        self.teams_page.click_all_topics()
        self.verify_my_team_count(0)

    def test_page_viewed_event(self):
        """
        Scenario: Visiting the team profile page should fire a page viewed event.
        Given I am enrolled in a course with a team configuration and a topic
        When I visit the team profile page
        Then my browser should post a page viewed event
        """
        self._set_team_configuration_and_membership()
        events = [{
            'event_type': 'edx.team.page_viewed',
            'event': {
                'page_name': 'single-team',
                'topic_id': self.topic['id'],
                'team_id': self.teams[0]['id']
            }
        }]
        with self.assert_events_match_during(self.only_team_events, expected_events=events):
            self.team_page.visit()
