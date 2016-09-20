# -*- coding: utf-8 -*-
"""
End-to-end tests for the LMS.
"""

import json
from datetime import datetime, timedelta

import ddt
from flaky import flaky
from nose.plugins.attrib import attr

from ..helpers import UniqueCourseTest, EventsTestMixin, auto_auth, create_multiple_choice_problem
from ...fixtures.course import CourseFixture, XBlockFixtureDesc
from ...pages.common.logout import LogoutPage
from ...pages.lms.course_nav import CourseNavPage
from ...pages.lms.courseware import CoursewarePage, CoursewareSequentialTabPage
from ...pages.lms.create_mode import ModeCreationPage
from ...pages.lms.dashboard import DashboardPage
from ...pages.lms.pay_and_verify import PaymentAndVerificationFlow, FakePaymentPage, FakeSoftwareSecureVerificationPage
from ...pages.lms.problem import ProblemPage
from ...pages.lms.progress import ProgressPage
from ...pages.lms.staff_view import StaffPage
from ...pages.lms.track_selection import TrackSelectionPage
from ...pages.studio.auto_auth import AutoAuthPage
from ...pages.studio.overview import CourseOutlinePage


class CoursewareTest(UniqueCourseTest):
    """
    Test courseware.
    """
    USERNAME = "STUDENT_TESTER"
    EMAIL = "student101@example.com"

    def setUp(self):
        super(CoursewareTest, self).setUp()

        self.courseware_page = CoursewarePage(self.browser, self.course_id)
        self.course_nav = CourseNavPage(self.browser)

        self.course_outline = CourseOutlinePage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

        # Install a course with sections/problems, tabs, updates, and handouts
        self.course_fix = CourseFixture(
            self.course_info['org'], self.course_info['number'],
            self.course_info['run'], self.course_info['display_name']
        )

        self.course_fix.add_children(
            XBlockFixtureDesc('chapter', 'Test Section 1').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection 1').add_children(
                    XBlockFixtureDesc('problem', 'Test Problem 1')
                )
            ),
            XBlockFixtureDesc('chapter', 'Test Section 2').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection 2').add_children(
                    XBlockFixtureDesc('problem', 'Test Problem 2')
                )
            )
        ).install()

        # Auto-auth register for the course.
        auto_auth(self.browser, self.USERNAME, self.EMAIL, False, self.course_id)

    def _goto_problem_page(self):
        """
        Open problem page with assertion.
        """
        self.courseware_page.visit()
        self.problem_page = ProblemPage(self.browser)  # pylint: disable=attribute-defined-outside-init
        self.assertEqual(self.problem_page.problem_name, 'Test Problem 1')

    def _create_breadcrumb(self, index):
        """ Create breadcrumb """
        return ['Test Section {}'.format(index), 'Test Subsection {}'.format(index), 'Test Problem {}'.format(index)]

    def test_courseware(self):
        """
        Test courseware if recent visited subsection become unpublished.
        """

        # Visit problem page as a student.
        self._goto_problem_page()

        # Logout and login as a staff user.
        LogoutPage(self.browser).visit()
        auto_auth(self.browser, "STAFF_TESTER", "staff101@example.com", True, self.course_id)

        # Visit course outline page in studio.
        self.course_outline.visit()

        # Set release date for subsection in future.
        self.course_outline.change_problem_release_date()

        # Logout and login as a student.
        LogoutPage(self.browser).visit()
        auto_auth(self.browser, self.USERNAME, self.EMAIL, False, self.course_id)

        # Visit courseware as a student.
        self.courseware_page.visit()
        # Problem name should be "Test Problem 2".
        self.assertEqual(self.problem_page.problem_name, 'Test Problem 2')

    def test_course_tree_breadcrumb(self):
        """
        Scenario: Correct course tree breadcrumb is shown.

        Given that I am a registered user
        And I visit my courseware page
        Then I should see correct course tree breadcrumb
        """
        self.courseware_page.visit()

        xblocks = self.course_fix.get_nested_xblocks(category="problem")
        for index in range(1, len(xblocks) + 1):
            self.course_nav.go_to_section('Test Section {}'.format(index), 'Test Subsection {}'.format(index))
            courseware_page_breadcrumb = self.courseware_page.breadcrumb
            expected_breadcrumb = self._create_breadcrumb(index)  # pylint: disable=no-member
            self.assertEqual(courseware_page_breadcrumb, expected_breadcrumb)


