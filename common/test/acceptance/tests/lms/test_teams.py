"""
Acceptance tests for the teams feature.
"""
import json

from nose.plugins.attrib import attr
from uuid import uuid4

from ..helpers import UniqueCourseTest
from ...pages.lms.teams import TeamsPage, BrowseTopicsPage, BrowseTeamsPage, TeamPage
from ...fixtures import LMS_BASE_URL
from ...fixtures.course import CourseFixture
from ...pages.lms.tab_nav import TabNavPage
from ...pages.lms.auto_auth import AutoAuthPage
from ...pages.lms.course_info import CourseInfoPage
from ...fixtures.discussion import (
    Thread,
    MultipleThreadFixture)


class TeamsTabBase(UniqueCourseTest):
    """Base class for Teams Tab tests"""
    def setUp(self):
        super(TeamsTabBase, self).setUp()
        self.tab_nav = TabNavPage(self.browser)
        self.course_info_page = CourseInfoPage(self.browser, self.course_id)
        self.teams_page = TeamsPage(self.browser, self.course_id)

    def create_topics(self, num_topics):
        """Create `num_topics` test topics."""
        return [{u"description": str(i), u"name": str(i), u"id": i} for i in xrange(num_topics)]

    def create_teams(self, topic, num_teams):
        """Create `num_teams` teams belonging to `topic`."""
        teams = []
        for i in xrange(num_teams):
            team = {
                'course_id': self.course_id,
                'topic_id': topic['id'],
                'name': 'Team {}'.format(i),
                'description': 'Description {}'.format(i)
            }
            response = self.course_fixture.session.post(
                LMS_BASE_URL + '/api/team/v0/teams/',
                data=json.dumps(team),
                headers=self.course_fixture.headers
            )
            teams.append(json.loads(response.text))
        return teams

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
            self.assertEqual("This is the new Teams tab.", self.teams_page.get_body_text())
        else:
            self.assertNotIn("Teams", self.tab_nav.tab_names)


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


@attr('shard_5')
class BrowseTopicsTest(TeamsTabBase):
    """
    Tests for the Browse tab of the Teams page.
    """

    def setUp(self):
        super(BrowseTopicsTest, self).setUp()
        self.topics_page = BrowseTopicsPage(self.browser, self.course_id)

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
        self.assertEqual(self.topics_page.get_pagination_header_text(), 'Showing 1-2 out of 2 total')
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
        self.assertEqual(len(self.topics_page.topic_cards), 12)
        self.assertEqual(self.topics_page.get_pagination_header_text(), 'Showing 1-12 out of 20 total')
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
        self.assertEqual(self.topics_page.get_pagination_header_text(), 'Showing 13-13 out of 13 total')
        self.topics_page.press_previous_page_button()
        self.assertEqual(len(self.topics_page.topic_cards), 12)
        self.assertEqual(self.topics_page.get_pagination_header_text(), 'Showing 1-12 out of 13 total')

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
        truncated_description = self.topics_page.topic_cards[0].text
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
        self.assertEqual(browse_teams_page.header_topic_name, 'Example Topic')
        self.assertEqual(browse_teams_page.header_topic_description, 'Description')


