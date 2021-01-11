# -*- coding: utf-8 -*-
"""
End-to-end tests for the LMS.
"""


from common.test.acceptance.fixtures.course import CourseFixture
from common.test.acceptance.pages.common.auto_auth import AutoAuthPage
from common.test.acceptance.pages.lms.course_home import CourseHomePage
from common.test.acceptance.pages.lms.course_wiki import (
    CourseWikiChildrenPage,
    CourseWikiEditPage,
    CourseWikiHistoryPage,
    CourseWikiPage
)
from common.test.acceptance.pages.lms.tab_nav import TabNavPage
from common.test.acceptance.tests.helpers import (
    UniqueCourseTest,
)
from openedx.core.lib.tests import attr


@attr('a11y')
class CourseWikiA11yTest(UniqueCourseTest):
    """
    Tests that verify the course wiki.
    """

    def setUp(self):
        """
        Initialize pages and install a course fixture.
        """
        super(CourseWikiA11yTest, self).setUp()

        # self.course_info['number'] must be shorter since we are accessing the wiki. See TNL-1751
        self.course_info['number'] = self.unique_id[0:6]

        self.course_wiki_page = CourseWikiPage(self.browser, self.course_id)
        self.course_home_page = CourseHomePage(self.browser, self.course_id)
        self.course_wiki_edit_page = CourseWikiEditPage(self.browser, self.course_id, self.course_info)
        self.tab_nav = TabNavPage(self.browser)

        CourseFixture(
            self.course_info['org'], self.course_info['number'],
            self.course_info['run'], self.course_info['display_name']
        ).install()

        # Auto-auth register for the course
        AutoAuthPage(self.browser, course_id=self.course_id).visit()

        # Access course wiki page
        self.course_home_page.visit()
        self.tab_nav.go_to_tab('Wiki')

    def _open_editor(self):
        self.course_wiki_page.open_editor()
        self.course_wiki_edit_page.wait_for_page()

    def test_view(self):
        """
        Verify the basic accessibility of the wiki page as initially displayed.
        """
        self.course_wiki_page.a11y_audit.config.set_rules({
            "ignore": [
                'aria-valid-attr',  # TODO: LEARNER-6611 & LEARNER-6865
                'region',  # TODO: AC-932
            ]
        })
        self.course_wiki_page.a11y_audit.check_for_accessibility_errors()

    def test_edit(self):
        """
        Verify the basic accessibility of edit wiki page.
        """
        self._open_editor()
        self.course_wiki_edit_page.a11y_audit.config.set_rules({
            "ignore": [
                'aria-valid-attr',  # TODO: LEARNER-6611 & LEARNER-6865
                'region',  # TODO: AC-932
            ]
        })
        self.course_wiki_edit_page.a11y_audit.check_for_accessibility_errors()

    def test_changes(self):
        """
        Verify the basic accessibility of changes wiki page.
        """
        self.course_wiki_page.show_history()
        history_page = CourseWikiHistoryPage(self.browser, self.course_id, self.course_info)
        history_page.a11y_audit.config.set_rules({
            "ignore": [
                'aria-valid-attr',  # TODO: LEARNER-6611 & LEARNER-6865
                'region',  # TODO: AC-932
            ]
        })
        history_page.wait_for_page()
        history_page.a11y_audit.check_for_accessibility_errors()

    def test_children(self):
        """
        Verify the basic accessibility of changes wiki page.
        """
        self.course_wiki_page.show_children()
        children_page = CourseWikiChildrenPage(self.browser, self.course_id, self.course_info)
        children_page.a11y_audit.config.set_rules({
            "ignore": [
                'aria-valid-attr',  # TODO: LEARNER-6611 & LEARNER-6865
                'region',  # TODO: AC-932
            ]
        })
        children_page.wait_for_page()
        children_page.a11y_audit.check_for_accessibility_errors()