@ddt.ddt
class ProctoredExamTest(UniqueCourseTest):
    """
    Test courseware.
    """
    USERNAME = "STUDENT_TESTER"
    EMAIL = "student101@example.com"

    def setUp(self):
        super(ProctoredExamTest, self).setUp()

        self.courseware_page = CoursewarePage(self.browser, self.course_id)

        self.course_outline = CourseOutlinePage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

        # Install a course with sections/problems, tabs, updates, and handouts
        course_fix = CourseFixture(
            self.course_info['org'], self.course_info['number'],
            self.course_info['run'], self.course_info['display_name']
        )
        course_fix.add_advanced_settings({
            "enable_proctored_exams": {"value": "true"}
        })

        course_fix.add_children(
            XBlockFixtureDesc('chapter', 'Test Section 1').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection 1').add_children(
                    XBlockFixtureDesc('problem', 'Test Problem 1')
                )
            )
        ).install()

        self.track_selection_page = TrackSelectionPage(self.browser, self.course_id)
        self.payment_and_verification_flow = PaymentAndVerificationFlow(self.browser, self.course_id)
        self.immediate_verification_page = PaymentAndVerificationFlow(
            self.browser, self.course_id, entry_point='verify-now'
        )
        self.upgrade_page = PaymentAndVerificationFlow(self.browser, self.course_id, entry_point='upgrade')
        self.fake_payment_page = FakePaymentPage(self.browser, self.course_id)
        self.dashboard_page = DashboardPage(self.browser)
        self.problem_page = ProblemPage(self.browser)

        # Add a verified mode to the course
        ModeCreationPage(
            self.browser, self.course_id, mode_slug=u'verified', mode_display_name=u'Verified Certificate',
            min_price=10, suggested_prices='10,20'
        ).visit()

        # Auto-auth register for the course.
        auto_auth(self.browser, self.USERNAME, self.EMAIL, False, self.course_id)

    def _login_as_a_verified_user(self):
        """
        login as a verififed user
        """

        auto_auth(self.browser, self.USERNAME, self.EMAIL, False, self.course_id)

        # the track selection page cannot be visited. see the other tests to see if any prereq is there.
        # Navigate to the track selection page
        self.track_selection_page.visit()

        # Enter the payment and verification flow by choosing to enroll as verified
        self.track_selection_page.enroll('verified')

        # Proceed to the fake payment page
        self.payment_and_verification_flow.proceed_to_payment()

        # Submit payment
        self.fake_payment_page.submit_payment()

    def _verify_user(self):
        """
        Takes user through the verification flow and then marks the verification as 'approved'.
        """
        # Immediately verify the user
        self.immediate_verification_page.immediate_verification()

        # Take face photo and proceed to the ID photo step
        self.payment_and_verification_flow.webcam_capture()
        self.payment_and_verification_flow.next_verification_step(self.immediate_verification_page)

        # Take ID photo and proceed to the review photos step
        self.payment_and_verification_flow.webcam_capture()
        self.payment_and_verification_flow.next_verification_step(self.immediate_verification_page)

        # Submit photos and proceed to the enrollment confirmation step
        self.payment_and_verification_flow.next_verification_step(self.immediate_verification_page)

        # Mark the verification as passing.
        verification = FakeSoftwareSecureVerificationPage(self.browser).visit()
        verification.mark_approved()

    def test_can_create_proctored_exam_in_studio(self):
        """
        Given that I am a staff member
        When I visit the course outline page in studio.
        And open the subsection edit dialog
        Then I can view all settings related to Proctored and timed exams
        """
        LogoutPage(self.browser).visit()
        auto_auth(self.browser, "STAFF_TESTER", "staff101@example.com", True, self.course_id)
        self.course_outline.visit()

        self.course_outline.open_subsection_settings_dialog()
        self.assertTrue(self.course_outline.proctoring_items_are_displayed())

    def test_proctored_exam_flow(self):
        """
        Given that I am a staff member on the exam settings section
        select advanced settings tab
        When I Make the exam proctored.
        And I login as a verified student.
        And I verify the user's ID.
        And visit the courseware as a verified student.
        Then I can see an option to take the exam as a proctored exam.
        """
        LogoutPage(self.browser).visit()
        auto_auth(self.browser, "STAFF_TESTER", "staff101@example.com", True, self.course_id)
        self.course_outline.visit()
        self.course_outline.open_subsection_settings_dialog()

        self.course_outline.select_advanced_tab()
        self.course_outline.make_exam_proctored()

        LogoutPage(self.browser).visit()
        self._login_as_a_verified_user()

        self._verify_user()

        self.courseware_page.visit()
        self.assertTrue(self.courseware_page.can_start_proctored_exam)

    def _setup_and_take_timed_exam(self, hide_after_due=False):
        """
        Helper to perform the common action "set up a timed exam as staff,
        then take it as student"
        """
        LogoutPage(self.browser).visit()
        auto_auth(self.browser, "STAFF_TESTER", "staff101@example.com", True, self.course_id)
        self.course_outline.visit()
        self.course_outline.open_subsection_settings_dialog()

        self.course_outline.select_advanced_tab()
        self.course_outline.make_exam_timed(hide_after_due=hide_after_due)

        LogoutPage(self.browser).visit()
        self._login_as_a_verified_user()
        self.courseware_page.visit()

        self.courseware_page.start_timed_exam()
        self.assertTrue(self.courseware_page.is_timer_bar_present)

        self.courseware_page.stop_timed_exam()
        self.assertTrue(self.courseware_page.has_submitted_exam_message())

        LogoutPage(self.browser).visit()

    @flaky  # TNL-5643
    @ddt.data(True, False)
    def test_timed_exam_flow(self, hide_after_due):
        """
        Given that I am a staff member on the exam settings section
        select advanced settings tab
        When I Make the exam timed.
        And I login as a verified student.
        And visit the courseware as a verified student.
        And I start the timed exam
        Then I am taken to the exam with a timer bar showing
        When I finish the exam
        Then I see the exam submitted dialog in place of the exam
        When I log back into studio as a staff member
        And change the problem's due date to be in the past
        And log back in as the original verified student
        Then I see the exam or message in accordance with the hide_after_due setting
        """
        self._setup_and_take_timed_exam(hide_after_due)

        LogoutPage(self.browser).visit()
        auto_auth(self.browser, "STAFF_TESTER", "staff101@example.com", True, self.course_id)
        self.course_outline.visit()
        last_week = (datetime.today() - timedelta(days=7)).strftime("%m/%d/%Y")
        self.course_outline.change_problem_due_date(last_week)

        LogoutPage(self.browser).visit()
        auto_auth(self.browser, self.USERNAME, self.EMAIL, False, self.course_id)
        self.courseware_page.visit()
        self.assertEqual(self.courseware_page.has_submitted_exam_message(), hide_after_due)

    def test_masquerade_visibility_override(self):
        """
        Given that a timed exam problem exists in the course
        And a student has taken that exam
        And that exam is hidden to the student
        And I am a staff user masquerading as the student
        Then I should be able to see the exam content
        """
        self._setup_and_take_timed_exam()

        LogoutPage(self.browser).visit()
        auto_auth(self.browser, "STAFF_TESTER", "staff101@example.com", True, self.course_id)
        self.courseware_page.visit()
        staff_page = StaffPage(self.browser, self.course_id)
        self.assertEqual(staff_page.staff_view_mode, 'Staff')

        staff_page.set_staff_view_mode_specific_student(self.USERNAME)
        self.assertFalse(self.courseware_page.has_submitted_exam_message())

    def test_field_visiblity_with_all_exam_types(self):
        """
        Given that I am a staff member
        And I have visited the course outline page in studio.
        And the subsection edit dialog is open
        select advanced settings tab
        For each of None, Timed, Proctored, and Practice exam types
        The time allotted and review rules fields have proper visibility
        None: False, False
        Timed: True, False
        Proctored: True, True
        Practice: True, False
        """
        LogoutPage(self.browser).visit()
        auto_auth(self.browser, "STAFF_TESTER", "staff101@example.com", True, self.course_id)
        self.course_outline.visit()

        self.course_outline.open_subsection_settings_dialog()
        self.course_outline.select_advanced_tab()

        self.course_outline.select_none_exam()
        self.assertFalse(self.course_outline.time_allotted_field_visible())
        self.assertFalse(self.course_outline.exam_review_rules_field_visible())

        self.course_outline.select_timed_exam()
        self.assertTrue(self.course_outline.time_allotted_field_visible())
        self.assertFalse(self.course_outline.exam_review_rules_field_visible())

        self.course_outline.select_proctored_exam()
        self.assertTrue(self.course_outline.time_allotted_field_visible())
        self.assertTrue(self.course_outline.exam_review_rules_field_visible())

        self.course_outline.select_practice_exam()
        self.assertTrue(self.course_outline.time_allotted_field_visible())
        self.assertFalse(self.course_outline.exam_review_rules_field_visible())


