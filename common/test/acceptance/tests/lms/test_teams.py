"""
Acceptance tests for the teams feature.
"""
import json

import ddt
from nose.plugins.attrib import attr
from uuid import uuid4

from ..helpers import UniqueCourseTest
from ...fixtures import LMS_BASE_URL
from ...fixtures.course import CourseFixture
from ...fixtures.discussion import (
    Thread,
    MultipleThreadFixture
)
from ...pages.lms.auto_auth import AutoAuthPage
from ...pages.lms.course_info import CourseInfoPage
from ...pages.lms.learner_profile import LearnerProfilePage
from ...pages.lms.tab_nav import TabNavPage
from ...pages.lms.teams import TeamsPage, BrowseTopicsPage, BrowseTeamsPage, CreateTeamPage, TeamPage


class TeamsTabBase(UniqueCourseTest):
    """Base class for Teams Tab tests"""
    def setUp(self):
        super(TeamsTabBase, self).setUp()
        self.tab_nav = TabNavPage(self.browser)
        self.course_info_page = CourseInfoPage(self.browser, self.course_id)
        self.teams_page = TeamsPage(self.browser, self.course_id)

    def create_topics(self, num_topics):
        """Create `num_topics` test topics."""
        return [{u"description": i, u"name": i, u"id": i} for i in map(str, xrange(num_topics))]

    def create_teams(self, topic, num_teams):
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
        ('browse', 'div.topics-list'),
        ('teams', 'p.temp-tab-view'),
        ('teams/{topic_id}/{team_id}', 'div.discussion-module'),
        ('topics/{topic_id}/create-team', 'div.create-team-instructions'),
        ('topics/{topic_id}', 'div.teams-list'),
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
        self.browser.get(
            '{url}#{route}'.format(
                url=self.browser.current_url,
                route=route.format(
                    topic_id=topic['id'],
                    team_id=team['id']
                ))
        )
        self.teams_page.wait_for_ajax()
        self.assertTrue(self.teams_page.q(css=selector).present)
        self.assertTrue(self.teams_page.q(css=selector).visible)


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
        self.topics_page = BrowseTopicsPage(self.browser, self.course_id)

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

    def test_navigation_links(self):
        """
        Scenario: User should be able to navigate to "browse all teams" and "search team description" links.
        Given I am enrolled in a course with a team configuration and a topic
            containing one team
        When I visit the Teams page for that topic
        Then I should see the correct page header
        And I should see the link to "browse all team"
        And I should navigate to that link
        And I see the relevant page loaded
        And I should see the link to "search teams"
        And I should navigate to that link
        And I see the relevant page loaded
        """
        self.browse_teams_page.visit()
        self.verify_page_header()

        self.browse_teams_page.click_browse_all_teams_link()
        self.assertTrue(self.topics_page.is_browser_on_page())

        self.browse_teams_page.visit()
        self.verify_page_header()
        self.browse_teams_page.click_search_team_link()
        # TODO Add search page expectation once that implemented.


