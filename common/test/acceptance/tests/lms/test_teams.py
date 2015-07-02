"""
Acceptance tests for the teams feature.
"""
from ..helpers import UniqueCourseTest
from ...pages.lms.teams import TeamsPage, BrowseTopicsPage
from nose.plugins.attrib import attr
from ...fixtures.course import CourseFixture
from ...pages.lms.tab_nav import TabNavPage
from ...pages.lms.auto_auth import AutoAuthPage
from ...pages.lms.course_info import CourseInfoPage


@attr('shard_5')
class TeamsTabTest(UniqueCourseTest):
    """
    Tests verifying when the Teams tab is present.
    """

    def setUp(self):
        super(TeamsTabTest, self).setUp()
        self.tab_nav = TabNavPage(self.browser)
        self.course_info_page = CourseInfoPage(self.browser, self.course_id)
        self.teams_page = TeamsPage(self.browser, self.course_id)

    def create_topics(self, num_topics):
        """Create `num_topics` test topics."""
        return [{u"description": str(i), u"name": str(i), u"id": i} for i in xrange(num_topics)]

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
        AutoAuthPage(self.browser, course_id=enroll_course_id, staff=global_staff).visit()
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
class BrowseTopicsTest(TeamsTabTest):
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