class CoursewareMultipleVerticalsTest(UniqueCourseTest, EventsTestMixin):
    """
    Test courseware with multiple verticals
    """
    USERNAME = "STUDENT_TESTER"
    EMAIL = "student101@example.com"

    def setUp(self):
        super(CoursewareMultipleVerticalsTest, self).setUp()

        self.courseware_page = CoursewarePage(self.browser, self.course_id)

        self.course_outline = CourseOutlinePage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

        # Install a course with sections/problems, tabs, updates, and handouts
        course_fix = CourseFixture(
            self.course_info['org'], self.course_info['number'],
            self.course_info['run'], self.course_info['display_name']
        )

        course_fix.add_children(
            XBlockFixtureDesc('chapter', 'Test Section 1').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection 1,1').add_children(
                    XBlockFixtureDesc('problem', 'Test Problem 1', data='<problem>problem 1 dummy body</problem>'),
                    XBlockFixtureDesc('html', 'html 1', data="<html>html 1 dummy body</html>"),
                    XBlockFixtureDesc('problem', 'Test Problem 2', data="<problem>problem 2 dummy body</problem>"),
                    XBlockFixtureDesc('html', 'html 2', data="<html>html 2 dummy body</html>"),
                ),
                XBlockFixtureDesc('sequential', 'Test Subsection 1,2').add_children(
                    XBlockFixtureDesc('problem', 'Test Problem 3', data='<problem>problem 3 dummy body</problem>'),
                ),
                XBlockFixtureDesc(
                    'sequential', 'Test HIDDEN Subsection', metadata={'visible_to_staff_only': True}
                ).add_children(
                    XBlockFixtureDesc('problem', 'Test HIDDEN Problem', data='<problem>hidden problem</problem>'),
                ),
            ),
            XBlockFixtureDesc('chapter', 'Test Section 2').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection 2,1').add_children(
                    XBlockFixtureDesc('problem', 'Test Problem 4', data='<problem>problem 4 dummy body</problem>'),
                ),
            ),
            XBlockFixtureDesc('chapter', 'Test HIDDEN Section', metadata={'visible_to_staff_only': True}).add_children(
                XBlockFixtureDesc('sequential', 'Test HIDDEN Subsection'),
            ),
        ).install()

        # Auto-auth register for the course.
        AutoAuthPage(self.browser, username=self.USERNAME, email=self.EMAIL,
                     course_id=self.course_id, staff=False).visit()
        self.courseware_page.visit()
        self.course_nav = CourseNavPage(self.browser)

    def test_navigation_buttons(self):
        # start in first section
        self.assert_navigation_state('Test Section 1', 'Test Subsection 1,1', 0, next_enabled=True, prev_enabled=False)

        # next takes us to next tab in sequential
        self.courseware_page.click_next_button_on_top()
        self.assert_navigation_state('Test Section 1', 'Test Subsection 1,1', 1, next_enabled=True, prev_enabled=True)

        # go to last sequential position
        self.courseware_page.go_to_sequential_position(4)
        self.assert_navigation_state('Test Section 1', 'Test Subsection 1,1', 3, next_enabled=True, prev_enabled=True)

        # next takes us to next sequential
        self.courseware_page.click_next_button_on_bottom()
        self.assert_navigation_state('Test Section 1', 'Test Subsection 1,2', 0, next_enabled=True, prev_enabled=True)

        # next takes us to next chapter
        self.courseware_page.click_next_button_on_top()
        self.assert_navigation_state('Test Section 2', 'Test Subsection 2,1', 0, next_enabled=False, prev_enabled=True)

        # previous takes us to previous chapter
        self.courseware_page.click_previous_button_on_top()
        self.assert_navigation_state('Test Section 1', 'Test Subsection 1,2', 0, next_enabled=True, prev_enabled=True)

        # previous takes us to last tab in previous sequential
        self.courseware_page.click_previous_button_on_bottom()
        self.assert_navigation_state('Test Section 1', 'Test Subsection 1,1', 3, next_enabled=True, prev_enabled=True)

        # previous takes us to previous tab in sequential
        self.courseware_page.click_previous_button_on_bottom()
        self.assert_navigation_state('Test Section 1', 'Test Subsection 1,1', 2, next_enabled=True, prev_enabled=True)

        # test UI events emitted by navigation
        filter_sequence_ui_event = lambda event: event.get('name', '').startswith('edx.ui.lms.sequence.')

        sequence_ui_events = self.wait_for_events(event_filter=filter_sequence_ui_event, timeout=2)
        legacy_events = [ev for ev in sequence_ui_events if ev['event_type'] in {'seq_next', 'seq_prev', 'seq_goto'}]
        nonlegacy_events = [ev for ev in sequence_ui_events if ev not in legacy_events]

        self.assertTrue(all('old' in json.loads(ev['event']) for ev in legacy_events))
        self.assertTrue(all('new' in json.loads(ev['event']) for ev in legacy_events))
        self.assertFalse(any('old' in json.loads(ev['event']) for ev in nonlegacy_events))
        self.assertFalse(any('new' in json.loads(ev['event']) for ev in nonlegacy_events))

        self.assert_events_match(
            [
                {
                    'event_type': 'seq_next',
                    'event': {
                        'old': 1,
                        'new': 2,
                        'current_tab': 1,
                        'tab_count': 4,
                        'widget_placement': 'top',
                    }
                },
                {
                    'event_type': 'seq_goto',
                    'event': {
                        'old': 2,
                        'new': 4,
                        'current_tab': 2,
                        'target_tab': 4,
                        'tab_count': 4,
                        'widget_placement': 'top',
                    }
                },
                {
                    'event_type': 'edx.ui.lms.sequence.next_selected',
                    'event': {
                        'current_tab': 4,
                        'tab_count': 4,
                        'widget_placement': 'bottom',
                    }
                },
                {
                    'event_type': 'edx.ui.lms.sequence.next_selected',
                    'event': {
                        'current_tab': 1,
                        'tab_count': 1,
                        'widget_placement': 'top',
                    }
                },
                {
                    'event_type': 'edx.ui.lms.sequence.previous_selected',
                    'event': {
                        'current_tab': 1,
                        'tab_count': 1,
                        'widget_placement': 'top',
                    }
                },
                {
                    'event_type': 'edx.ui.lms.sequence.previous_selected',
                    'event': {
                        'current_tab': 1,
                        'tab_count': 1,
                        'widget_placement': 'bottom',
                    }
                },
                {
                    'event_type': 'seq_prev',
                    'event': {
                        'old': 4,
                        'new': 3,
                        'current_tab': 4,
                        'tab_count': 4,
                        'widget_placement': 'bottom',
                    }
                },
            ],
            sequence_ui_events
        )

    def test_outline_selected_events(self):
        self.course_nav.go_to_section('Test Section 1', 'Test Subsection 1,2')

        self.course_nav.go_to_section('Test Section 2', 'Test Subsection 2,1')

        # test UI events emitted by navigating via the course outline
        filter_selected_events = lambda event: event.get('name', '') == 'edx.ui.lms.outline.selected'
        selected_events = self.wait_for_events(event_filter=filter_selected_events, timeout=2)

        # note: target_url is tested in unit tests, as the url changes here with every test (it includes GUIDs).
        self.assert_events_match(
            [
                {
                    'event_type': 'edx.ui.lms.outline.selected',
                    'name': 'edx.ui.lms.outline.selected',
                    'event': {
                        'target_name': 'Test Subsection 1,2 ',
                        'widget_placement': 'accordion',
                    }
                },
                {
                    'event_type': 'edx.ui.lms.outline.selected',
                    'name': 'edx.ui.lms.outline.selected',
                    'event': {
                        'target_name': 'Test Subsection 2,1 ',
                        'widget_placement': 'accordion',

                    }
                },
            ],
            selected_events
        )

    def test_link_clicked_events(self):
        """
        Given that I am a user in the courseware
        When I navigate via the left-hand nav
        Then a link clicked event is logged
        """
        self.course_nav.go_to_section('Test Section 1', 'Test Subsection 1,2')
        self.course_nav.go_to_section('Test Section 2', 'Test Subsection 2,1')

        filter_link_clicked = lambda event: event.get('name', '') == 'edx.ui.lms.link_clicked'
        link_clicked_events = self.wait_for_events(event_filter=filter_link_clicked, timeout=2)
        self.assertEqual(len(link_clicked_events), 2)

    def assert_navigation_state(
            self, section_title, subsection_title, subsection_position, next_enabled, prev_enabled
    ):
        """
        Verifies that the navigation state is as expected.
        """
        self.assertTrue(self.course_nav.is_on_section(section_title, subsection_title))
        self.assertEquals(self.courseware_page.sequential_position, subsection_position)
        self.assertEquals(self.courseware_page.is_next_button_enabled, next_enabled)
        self.assertEquals(self.courseware_page.is_previous_button_enabled, prev_enabled)

    def test_tab_position(self):
        # test that using the position in the url direct to correct tab in courseware
        self.course_nav.go_to_section('Test Section 1', 'Test Subsection 1,1')
        subsection_url = self.course_nav.active_subsection_url
        url_part_list = subsection_url.split('/')
        self.assertEqual(len(url_part_list), 9)

        course_id = url_part_list[4]
        chapter_id = url_part_list[-3]
        subsection_id = url_part_list[-2]
        problem1_page = CoursewareSequentialTabPage(
            self.browser,
            course_id=course_id,
            chapter=chapter_id,
            subsection=subsection_id,
            position=1
        ).visit()
        self.assertIn('problem 1 dummy body', problem1_page.get_selected_tab_content())

        html1_page = CoursewareSequentialTabPage(
            self.browser,
            course_id=course_id,
            chapter=chapter_id,
            subsection=subsection_id,
            position=2
        ).visit()
        self.assertIn('html 1 dummy body', html1_page.get_selected_tab_content())

        problem2_page = CoursewareSequentialTabPage(
            self.browser,
            course_id=course_id,
            chapter=chapter_id,
            subsection=subsection_id,
            position=3
        ).visit()
        self.assertIn('problem 2 dummy body', problem2_page.get_selected_tab_content())

        html2_page = CoursewareSequentialTabPage(
            self.browser,
            course_id=course_id,
            chapter=chapter_id,
            subsection=subsection_id,
            position=4
        ).visit()
        self.assertIn('html 2 dummy body', html2_page.get_selected_tab_content())

    @attr('a11y')
    def test_courseware_a11y(self):
        """
        Run accessibility audit for the problem type.
        """
        self.course_nav.go_to_section('Test Section 1', 'Test Subsection 1,1')
        # Set the scope to the sequence navigation
        self.courseware_page.a11y_audit.config.set_scope(
            include=['div.sequence-nav'])
        self.courseware_page.a11y_audit.check_for_accessibility_errors()


