# -*- coding: utf-8 -*-
"""
End-to-end tests related to the divided discussion management on the LMS Instructor Dashboard
"""

import uuid

from common.test.acceptance.fixtures.course import CourseFixture, XBlockFixtureDesc
from common.test.acceptance.pages.common.auto_auth import AutoAuthPage
from common.test.acceptance.pages.common.utils import add_enrollment_course_modes
from common.test.acceptance.pages.lms.discussion import DiscussionTabSingleThreadPage
from common.test.acceptance.pages.lms.instructor_dashboard import InstructorDashboardPage
from common.test.acceptance.tests.discussion.helpers import BaseDiscussionMixin, CohortTestMixin
from common.test.acceptance.tests.helpers import UniqueCourseTest
from openedx.core.lib.tests import attr


class BaseDividedDiscussionTest(UniqueCourseTest, CohortTestMixin):
    """
    Base class for tests related to divided discussions.
    """
    def setUp(self):
        """
        Set up a discussion topic
        """
        super(BaseDividedDiscussionTest, self).setUp()

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
        self.scheme_key = 'scheme'

    def check_discussion_topic_visibility(self, visible=True):
        """
        Assert that discussion topics are visible with appropriate content.
        """
        self.assertEqual(visible, self.discussion_management_page.discussion_topics_visible())

        if visible:
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

    def reload_page(self, topics_visible=True):
        """
        Refresh the page, then verify if the discussion topics are visible on the discussion
        management instructor dashboard tab.
        """
        self.browser.refresh()
        self.discussion_management_page.wait_for_page()

        self.instructor_dashboard_page.select_discussion_management()
        self.discussion_management_page.wait_for_page()

        self.check_discussion_topic_visibility(topics_visible)

    def verify_save_confirmation_message(self, key):
        """
        Verify that the save confirmation message for the specified portion of the page is visible.
        """
        confirmation_message = self.discussion_management_page.get_divide_discussions_message(key=key)
        self.assertIn("Your changes have been saved.", confirmation_message)


@attr(shard=6)
class DividedDiscussionTopicsTest(BaseDividedDiscussionTest):
    """
    Tests for dividing the inline and course-wide discussion topics.
    """

    def save_and_verify_discussion_topics(self, key):
        """
        Saves the discussion topics and the verify the changes.
        """
        # click on the inline save button.
        self.discussion_management_page.save_discussion_topics(key)

        # verifies that changes saved successfully.
        self.verify_save_confirmation_message(key)

        # save button disabled again.
        self.assertTrue(self.discussion_management_page.is_save_button_disabled(key))

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
        self.check_discussion_topic_visibility()

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
        self.check_discussion_topic_visibility()

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
        self.check_discussion_topic_visibility()
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
        self.check_discussion_topic_visibility()

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
        self.check_discussion_topic_visibility()

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
        self.check_discussion_topic_visibility()

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


