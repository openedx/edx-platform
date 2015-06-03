"""
Acceptance tests for the teams feature.
"""
from ..helpers import UniqueCourseTest
from ...pages.lms.teams import TeamsPage
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
        self.test_topic = {u"name": u"a topic", u"description": u"test topic", u"id": 0}

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
        self.set_team_configuration({u"max_team_size": 10, u"topics": [self.test_topic]}, enroll_in_course=False)
        self.verify_teams_present(False)

    def test_teams_enabled(self):
        """
        Scenario: teams tab should be present if user is enrolled in the course and it has team configuration
        Given I am enrolled in a course with team configuration and topics
        When I view the course info page
        Then I should see the Teams tab
        And the correct content should be on the page
        """
        self.set_team_configuration({u"max_team_size": 10, u"topics": [self.test_topic]})
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
            {u"max_team_size": 10, u"topics": [self.test_topic]}, enroll_in_course=False, global_staff=True
        )
        self.verify_teams_present(True)