class ProblemStateOnNavigationTest(UniqueCourseTest):
    """
    Test courseware with problems in multiple verticals
    """
    USERNAME = "STUDENT_TESTER"
    EMAIL = "student101@example.com"

    problem1_name = 'MULTIPLE CHOICE TEST PROBLEM 1'
    problem2_name = 'MULTIPLE CHOICE TEST PROBLEM 2'

    def setUp(self):
        super(ProblemStateOnNavigationTest, self).setUp()

        self.courseware_page = CoursewarePage(self.browser, self.course_id)

        # Install a course with section, tabs and multiple choice problems.
        course_fix = CourseFixture(
            self.course_info['org'], self.course_info['number'],
            self.course_info['run'], self.course_info['display_name']
        )

        course_fix.add_children(
            XBlockFixtureDesc('chapter', 'Test Section 1').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection 1,1').add_children(
                    create_multiple_choice_problem(self.problem1_name),
                    create_multiple_choice_problem(self.problem2_name),
                ),
            ),
        ).install()

        # Auto-auth register for the course.
        AutoAuthPage(
            self.browser, username=self.USERNAME, email=self.EMAIL,
            course_id=self.course_id, staff=False
        ).visit()

        self.courseware_page.visit()
        self.problem_page = ProblemPage(self.browser)

    def go_to_tab_and_assert_problem(self, position, problem_name):
        """
        Go to sequential tab and assert that we are on problem whose name is given as a parameter.
        Args:
            position: Position of the sequential tab
            problem_name: Name of the problem
        """
        self.courseware_page.go_to_sequential_position(position)
        self.problem_page.wait_for_element_presence(
            self.problem_page.CSS_PROBLEM_HEADER,
            'wait for problem header'
        )
        self.assertEqual(self.problem_page.problem_name, problem_name)

    def test_perform_problem_check_and_navigate(self):
        """
        Scenario:
        I go to sequential position 1
        Facing problem1, I select 'choice_1'
        Then I click check button
        Then I go to sequential position 2
        Then I came back to sequential position 1 again
        Facing problem1, I observe the problem1 content is not
        outdated before and after sequence navigation
        """
        # Go to sequential position 1 and assert that we are on problem 1.
        self.go_to_tab_and_assert_problem(1, self.problem1_name)

        # Update problem 1's content state by clicking check button.
        self.problem_page.click_choice('choice_choice_1')
        self.problem_page.click_check()
        self.problem_page.wait_for_expected_status('label.choicegroup_incorrect', 'incorrect')

        # Save problem 1's content state as we're about to switch units in the sequence.
        problem1_content_before_switch = self.problem_page.problem_content

        # Go to sequential position 2 and assert that we are on problem 2.
        self.go_to_tab_and_assert_problem(2, self.problem2_name)

        # Come back to our original unit in the sequence and assert that the content hasn't changed.
        self.go_to_tab_and_assert_problem(1, self.problem1_name)
        problem1_content_after_coming_back = self.problem_page.problem_content
        self.assertEqual(problem1_content_before_switch, problem1_content_after_coming_back)

    def test_perform_problem_save_and_navigate(self):
        """
        Scenario:
        I go to sequential position 1
        Facing problem1, I select 'choice_1'
        Then I click save button
        Then I go to sequential position 2
        Then I came back to sequential position 1 again
        Facing problem1, I observe the problem1 content is not
        outdated before and after sequence navigation
        """
        # Go to sequential position 1 and assert that we are on problem 1.
        self.go_to_tab_and_assert_problem(1, self.problem1_name)

        # Update problem 1's content state by clicking save button.
        self.problem_page.click_choice('choice_choice_1')
        self.problem_page.click_save()
        self.problem_page.wait_for_expected_status('div.capa_alert', 'saved')

        # Save problem 1's content state as we're about to switch units in the sequence.
        problem1_content_before_switch = self.problem_page.problem_content

        # Go to sequential position 2 and assert that we are on problem 2.
        self.go_to_tab_and_assert_problem(2, self.problem2_name)

        # Come back to our original unit in the sequence and assert that the content hasn't changed.
        self.go_to_tab_and_assert_problem(1, self.problem1_name)
        problem1_content_after_coming_back = self.problem_page.problem_content
        self.assertIn(problem1_content_after_coming_back, problem1_content_before_switch)

    def test_perform_problem_reset_and_navigate(self):
        """
        Scenario:
        I go to sequential position 1
        Facing problem1, I select 'choice_1'
        Then perform the action – check and reset
        Then I go to sequential position 2
        Then I came back to sequential position 1 again
        Facing problem1, I observe the problem1 content is not
        outdated before and after sequence navigation
        """
        # Go to sequential position 1 and assert that we are on problem 1.
        self.go_to_tab_and_assert_problem(1, self.problem1_name)

        # Update problem 1's content state – by performing reset operation.
        self.problem_page.click_choice('choice_choice_1')
        self.problem_page.click_check()
        self.problem_page.wait_for_expected_status('label.choicegroup_incorrect', 'incorrect')
        self.problem_page.click_reset()
        self.problem_page.wait_for_expected_status('span.unanswered', 'unanswered')

        # Save problem 1's content state as we're about to switch units in the sequence.
        problem1_content_before_switch = self.problem_page.problem_content

        # Go to sequential position 2 and assert that we are on problem 2.
        self.go_to_tab_and_assert_problem(2, self.problem2_name)

        # Come back to our original unit in the sequence and assert that the content hasn't changed.
        self.go_to_tab_and_assert_problem(1, self.problem1_name)
        problem1_content_after_coming_back = self.problem_page.problem_content
        self.assertEqual(problem1_content_before_switch, problem1_content_after_coming_back)