@attr(shard=6)
class DivisionSchemeTest(BaseDividedDiscussionTest, BaseDiscussionMixin):
    """
    Tests for changing the division scheme for Discussions.
    """

    def add_modes_and_view_discussion_mgmt_page(self, modes):
        """
        Adds enrollment modes to the course, and then goes to the
        discussion tab on the instructor dashboard.
        """
        add_enrollment_course_modes(self.browser, self.course_id, modes)
        self.view_discussion_management_page()

    def view_discussion_management_page(self):
        """
        Go to the discussion tab on the instructor dashboard.
        """
        self.instructor_dashboard_page.visit()
        self.assertTrue(self.instructor_dashboard_page.is_discussion_management_visible())
        self.instructor_dashboard_page.select_discussion_management()
        self.discussion_management_page.wait_for_page()

    def setup_thread_page(self, thread_id):
        """
        This is called by BaseDiscussionMixin.setup_thread.
        """
        self.thread_page = DiscussionTabSingleThreadPage(
            self.browser, self.course_id, self.discussion_id, thread_id
        )
        self.thread_page.visit()

    def test_not_divided_hides_discussion_topics(self):
        """
        Tests that discussion topics are hidden iff discussion division is disabled.
        """
        # Initially "Cohort" is the selected scheme.
        self.assertTrue(
            self.discussion_management_page.division_scheme_visible(self.discussion_management_page.COHORT_SCHEME)
        )
        self.assertEqual(
            self.discussion_management_page.COHORT_SCHEME,
            self.discussion_management_page.get_selected_scheme()
        )
        self.check_discussion_topic_visibility(visible=True)

        self.discussion_management_page.select_division_scheme(self.discussion_management_page.NOT_DIVIDED_SCHEME)
        self.verify_save_confirmation_message(self.scheme_key)
        self.check_discussion_topic_visibility(visible=False)

        # Reload the page and make sure that the change was persisted
        self.reload_page(topics_visible=False)
        self.assertTrue(self.discussion_management_page.division_scheme_visible(
            self.discussion_management_page.COHORT_SCHEME)
        )
        self.assertEqual(
            self.discussion_management_page.NOT_DIVIDED_SCHEME,
            self.discussion_management_page.get_selected_scheme()
        )

        # Select "cohort" again and make sure that the discussion topics appear.
        self.discussion_management_page.select_division_scheme(self.discussion_management_page.COHORT_SCHEME)
        self.verify_save_confirmation_message(self.scheme_key)
        self.check_discussion_topic_visibility(visible=True)

    def test_disabling_cohorts(self):
        """
        Test that the discussions management tab hides when there is <= 1 enrollment track, the Cohort division scheme
         is not selected, and cohorts are disabled.
        (even without reloading the page).
        """
        self.disable_cohorting(self.course_fixture)
        self.instructor_dashboard_page.visit()
        self.assertFalse(self.instructor_dashboard_page.is_discussion_management_visible())

    def test_disabling_cohorts_while_selected(self):
        """
        Test that disabling cohorts does not hide the discussion tab when there is more than one enrollment track.
        Also that the division scheme for cohorts is visible iff it was selected.
        (even without reloading the page).
        """
        add_enrollment_course_modes(self.browser, self.course_id, ['audit', 'verified'])

        # Verify that the tab is visible, the cohort scheme is selected by default for divided discussions
        self.disable_cohorting(self.course_fixture)

        # Go to Discussions tab and ensure that the correct scheme options are visible
        self.view_discussion_management_page()
        self.assertTrue(
            self.discussion_management_page.division_scheme_visible(
                self.discussion_management_page.COHORT_SCHEME
            )
        )

    def test_disabling_cohorts_while_not_selected(self):
        """
        Test that disabling cohorts does not hide the discussion tab when there is more than one enrollment track.
        Also that the division scheme for cohorts is not visible when cohorts are disabled and another scheme is
        selected for division.
        (even without reloading the page).
        """
        add_enrollment_course_modes(self.browser, self.course_id, ['audit', 'verified'])

        # Verify that the tab is visible
        self.view_discussion_management_page()
        self.discussion_management_page.select_division_scheme(self.discussion_management_page.ENROLLMENT_TRACK_SCHEME)
        self.verify_save_confirmation_message(self.scheme_key)
        self.disable_cohorting(self.course_fixture)

        # Go to Discussions tab and ensure that the correct scheme options are visible
        self.view_discussion_management_page()
        self.assertFalse(
            self.discussion_management_page.division_scheme_visible(
                self.discussion_management_page.COHORT_SCHEME
            )
        )

    def test_single_enrollment_mode(self):
        """
        Test that the enrollment track scheme is not visible if there is a single enrollment mode.
        """
        self.add_modes_and_view_discussion_mgmt_page(['audit'])
        self.assertFalse(
            self.discussion_management_page.division_scheme_visible(
                self.discussion_management_page.ENROLLMENT_TRACK_SCHEME
            )
        )

    def test_radio_buttons_with_multiple_enrollment_modes(self):
        """
        Test that the enrollment track scheme is visible if there are multiple enrollment tracks,
        and that the selection can be persisted.

        Also verifies that the cohort division scheme is not presented if cohorts are disabled and cohorts
        are not the selected division scheme.
        """
        self.add_modes_and_view_discussion_mgmt_page(['audit', 'verified'])
        self.assertTrue(
            self.discussion_management_page.division_scheme_visible(
                self.discussion_management_page.ENROLLMENT_TRACK_SCHEME
            )
        )
        # And the cohort scheme is initially visible because it is selected (and cohorts are enabled).
        self.assertTrue(
            self.discussion_management_page.division_scheme_visible(self.discussion_management_page.COHORT_SCHEME)
        )

        self.discussion_management_page.select_division_scheme(self.discussion_management_page.ENROLLMENT_TRACK_SCHEME)
        self.verify_save_confirmation_message(self.scheme_key)
        self.check_discussion_topic_visibility(visible=True)

        # Also disable cohorts so we can verify that the cohort scheme choice goes away.
        self.disable_cohorting(self.course_fixture)

        self.reload_page(topics_visible=True)
        self.assertEqual(
            self.discussion_management_page.ENROLLMENT_TRACK_SCHEME,
            self.discussion_management_page.get_selected_scheme()
        )
        # Verify that the cohort scheme is no longer visible as cohorts are disabled.
        self.assertFalse(
            self.discussion_management_page.division_scheme_visible(self.discussion_management_page.COHORT_SCHEME)
        )

    def test_enrollment_track_discussion_visibility_label(self):
        """
        If enrollment tracks are the division scheme, verifies that discussion visibility labels
        correctly render.

        Note that there are similar tests for cohorts in test_cohorts.py.
        """
        def refresh_thread_page():
            self.browser.refresh()
            self.thread_page.wait_for_page()

        # Make moderator for viewing all groups in discussions.
        AutoAuthPage(self.browser, course_id=self.course_id, roles="Moderator", staff=True).visit()

        self.add_modes_and_view_discussion_mgmt_page(['audit', 'verified'])
        self.discussion_management_page.select_division_scheme(self.discussion_management_page.ENROLLMENT_TRACK_SCHEME)
        self.verify_save_confirmation_message(self.scheme_key)
        # Set "always divide" as the thread we will be creating will be an inline thread,
        # and this way the thread does not need to be explicitly divided.
        self.enable_always_divide_inline_discussions(self.course_fixture)

        # Create a thread with group_id corresponding to the Audit enrollment mode.
        # The Audit group ID is 1, and for the comment service group_id we negate it.
        self.setup_thread(1, group_id=-1)

        refresh_thread_page()
        self.assertEquals(
            self.thread_page.get_group_visibility_label(),
            "This post is visible only to {}.".format("Audit")
        )

        # Disable dividing discussions and verify that the post now shows as visible to everyone.
        self.view_discussion_management_page()
        self.discussion_management_page.select_division_scheme(self.discussion_management_page.NOT_DIVIDED_SCHEME)
        self.verify_save_confirmation_message(self.scheme_key)

        self.thread_page.visit()
        self.assertEquals(self.thread_page.get_group_visibility_label(), "This post is visible to everyone.")
