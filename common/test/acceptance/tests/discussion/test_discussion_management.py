# -*- coding: utf-8 -*-
"""
End-to-end tests related to the divided discussion management on the LMS Instructor Dashboard
"""

from nose.plugins.attrib import attr
from common.test.acceptance.tests.discussion.helpers import CohortTestMixin
from common.test.acceptance.tests.helpers import UniqueCourseTest
from common.test.acceptance.fixtures.course import CourseFixture, XBlockFixtureDesc
from common.test.acceptance.pages.lms.auto_auth import AutoAuthPage
from common.test.acceptance.pages.lms.instructor_dashboard import InstructorDashboardPage

import uuid


@attr(shard=6)
class DividedDiscussionTopicsTest(UniqueCourseTest, CohortTestMixin):
    """
    Tests for dividing the inline and course-wide discussion topics.
    """
    def setUp(self):
        """
        Set up a discussion topic
        """
        super(DividedDiscussionTopicsTest, self).setUp()

        self.discussion_id = "test_discussion_{}".format(uuid.uuid4().hex)
        self.course_fixture = CourseFixture(**self.course_info).add_children(
            XBlockFixtureDesc("chapter", "Test Section").add_children(
                XBlockFixtureDesc("sequential", "Test Subsection").add_children(
                    XBlockFixtureDesc("vertical", "Test Unit").add_children(
                        XBlockFixtureDesc(
                            "discussion",
                            "Test Discussion",
                            metadata={"discussion_id": self.discussion_id}
                        )
                    )
                )
            )
        ).install()

        # create course with single cohort and two content groups (user_partition of type "cohort")
        self.cohort_name = "OnlyCohort"
        self.setup_cohort_config(self.course_fixture)
        self.cohort_id = self.add_manual_cohort(self.course_fixture, self.cohort_name)

        # login as an instructor
        self.instructor_name = "instructor_user"
        self.instructor_id = AutoAuthPage(
            self.browser, username=self.instructor_name, email="instructor_user@example.com",
            course_id=self.course_id, staff=True
        ).visit().get_user_id()

        # go to the membership page on the instructor dashboard
        self.instructor_dashboard_page = InstructorDashboardPage(self.browser, self.course_id)
        self.instructor_dashboard_page.visit()
        self.discussion_management_page = self.instructor_dashboard_page.select_discussion_management()
        self.discussion_management_page.wait_for_page()

        self.course_wide_key = 'course-wide'
        self.inline_key = 'inline'

    def divided_discussion_topics_are_visible(self):
        """
        Assert that discussion topics are visible with appropriate content.
        """
        self.assertTrue(self.discussion_management_page.discussion_topics_visible())

        self.assertEqual(
            "Course-Wide Discussion Topics",
            self.discussion_management_page.divided_discussion_heading_is_visible(self.course_wide_key)
        )
        self.assertTrue(self.discussion_management_page.is_save_button_disabled(self.course_wide_key))

        self.assertEqual(
            "Content-Specific Discussion Topics",
            self.discussion_management_page.divided_discussion_heading_is_visible(self.inline_key)
        )
        self.assertTrue(self.discussion_management_page.is_save_button_disabled(self.inline_key))

    def save_and_verify_discussion_topics(self, key):
        """
        Saves the discussion topics and the verify the changes.
        """
        # click on the inline save button.
        self.discussion_management_page.save_discussion_topics(key)

        # verifies that changes saved successfully.
        confirmation_message = self.discussion_management_page.get_divide_discussions_message(key=key)
        self.assertEqual("Your changes have been saved.", confirmation_message)

        # save button disabled again.
        self.assertTrue(self.discussion_management_page.is_save_button_disabled(key))

    def reload_page(self):
        """
        Refresh the page.
        """
        self.browser.refresh()
        self.discussion_management_page.wait_for_page()

        self.instructor_dashboard_page.select_discussion_management()
        self.discussion_management_page.wait_for_page()

        self.divided_discussion_topics_are_visible()

    def verify_discussion_topics_after_reload(self, key, divided_topics):
        """
        Verifies the changed topics.
        """
        self.reload_page()
        self.assertEqual(self.discussion_management_page.get_divided_topics_count(key), divided_topics)

    def test_divide_course_wide_discussion_topic(self):
        """
        Scenario: divide a course-wide discussion topic.

        Given I have a course with a divide defined,
        And a course-wide discussion with disabled Save button.
        When I click on the course-wide discussion topic
        Then I see the enabled save button
        When I click on save button
        Then I see success message
        When I reload the page
        Then I see the discussion topic selected
        """
        self.divided_discussion_topics_are_visible()

        divided_topics_before = self.discussion_management_page.get_divided_topics_count(self.course_wide_key)
        self.discussion_management_page.select_discussion_topic(self.course_wide_key)

        self.assertFalse(self.discussion_management_page.is_save_button_disabled(self.course_wide_key))

        self.save_and_verify_discussion_topics(key=self.course_wide_key)
        divided_topics_after = self.discussion_management_page.get_divided_topics_count(self.course_wide_key)

        self.assertNotEqual(divided_topics_before, divided_topics_after)

        self.verify_discussion_topics_after_reload(self.course_wide_key, divided_topics_after)

    def test_always_divide_inline_topic_enabled(self):
        """
        Scenario: Select the always_divide_inline_topics radio button

        Given I have a course with a cohort defined,
        And an inline discussion topic with disabled Save button.
        When I click on always_divide_inline_topics
        Then I see enabled save button
        And I see disabled inline discussion topics
        When I save the change
        And I reload the page
        Then I see the always_divide_inline_topics option enabled
        """
        self.divided_discussion_topics_are_visible()

        # enable always inline discussion topics and save the change
        self.discussion_management_page.select_always_inline_discussion()
        self.assertFalse(self.discussion_management_page.is_save_button_disabled(self.inline_key))
        self.assertTrue(self.discussion_management_page.inline_discussion_topics_disabled())
        self.discussion_management_page.save_discussion_topics(key=self.inline_key)

        self.reload_page()
        self.assertTrue(self.discussion_management_page.always_inline_discussion_selected())

    def test_divide_some_inline_topics_enabled(self):
        """
        Scenario: Select the divide_some_inline_topics radio button

        Given I have a course with a divide defined and always_divide_inline_topics set to True
        And an inline discussion topic with disabled Save button.
        When I click on divide_some_inline_topics
        Then I see enabled save button
        And I see enabled inline discussion topics
        When I save the change
        And I reload the page
        Then I see the divide_some_inline_topics option enabled
        """
        self.divided_discussion_topics_are_visible()
        # By default always inline discussion topics is False. Enable it (and reload the page).
        self.assertFalse(self.discussion_management_page.always_inline_discussion_selected())
        self.discussion_management_page.select_always_inline_discussion()
        self.discussion_management_page.save_discussion_topics(key=self.inline_key)
        self.reload_page()
        self.assertFalse(self.discussion_management_page.divide_some_inline_discussion_selected())

        # enable some inline discussion topic radio button.
        self.discussion_management_page.select_divide_some_inline_discussion()
        # I see that save button is enabled
        self.assertFalse(self.discussion_management_page.is_save_button_disabled(self.inline_key))
        # I see that inline discussion topics are enabled
        self.assertFalse(self.discussion_management_page.inline_discussion_topics_disabled())
        self.discussion_management_page.save_discussion_topics(key=self.inline_key)

        self.reload_page()
        self.assertTrue(self.discussion_management_page.divide_some_inline_discussion_selected())

    def test_divide_inline_discussion_topic(self):
        """
        Scenario: divide inline discussion topic.

        Given I have a course with a divide defined,
        And a inline discussion topic with disabled Save button
        And When I click on inline discussion topic
        And I see enabled save button
        And When i click save button
        Then I see success message
        When I reload the page
        Then I see the discussion topic selected
        """
        self.divided_discussion_topics_are_visible()

        divided_topics_before = self.discussion_management_page.get_divided_topics_count(self.inline_key)
        # check the discussion topic.
        self.discussion_management_page.select_discussion_topic(self.inline_key)

        # Save button enabled.
        self.assertFalse(self.discussion_management_page.is_save_button_disabled(self.inline_key))

        # verifies that changes saved successfully.
        self.save_and_verify_discussion_topics(key=self.inline_key)

        divided_topics_after = self.discussion_management_page.get_divided_topics_count(self.inline_key)
        self.assertNotEqual(divided_topics_before, divided_topics_after)

        self.verify_discussion_topics_after_reload(self.inline_key, divided_topics_after)

    def test_verify_that_selecting_the_final_child_selects_category(self):
        """
        Scenario: Category should be selected on selecting final child.

        Given I have a course with a cohort defined,
        And a inline discussion with disabled Save button.
        When I click on child topics
        Then I see enabled saved button
        Then I see parent category to be checked.
        """
        self.divided_discussion_topics_are_visible()

        # category should not be selected.
        self.assertFalse(self.discussion_management_page.is_category_selected())

        # check the discussion topic.
        self.discussion_management_page.select_discussion_topic(self.inline_key)

        # verify that category is selected.
        self.assertTrue(self.discussion_management_page.is_category_selected())

    def test_verify_that_deselecting_the_final_child_deselects_category(self):
        """
        Scenario: Category should be deselected on deselecting final child.

        Given I have a course with a cohort defined,
        And a inline discussion with disabled Save button.
        When I click on final child topics
        Then I see enabled saved button
        Then I see parent category to be deselected.
        """
        self.divided_discussion_topics_are_visible()

        # category should not be selected.
        self.assertFalse(self.discussion_management_page.is_category_selected())

        # check the discussion topic.
        self.discussion_management_page.select_discussion_topic(self.inline_key)

        # verify that category is selected.
        self.assertTrue(self.discussion_management_page.is_category_selected())

        # un-check the discussion topic.
        self.discussion_management_page.select_discussion_topic(self.inline_key)

        # category should not be selected.
        self.assertFalse(self.discussion_management_page.is_category_selected())