@attr('shard_5')
class BrowseTeamsWithinTopicTest(TeamsTabBase):
    """
    Tests for browsing Teams within a Topic on the Teams page.
    """
    TEAMS_PAGE_SIZE = 10

    def setUp(self):
        super(BrowseTeamsWithinTopicTest, self).setUp()
        self.topic = {u"name": u"Example Topic", u"id": "example_topic", u"description": "Description"}
        self.set_team_configuration({'course_id': self.course_id, 'max_team_size': 10, 'topics': [self.topic]})
        self.browse_teams_page = BrowseTeamsPage(self.browser, self.course_id, self.topic)

    def verify_page_header(self):
        """Verify that the page header correctly reflects the current topic's name and description."""
        self.assertEqual(self.browse_teams_page.header_topic_name, self.topic['name'])
        self.assertEqual(self.browse_teams_page.header_topic_description, self.topic['description'])

    def verify_teams(self, expected_teams):
        """Verify that the list of team cards on the current page match the expected teams in order."""

        def assert_team_equal(expected_team, team_card_name, team_card_description):
            """
            Helper to assert that a single team card has the expected name and
            description.
            """
            self.assertEqual(expected_team['name'], team_card_name)
            self.assertEqual(expected_team['description'], team_card_description)

        team_cards = self.browse_teams_page.team_cards
        team_card_names = [
            team_card.find_element_by_css_selector('.card-title').text
            for team_card in team_cards.results
        ]
        team_card_descriptions = [
            team_card.find_element_by_css_selector('.card-description').text
            for team_card in team_cards.results
        ]
        map(assert_team_equal, expected_teams, team_card_names, team_card_descriptions)

    def verify_on_page(self, page_num, total_teams, pagination_header_text, footer_visible):
        """
        Verify that we are on the correct team list page.

        Arguments:
            page_num (int): The one-indexed page we expect to be on
            total_teams (list): An unsorted list of all the teams for the
                current topic
            pagination_header_text (str): Text we expect to see in the
                pagination header.
            footer_visible (bool): Whether we expect to see the pagination
                footer controls.
        """
        alphabetized_teams = sorted(total_teams, key=lambda team: team['name'])
        self.assertEqual(self.browse_teams_page.get_pagination_header_text(), pagination_header_text)
        self.verify_teams(alphabetized_teams[(page_num - 1) * self.TEAMS_PAGE_SIZE:page_num * self.TEAMS_PAGE_SIZE])
        self.assertEqual(
            self.browse_teams_page.pagination_controls_visible(),
            footer_visible,
            msg='Expected paging footer to be ' + 'visible' if footer_visible else 'invisible'
        )

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
        self.assertEqual(self.browse_teams_page.get_pagination_header_text(), 'Showing 0 out of 0 total')
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
        teams = self.create_teams(self.topic, self.TEAMS_PAGE_SIZE)
        self.browse_teams_page.visit()
        self.verify_page_header()
        self.assertEqual(self.browse_teams_page.get_pagination_header_text(), 'Showing 1-10 out of 10 total')
        self.verify_teams(teams)
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
        teams = self.create_teams(self.topic, self.TEAMS_PAGE_SIZE + 1)
        self.browse_teams_page.visit()
        self.verify_page_header()
        self.verify_on_page(1, teams, 'Showing 1-10 out of 11 total', True)
        self.browse_teams_page.press_next_page_button()
        self.verify_on_page(2, teams, 'Showing 11-11 out of 11 total', True)
        self.browse_teams_page.press_previous_page_button()
        self.verify_on_page(1, teams, 'Showing 1-10 out of 11 total', True)

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
        teams = self.create_teams(self.topic, self.TEAMS_PAGE_SIZE + 10)
        self.browse_teams_page.visit()
        self.verify_page_header()
        self.verify_on_page(1, teams, 'Showing 1-10 out of 20 total', True)
        self.browse_teams_page.go_to_page(2)
        self.verify_on_page(2, teams, 'Showing 11-20 out of 20 total', True)
        self.browse_teams_page.go_to_page(1)
        self.verify_on_page(1, teams, 'Showing 1-10 out of 20 total', True)

    def test_teams_membership(self):
        """
        Scenario: Team cards correctly reflect membership of the team.
        Given I am enrolled in a course with a team configuration and a topic
            containing one team
        And I add myself to the team
        When I visit the Teams page for that topic
        Then I should see the correct page header
        And I should see the team for that topic
        And I should see that the team card shows my membership
        """
        teams = self.create_teams(self.topic, 1)
        self.browse_teams_page.visit()
        self.verify_page_header()
        self.verify_teams(teams)
        self.create_membership(self.user_info['username'], teams[0]['id'])
        self.browser.refresh()
        self.browse_teams_page.wait_for_ajax()
        self.assertEqual(
            self.browse_teams_page.team_cards[0].find_element_by_css_selector('.member-count').text,
            '1 / 10 Members'
        )


@attr('shard_5')
class TeamPageTest(TeamsTabBase):
    """Tests for viewing a specific team"""
    def setUp(self):
        super(TeamPageTest, self).setUp()
        self.topic = {u"name": u"Example Topic", u"id": "example_topic", u"description": "Description"}
        self.set_team_configuration({'course_id': self.course_id, 'max_team_size': 10, 'topics': [self.topic]})
        self.team = self.create_teams(self.topic, 1)[0]
        self.create_membership(self.user_info['username'], self.team['id'])
        self.team_page = TeamPage(self.browser, self.course_id, self.team)

    def setup_thread(self):
        """
        Set up multiple threads on the team page by passing 'thread_count'.
        """
        thread = Thread(
            id="test_thread_{}".format(uuid4().hex),
            commentable_id=self.team['discussion_topic_id'],
            body="Dummy text body."
        )
        thread_fixture = MultipleThreadFixture([thread])
        thread_fixture.push()
        return thread

    def test_discussion_on_team_page(self):
        """
        Scenario: Team Page renders a team discussion.
        Given I am enrolled in a course with a team configuration, a topic,
            and a team belonging to that topic
        When I post a thread in the team's discussion
        And I visit the Team page for that team
        Then I should see a discussion with the correct discussion_id
        And I should see the thread which I had posted
        """
        thread = self.setup_thread()
        self.team_page.visit()
        self.assertEqual(self.team_page.discussion_id, self.team['discussion_topic_id'])
        discussion = self.team_page.discussion_page
        self.assertTrue(discussion.is_browser_on_page())
        self.assertTrue(discussion.is_discussion_expanded())
        self.assertEqual(discussion.get_num_displayed_threads(), 1)
        self.assertTrue(discussion.has_thread(thread['id']))