class SubsectionHiddenAfterDueDateTest(UniqueCourseTest):
    """
    Tests the "hide after due date" setting for
    subsections.
    """
    USERNAME = "STUDENT_TESTER"
    EMAIL = "student101@example.com"

    def setUp(self):
        super(SubsectionHiddenAfterDueDateTest, self).setUp()

        self.courseware_page = CoursewarePage(self.browser, self.course_id)
        self.logout_page = LogoutPage(self.browser)

        self.course_outline = CourseOutlinePage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

        # Install a course with sections/problems, tabs, updates, and handouts
        course_fix = CourseFixture(
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run'],
            self.course_info['display_name']
        )

        course_fix.add_children(
            XBlockFixtureDesc('chapter', 'Test Section 1').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection 1').add_children(
                    create_multiple_choice_problem('Test Problem 1')
                )
            )
        ).install()

        self.progress_page = ProgressPage(self.browser, self.course_id)
        self._setup_subsection()

        # Auto-auth register for the course.
        auto_auth(self.browser, self.USERNAME, self.EMAIL, False, self.course_id)

    def _setup_subsection(self):
        """
        Helper to set up a problem subsection as staff, then take
        it as a student.
        """
        self.logout_page.visit()
        auto_auth(self.browser, "STAFF_TESTER", "staff101@example.com", True, self.course_id)
        self.course_outline.visit()
        self.course_outline.open_subsection_settings_dialog()

        self.course_outline.select_advanced_tab('hide_after_due_date')
        self.course_outline.make_subsection_hidden_after_due_date()

        self.logout_page.visit()
        auto_auth(self.browser, self.USERNAME, self.EMAIL, False, self.course_id)
        self.courseware_page.visit()

        self.logout_page.visit()

    def test_subsecton_hidden_after_due_date(self):
        """
        Given that I am a staff member on the subsection settings section
        And I select the advanced settings tab
        When I Make the subsection hidden after its due date.
        And I login as a student.
        And visit the subsection in the courseware as a verified student.
        Then I am able to see the subsection
        And when I visit the progress page
        Then I should be able to see my grade on the progress page
        When I log in as staff
        And I make the subsection due in the past so that the current date is past its due date
        And I log in as a student
        And I visit the subsection in the courseware
        Then the subsection should be hidden with a message that its due date has passed
        And when I visit the progress page
        Then I should be able to see my grade on the progress page
        """
        self.logout_page.visit()
        auto_auth(self.browser, self.USERNAME, self.EMAIL, False, self.course_id)
        self.courseware_page.visit()
        self.assertFalse(self.courseware_page.content_hidden_past_due_date())

        self.progress_page.visit()
        self.assertEqual(self.progress_page.scores('Test Section 1', 'Test Subsection 1'), [(0, 1)])

        self.logout_page.visit()
        auto_auth(self.browser, "STAFF_TESTER", "staff101@example.com", True, self.course_id)
        self.course_outline.visit()
        last_week = (datetime.today() - timedelta(days=7)).strftime("%m/%d/%Y")
        self.course_outline.change_problem_due_date(last_week)

        self.logout_page.visit()
        auto_auth(self.browser, self.USERNAME, self.EMAIL, False, self.course_id)
        self.courseware_page.visit()
        self.assertTrue(self.courseware_page.content_hidden_past_due_date())

        self.progress_page.visit()
        self.assertEqual(self.progress_page.scores('Test Section 1', 'Test Subsection 1'), [(0, 1)])