@attr('shard_5')
class CreateTeamTest(TeamsTabBase):
    """
    Tests for creating a new Team within a Topic on the Teams page.
    """

    def setUp(self):
        super(CreateTeamTest, self).setUp()
        self.topic = {'name': 'Example Topic', 'id': 'example_topic', 'description': 'Description'}
        self.set_team_configuration({'course_id': self.course_id, 'max_team_size': 10, 'topics': [self.topic]})
        self.browse_teams_page = BrowseTeamsPage(self.browser, self.course_id, self.topic)
        self.browse_teams_page.visit()
        self.create_team_page = CreateTeamPage(self.browser, self.course_id, self.topic)
        self.team_name = 'Avengers'

    def verify_page_header(self):
        """
        Verify that the page header correctly reflects the
        create team header, description and breadcrumb.
        """
        self.assertEqual(self.create_team_page.header_page_name, 'Create a New Team')
        self.assertEqual(
            self.create_team_page.header_page_description,
            'Create a new team if you can\'t find existing teams to join, '
            'or if you would like to learn with friends you know.'
        )
        self.assertEqual(self.create_team_page.header_page_breadcrumbs, self.topic['name'])

    def verify_and_navigate_to_create_team_page(self):
        """Navigates to the create team page and verifies."""
        self.browse_teams_page.click_create_team_link()
        self.verify_page_header()

    def fill_create_form(self):
        """Fill the create team form fields with appropriate values."""
        self.create_team_page.value_for_text_field(field_id='name', value=self.team_name)
        self.create_team_page.value_for_textarea_field(
            field_id='description',
            value='The Avengers are a fictional team of superheroes.'
        )
        self.create_team_page.value_for_dropdown_field(field_id='language', value='English')
        self.create_team_page.value_for_dropdown_field(field_id='country', value='Pakistan')

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
        self.assertEqual(
            self.create_team_page.message_for_field('name'),
            'A name that identifies your team (maximum 255 characters).'
        )
        self.assertEqual(
            self.create_team_page.message_for_textarea_field('description'),
            'A short description of the team to help other learners understand '
            'the goals or direction of the team (maximum 300 characters).'
        )
        self.assertEqual(
            self.create_team_page.message_for_field('country'),
            'The country that team members primarily identify with.'
        )
        self.assertEqual(
            self.create_team_page.message_for_field('language'),
            'The language that team members primarily use to communicate with each other.'
        )

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
        self.create_team_page.submit_form()

        self.assertEqual(
            self.create_team_page.validation_message_text,
            'Check the highlighted fields below and try again.'
        )
        self.assertTrue(self.create_team_page.error_for_field(field_id='name'))
        self.assertTrue(self.create_team_page.error_for_field(field_id='description'))

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
        self.create_team_page.value_for_text_field(
            field_id='name',
            value='EdX is a massive open online course (MOOC) provider and online learning platform. '
                  'It hosts online university-level courses in a wide range of disciplines to a worldwide '
                  'audience, some at no charge. It also conducts research into learning based on how '
                  'people use its platform. EdX was created for students and institutions that seek to'
                  'transform themselves through cutting-edge technologies, innovative pedagogy, and '
                  'rigorous courses. More than 70 schools, nonprofits, corporations, and international'
                  'organizations offer or plan to offer courses on the edX website. As of 22 October 2014,'
                  'edX has more than 4 million users taking more than 500 courses online.'
        )
        self.create_team_page.submit_form()

        self.assertEqual(
            self.create_team_page.validation_message_text,
            'Check the highlighted fields below and try again.'
        )
        self.assertTrue(self.create_team_page.error_for_field(field_id='name'))

    def test_user_can_create_new_team_successfully(self):
        """
        Scenario: The user should be able to create new team.
        Given I am enrolled in a course with a team configuration and a topic
        When I visit the Create Team page for that topic
        Then I should see the Create Team header and form
        When I fill all the fields present with appropriate data
        And I click Create button
        Then I should see the page for my team
        And I should see the message that says
        "You are member of this team"
        """
        self.verify_and_navigate_to_create_team_page()

        self.fill_create_form()
        self.create_team_page.submit_form()

        # Verify that the page is shown for the new team
        team_page = TeamPage(self.browser, self.course_id)
        team_page.wait_for_page()
        self.assertEqual(team_page.team_name, self.team_name)
        self.assertEqual(team_page.team_description, 'The Avengers are a fictional team of superheroes.')
        self.assertEqual(team_page.team_membership_text, 'You are a member of this team.')

    def test_user_can_cancel_the_team_creation(self):
        """
        Scenario: The user should be able to cancel the creation of new team.
        Given I am enrolled in a course with a team configuration and a topic
        When I visit the Create Team page for that topic
        Then I should see the Create Team header and form
        When I click Cancel button
        Then I should see teams list page without any new team.
        """
        self.assertEqual(self.browse_teams_page.get_pagination_header_text(), 'Showing 0 out of 0 total')

        self.verify_and_navigate_to_create_team_page()
        self.create_team_page.cancel_team()

        self.assertTrue(self.browse_teams_page.is_browser_on_page())
        self.assertEqual(self.browse_teams_page.get_pagination_header_text(), 'Showing 0 out of 0 total')


@attr('shard_5')
@ddt.ddt
class TeamPageTest(TeamsTabBase):
    """Tests for viewing a specific team"""
    def setUp(self):
        super(TeamPageTest, self).setUp()
        self.topic = {u"name": u"Example Topic", u"id": "example_topic", u"description": "Description"}

    def _team_config(
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
        self._team_config()
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
        self._team_config(create_membership=False)
        self.setup_discussion_user(staff=is_staff)
        self.verify_teams_discussion_permissions(False)

    @ddt.data('Moderator', 'Community TA', 'Administrator')
    def test_discussion_privileged(self, role):
        self._team_config(create_membership=False)
        self.setup_discussion_user(role=role)
        self.verify_teams_discussion_permissions(True)

    def assert_team_details_for_members(self, num_members, max_size=10, invite_text=''):
        """
        Verifies that team members can see all the info. present on detail page.

        Arguments:
            num_members (int): number of users in a team
            max_size (int): number of users a team can have
            invite_text (str): help text for invite link.
        """
        self.assertEqual(self.team_page.team_membership_text, 'You are a member of this team.')
        # TODO change location and language when functionality implemented.
        self.assertEqual(
            self.team_page.team_details_info, {
                'team_members_present': True if num_members else False,
                'team_capacity': '{num_members} / {max_size} {members_text}'.format(
                    num_members=num_members,
                    max_size=max_size,
                    members_text='Member' if num_members == max_size else 'Members'
                ),
                'team_location': 'AF',
                'team_language': 'aa'
            }
        )
        self.assertEqual(self.team_page.team_members, num_members)
        self.assertTrue(self.team_page.team_leave_link_present)
        self.assertTrue(self.team_page.team_invite_section_present)
        self.assertEqual(self.team_page.team_invite_help_text, invite_text)

    def assert_team_details_for_non_members(self, num_members, max_size=10):
        """
        Verifies that Non team members can see only limited info.

        Arguments:
            num_members (int): number of users in a team
        """
        self.assertEqual(self.team_page.team_membership_text, '')
        # TODO change location and language when functionality implemented.
        self.assertEqual(
            self.team_page.team_details_info, {
                'team_members_present': True if num_members else False,
                'team_capacity': '{num_members} / 10 {members_text}'.format(
                    num_members=num_members,
                    members_text='Member' if num_members == max_size else 'Members'
                ),
                'team_location': 'AF',
                'team_language': 'aa'
            }
        )
        self.assertFalse(self.team_page.team_leave_link_present)
        self.assertFalse(self.team_page.team_invite_section_present)

    def test_team_member_can_see_full_team_details(self):
        """
        Scenario: Team member can see full info for team.
        Given I am enrolled in a course with a team configuration, a topic,
            and a team belonging to that topic of which I am a member
        When I visit the Team page for that team
        Then I should see a full team detail
        And I should see the team members
        And I should see the team membership text
        And I should see the language & country
        And I should see the Leave Team and Invite Team
        """
        self._team_config()
        self.team_page.visit()

        self.assert_team_details_for_members(
            num_members=1,
            invite_text='Send this link to friends so that they can join too.'
        )

    def test_other_users_can_see_limited_team_details(self):
        """
        Scenario: Users who are not member of this team can only see limited info for this team.
        Given I am enrolled in a course with a team configuration, a topic,
            and a team belonging to that topic of which I am not a member
        When I visit the Team page for that team
        Then I should not see full team detail
        And I should see the team members
        And I should not see the team membership text
        And I should not see the Leave Team and Invite Team
        """
        self._team_config(create_membership=False)
        self.team_page.visit()

        self.assert_team_details_for_non_members(num_members=0)

    def test_user_can_navigate_to_members_profile_page(self):
        """
        Scenario: User can navigate to profile page via team member profile image.
        Given I am enrolled in a course with a team configuration, a topic,
            and a team belonging to that topic of which I am a member
        When I visit the Team page for that team
        Then I should see a profile image for team member
        When I click on profile image
        Then I should be taken to the user's profile page
        And I should see the username on profile page
        """
        self._team_config()
        self.team_page.visit()

        self.team_page.click_users_profile_image()

        learner_profile_page = LearnerProfilePage(self.browser, self.team_page.username)
        learner_profile_page.wait_for_page()
        learner_profile_page.wait_for_field('username')
        self.assertTrue(learner_profile_page.field_is_visible('username'))

    def test_team_member_cannot_see_invite_link_if_team_full(self):
        """
        Scenario: Team members should not see the invite link if the team is full.
        Given I am enrolled in a course with a team configuration, a topic,
            and a team belonging to that topic of which I am a member
        When I visit the Team page for that team
        Then I should see the "team is full" message
        And I should not see the invite link
        """
        self._team_config(max_team_size=1)
        self.team_page.visit()

        self.assert_team_details_for_members(
            num_members=1,
            max_size=1,
            invite_text='No invitations are available. This team is full.'
        )

    def test_team_member_can_see_invite_link(self):
        """
        Scenario: Team members should see the invite link if the team has capacity.
        Given I am enrolled in a course with a team configuration, a topic,
            and a team belonging to that topic of which I am a member
        When I visit the Team page for that team
        Then I should see the invite link help message
        And I should see the invite link that can be selected
        """
        self._team_config()
        self.team_page.visit()

        self.assert_team_details_for_members(
            num_members=1,
            invite_text='Send this link to friends so that they can join too.'
        )
        self.assertEqual(self.team_page.team_invite_url, '{0}?invite=true'.format(self.team_page.url))
