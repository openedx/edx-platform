# -*- coding: utf-8 -*-
"""
End-to-end tests for the LMS.
"""


import json
from datetime import datetime, timedelta
from textwrap import dedent

import pytz

from common.test.acceptance.fixtures.course import CourseFixture, XBlockFixtureDesc
from common.test.acceptance.pages.common.auto_auth import AutoAuthPage
from common.test.acceptance.pages.common.logout import LogoutPage
from common.test.acceptance.pages.common.utils import enroll_user_track
from common.test.acceptance.pages.lms import BASE_URL
from common.test.acceptance.pages.lms.account_settings import AccountSettingsPage
from common.test.acceptance.pages.lms.course_about import CourseAboutPage
from common.test.acceptance.pages.lms.course_home import CourseHomePage
from common.test.acceptance.pages.lms.course_wiki import (
    CourseWikiChildrenPage,
    CourseWikiEditPage,
    CourseWikiHistoryPage,
    CourseWikiPage
)
from common.test.acceptance.pages.lms.courseware import CoursewarePage
from common.test.acceptance.pages.lms.create_mode import ModeCreationPage
from common.test.acceptance.pages.lms.dashboard import DashboardPage
from common.test.acceptance.pages.lms.discovery import CourseDiscoveryPage
from common.test.acceptance.pages.lms.login_and_register import CombinedLoginAndRegisterPage, ResetPasswordPage
from common.test.acceptance.pages.lms.pay_and_verify import FakePaymentPage, PaymentAndVerificationFlow
from common.test.acceptance.pages.lms.problem import ProblemPage
from common.test.acceptance.pages.lms.tab_nav import TabNavPage
from common.test.acceptance.tests.helpers import (
    EventsTestMixin,
    UniqueCourseTest,
    get_selected_option_text,
    remove_file,
    select_option_by_text
)
from openedx.core.lib.tests import attr


@attr(shard=19)
class ForgotPasswordPageTest(UniqueCourseTest):
    """
    Test that forgot password forms is rendered if url contains 'forgot-password-modal'
    in hash.
    """

    def setUp(self):
        """ Initialize the page object """
        super(ForgotPasswordPageTest, self).setUp()
        self.user_info = self._create_user()
        self.reset_password_page = ResetPasswordPage(self.browser)

    def _create_user(self):
        """
        Create a unique user
        """
        auto_auth = AutoAuthPage(self.browser).visit()
        user_info = auto_auth.user_info
        LogoutPage(self.browser).visit()
        return user_info

    def test_reset_password_form_visibility(self):
        # Navigate to the password reset page
        self.reset_password_page.visit()

        # Expect that reset password form is visible on the page
        self.assertTrue(self.reset_password_page.is_form_visible())

    def test_reset_password_confirmation_box_visibility(self):
        # Navigate to the password reset page
        self.reset_password_page.visit()

        # Navigate to the password reset form and try to submit it
        self.reset_password_page.fill_password_reset_form(self.user_info['email'])

        self.reset_password_page.is_success_visible(".submission-success")

        # Expect that we're shown a success message
        self.assertIn("Check Your Email", self.reset_password_page.get_success_message())


@attr(shard=19)
class LoginFromCombinedPageTest(UniqueCourseTest):
    """Test that we can log in using the combined login/registration page.

    Also test that we can request a password reset from the combined
    login/registration page.

    """

    def setUp(self):
        """Initialize the page objects and create a test course. """
        super(LoginFromCombinedPageTest, self).setUp()
        self.login_page = CombinedLoginAndRegisterPage(
            self.browser,
            start_page="login",
            course_id=self.course_id
        )
        self.dashboard_page = DashboardPage(self.browser)

        # Create a course to enroll in
        CourseFixture(
            self.course_info['org'], self.course_info['number'],
            self.course_info['run'], self.course_info['display_name']
        ).install()

    def test_login_success(self):
        # Create a user account
        email, password = self._create_unique_user()

        # Navigate to the login page and try to log in
        self.login_page.visit().login(email=email, password=password)

        # Expect that we reach the dashboard and we're auto-enrolled in the course
        course_names = self.dashboard_page.wait_for_page().available_courses
        self.assertIn(self.course_info["display_name"], course_names)

    def test_login_failure(self):
        # Navigate to the login page
        self.login_page.visit()

        # User account does not exist
        self.login_page.login(email="nobody@nowhere.com", password="password")

        # Verify that an error is displayed
        self.assertIn("Email or password is incorrect.", self.login_page.wait_for_errors())

    def test_toggle_to_register_form(self):
        self.login_page.visit().toggle_form()
        self.assertEqual(self.login_page.current_form, "register")

    def test_password_reset_success(self):
        # Create a user account
        email, password = self._create_unique_user()  # pylint: disable=unused-variable

        # Navigate to the password reset form and try to submit it
        self.login_page.visit().password_reset(email=email)

        # Expect that we're shown a success message
        self.assertIn("Check Your Email", self.login_page.wait_for_success())

    def test_password_reset_no_user(self):
        # Navigate to the password reset form
        self.login_page.visit()

        # User account does not exist
        self.login_page.password_reset(email="nobody@nowhere.com")

        # Expect that we're shown a success message
        self.assertIn("Check Your Email", self.login_page.wait_for_success())

    def test_third_party_login(self):
        """
        Test that we can login using third party credentials, and that the
        third party account gets linked to the edX account.
        """
        # Create a user account
        email, password = self._create_unique_user()

        # Navigate to the login page
        self.login_page.visit()
        # Baseline screen-shots are different for chrome and firefox.
        #self.assertScreenshot('#login .login-providers', 'login-providers-{}'.format(self.browser.name), .25)
        #The line above is commented out temporarily see SOL-1937

        # Try to log in using "Dummy" provider
        self.login_page.click_third_party_dummy_provider()

        # The user will be redirected somewhere and then back to the login page:
        msg_text = self.login_page.wait_for_auth_status_message()
        self.assertIn("You have successfully signed into Dummy", msg_text)
        self.assertIn(
            u"To link your accounts, sign in now using your édX password",
            msg_text
        )

        # Now login with username and password:
        self.login_page.login(email=email, password=password)

        # Expect that we reach the dashboard and we're auto-enrolled in the course
        course_names = self.dashboard_page.wait_for_page().available_courses
        self.assertIn(self.course_info["display_name"], course_names)

        try:
            # Now logout and check that we can log back in instantly (because the account is linked):
            LogoutPage(self.browser).visit()

            self.login_page.visit()
            self.login_page.click_third_party_dummy_provider()

            self.dashboard_page.wait_for_page()
        finally:
            self._unlink_dummy_account()

    def test_hinted_login(self):
        """ Test the login page when coming from course URL that specified which third party provider to use """
        # Create a user account and link it to third party auth with the dummy provider:
        AutoAuthPage(self.browser, course_id=self.course_id).visit()
        self._link_dummy_account()
        try:
            LogoutPage(self.browser).visit()

            # When not logged in, try to load a course URL that includes the provider hint ?tpa_hint=...
            course_page = CoursewarePage(self.browser, self.course_id)
            self.browser.get(course_page.url + '?tpa_hint=oa2-dummy')

            # We should now be redirected to the login page
            self.login_page.wait_for_page()
            self.assertIn(
                "Would you like to sign in using your Dummy credentials?",
                self.login_page.hinted_login_prompt
            )

            # Baseline screen-shots are different for chrome and firefox.
            #self.assertScreenshot('#hinted-login-form', 'hinted-login-{}'.format(self.browser.name), .25)
            #The line above is commented out temporarily see SOL-1937
            self.login_page.click_third_party_dummy_provider()

            # We should now be redirected to the course page
            course_page.wait_for_page()
        finally:
            self._unlink_dummy_account()

    def _link_dummy_account(self):
        """ Go to Account Settings page and link the user's account to the Dummy provider """
        account_settings = AccountSettingsPage(self.browser).visit()
        # switch to "Linked Accounts" tab
        account_settings.switch_account_settings_tabs('accounts-tab')

        field_id = "auth-oa2-dummy"
        account_settings.wait_for_field(field_id)
        self.assertEqual("Link Your Account", account_settings.link_title_for_link_field(field_id))
        account_settings.click_on_link_in_link_field(field_id)

        # make sure we are on "Linked Accounts" tab after the account settings
        # page is reloaded
        account_settings.switch_account_settings_tabs('accounts-tab')
        account_settings.wait_for_link_title_for_link_field(field_id, "Unlink This Account")

    def _unlink_dummy_account(self):
        """ Verify that the 'Dummy' third party auth provider is linked, then unlink it """
        # This must be done after linking the account, or we'll get cross-test side effects
        account_settings = AccountSettingsPage(self.browser).visit()
        # switch to "Linked Accounts" tab
        account_settings.switch_account_settings_tabs('accounts-tab')

        field_id = "auth-oa2-dummy"
        account_settings.wait_for_field(field_id)
        self.assertEqual("Unlink This Account", account_settings.link_title_for_link_field(field_id))
        account_settings.click_on_link_in_link_field(field_id)
        account_settings.wait_for_message(field_id, "Successfully unlinked")

    def _create_unique_user(self):
        """
        Create a new user with a unique name and email.
        """
        username = u"test_{uuid}".format(uuid=self.unique_id[0:6])
        email = u"{user}@example.com".format(user=username)
        password = "password"

        # Create the user (automatically logs us in)
        AutoAuthPage(
            self.browser,
            username=username,
            email=email,
            password=password
        ).visit()

        # Log out
        LogoutPage(self.browser).visit()

        return (email, password)


@attr(shard=19)
class RegisterFromCombinedPageTest(UniqueCourseTest):
    """Test that we can register a new user from the combined login/registration page. """

    def setUp(self):
        """Initialize the page objects and create a test course. """
        super(RegisterFromCombinedPageTest, self).setUp()
        self.register_page = CombinedLoginAndRegisterPage(
            self.browser,
            start_page="register",
            course_id=self.course_id
        )
        self.dashboard_page = DashboardPage(self.browser)

        # Create a course to enroll in
        CourseFixture(
            self.course_info['org'], self.course_info['number'],
            self.course_info['run'], self.course_info['display_name']
        ).install()

    def test_register_success(self):
        # Navigate to the registration page
        self.register_page.visit()

        # Fill in the form and submit it
        username = u"test_{uuid}".format(uuid=self.unique_id[0:6])
        email = u"{user}@example.com".format(user=username)
        self.register_page.register(
            email=email,
            password="password",
            username=username,
            full_name="Test User",
            country="US",
            favorite_movie="Mad Max: Fury Road"
        )

        # Expect that we reach the dashboard and we're auto-enrolled in the course
        course_names = self.dashboard_page.wait_for_page().available_courses
        self.assertIn(self.course_info["display_name"], course_names)

    def test_register_failure(self):
        # Navigate to the registration page
        self.register_page.visit()

        # Enter a blank for the username field, which is required
        # Don't agree to the terms of service / honor code.
        # Don't specify a country code, which is required.
        # Don't specify a favorite movie.
        username = u"test_{uuid}".format(uuid=self.unique_id[0:6])
        email = u"{user}@example.com".format(user=username)
        self.register_page.register(
            email=email,
            password="password",
            username="",
            full_name="Test User"
        )
        # Verify that the expected errors are displayed.
        errors = self.register_page.wait_for_errors()
        self.assertIn(u'Please enter your Public Username.', errors)
        self.assertIn(u'Select your country or region of residence.', errors)
        self.assertIn(u'Please tell us your favorite movie.', errors)

    def test_toggle_to_login_form(self):
        self.register_page.visit().toggle_form()
        self.assertEqual(self.register_page.current_form, "login")

    def test_third_party_register(self):
        """
        Test that we can register using third party credentials, and that the
        third party account gets linked to the edX account.
        """
        # Navigate to the register page
        self.register_page.visit()
        # Baseline screen-shots are different for chrome and firefox.
        #self.assertScreenshot('#register .login-providers', 'register-providers-{}'.format(self.browser.name), .25)
        # The line above is commented out temporarily see SOL-1937

        # Try to authenticate using the "Dummy" provider
        self.register_page.click_third_party_dummy_provider()

        # The user will be redirected somewhere and then back to the register page:
        msg_text = self.register_page.wait_for_auth_status_message()
        self.assertEqual(self.register_page.current_form, "register")
        self.assertIn("You've successfully signed into Dummy", msg_text)
        self.assertIn("We just need a little more information", msg_text)

        # Now the form should be pre-filled with the data from the Dummy provider:
        self.assertEqual(self.register_page.email_value, "adama@fleet.colonies.gov")
        self.assertEqual(self.register_page.full_name_value, "William Adama")
        self.assertIn("Galactica1", self.register_page.username_value)

        # Set country and submit the form:
        self.register_page.register(country="US", favorite_movie="Battlestar Galactica")

        # Expect that we reach the dashboard and we're auto-enrolled in the course
        course_names = self.dashboard_page.wait_for_page().available_courses
        self.assertIn(self.course_info["display_name"], course_names)

        # Now logout and check that we can log back in instantly (because the account is linked):
        LogoutPage(self.browser).visit()

        login_page = CombinedLoginAndRegisterPage(self.browser, start_page="login")
        login_page.visit()
        login_page.click_third_party_dummy_provider()

        self.dashboard_page.wait_for_page()

        # Now unlink the account (To test the account settings view and also to prevent cross-test side effects)
        account_settings = AccountSettingsPage(self.browser).visit()
        # switch to "Linked Accounts" tab
        account_settings.switch_account_settings_tabs('accounts-tab')

        field_id = "auth-oa2-dummy"
        account_settings.wait_for_field(field_id)
        self.assertEqual("Unlink This Account", account_settings.link_title_for_link_field(field_id))
        account_settings.click_on_link_in_link_field(field_id)
        account_settings.wait_for_message(field_id, "Successfully unlinked")


@attr(shard=19)
class PayAndVerifyTest(EventsTestMixin, UniqueCourseTest):
    """Test that we can proceed through the payment and verification flow."""
    def setUp(self):
        """Initialize the test.

        Create the necessary page objects, create a test course and configure its modes,
        create a user and log them in.
        """
        super(PayAndVerifyTest, self).setUp()

        self.payment_and_verification_flow = PaymentAndVerificationFlow(self.browser, self.course_id)
        self.immediate_verification_page = PaymentAndVerificationFlow(self.browser, self.course_id, entry_point='verify-now')
        self.upgrade_page = PaymentAndVerificationFlow(self.browser, self.course_id, entry_point='upgrade')
        self.fake_payment_page = FakePaymentPage(self.browser, self.course_id)
        self.dashboard_page = DashboardPage(self.browser)

        # Create a course
        CourseFixture(
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run'],
            self.course_info['display_name']
        ).install()

        # Add an honor mode to the course
        ModeCreationPage(self.browser, self.course_id).visit()

        # Add a verified mode to the course
        ModeCreationPage(self.browser, self.course_id, mode_slug=u'verified', mode_display_name=u'Verified Certificate', min_price=10, suggested_prices='10,20').visit()

    def test_deferred_verification_enrollment(self):
        # Create a user and log them in
        student_id = AutoAuthPage(self.browser).visit().get_user_id()

        enroll_user_track(self.browser, self.course_id, 'verified')

        # Navigate to the dashboard
        self.dashboard_page.visit()

        # Expect that we're enrolled as verified in the course
        enrollment_mode = self.dashboard_page.get_enrollment_mode(self.course_info["display_name"])
        self.assertEqual(enrollment_mode, 'verified')

    def test_enrollment_upgrade(self):
        # Create a user, log them in, and enroll them in the honor mode
        student_id = AutoAuthPage(self.browser, course_id=self.course_id).visit().get_user_id()

        # Navigate to the dashboard
        self.dashboard_page.visit()

        # Expect that we're enrolled as honor in the course
        enrollment_mode = self.dashboard_page.get_enrollment_mode(self.course_info["display_name"])
        self.assertEqual(enrollment_mode, 'honor')

        # Click the upsell button on the dashboard
        self.dashboard_page.upgrade_enrollment(self.course_info["display_name"], self.upgrade_page)

        # Select the first contribution option appearing on the page
        self.upgrade_page.indicate_contribution()

        # Proceed to the fake payment page
        self.upgrade_page.proceed_to_payment()

        def only_enrollment_events(event):
            """Filter out all non-enrollment events."""
            return event['event_type'].startswith('edx.course.enrollment.')

        expected_events = [
            {
                'event_type': 'edx.course.enrollment.mode_changed',
                'event': {
                    'user_id': int(student_id),
                    'mode': 'verified',
                }
            }
        ]

        with self.assert_events_match_during(event_filter=only_enrollment_events, expected_events=expected_events):
            # Submit payment
            self.fake_payment_page.submit_payment()

        # Navigate to the dashboard
        self.dashboard_page.visit()

        # Expect that we're enrolled as verified in the course
        enrollment_mode = self.dashboard_page.get_enrollment_mode(self.course_info["display_name"])
        self.assertEqual(enrollment_mode, 'verified')


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


@attr(shard=1)
class VisibleToStaffOnlyTest(UniqueCourseTest):
    """
    Tests that content with visible_to_staff_only set to True cannot be viewed by students.
    """
    def setUp(self):
        super(VisibleToStaffOnlyTest, self).setUp()

        course_fix = CourseFixture(
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run'],
            self.course_info['display_name']
        )

        course_fix.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Subsection With Locked Unit').add_children(
                    XBlockFixtureDesc('vertical', 'Locked Unit', metadata={'visible_to_staff_only': True}).add_children(
                        XBlockFixtureDesc('html', 'Html Child in locked unit', data="<html>Visible only to staff</html>"),
                    ),
                    XBlockFixtureDesc('vertical', 'Unlocked Unit').add_children(
                        XBlockFixtureDesc('html', 'Html Child in unlocked unit', data="<html>Visible only to all</html>"),
                    )
                ),
                XBlockFixtureDesc('sequential', 'Unlocked Subsection').add_children(
                    XBlockFixtureDesc('vertical', 'Test Unit').add_children(
                        XBlockFixtureDesc('html', 'Html Child in visible unit', data="<html>Visible to all</html>"),
                    )
                ),
                XBlockFixtureDesc('sequential', 'Locked Subsection', metadata={'visible_to_staff_only': True}).add_children(
                    XBlockFixtureDesc('vertical', 'Test Unit').add_children(
                        XBlockFixtureDesc(
                            'html', 'Html Child in locked subsection', data="<html>Visible only to staff</html>"
                        )
                    )
                )
            )
        ).install()

        self.course_home_page = CourseHomePage(self.browser, self.course_id)
        self.courseware_page = CoursewarePage(self.browser, self.course_id)

    def test_visible_to_student(self):
        """
        Scenario: Content marked 'visible_to_staff_only' is not visible for students in the course
            Given some of the course content has been marked 'visible_to_staff_only'
            And I am logged on with an authorized student account
            Then I can only see content without 'visible_to_staff_only' set to True
        """
        AutoAuthPage(self.browser, username="STUDENT_TESTER", email="johndoe_student@example.com",
                     course_id=self.course_id, staff=False).visit()

        self.course_home_page.visit()
        self.assertEqual(2, len(self.course_home_page.outline.sections['Test Section']))

        self.course_home_page.outline.go_to_section("Test Section", "Subsection With Locked Unit")
        self.courseware_page.wait_for_page()
        self.assertEqual([u'Unlocked Unit'], self.courseware_page.nav.sequence_items)

        self.course_home_page.visit()
        self.course_home_page.outline.go_to_section("Test Section", "Unlocked Subsection")
        self.courseware_page.wait_for_page()
        self.assertEqual([u'Test Unit'], self.courseware_page.nav.sequence_items)


@attr(shard=1)
class ProblemExecutionTest(UniqueCourseTest):
    """
    Tests of problems.
    """

    def setUp(self):
        """
        Initialize pages and install a course fixture.
        """
        super(ProblemExecutionTest, self).setUp()

        self.course_home_page = CourseHomePage(self.browser, self.course_id)
        self.tab_nav = TabNavPage(self.browser)

        # Install a course with sections and problems.
        course_fix = CourseFixture(
            self.course_info['org'], self.course_info['number'],
            self.course_info['run'], self.course_info['display_name']
        )

        course_fix.add_asset(['python_lib.zip'])

        course_fix.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc('problem', 'Python Problem', data=dedent(
                        """\
                        <problem>
                        <script type="loncapa/python">
                        from number_helpers import seventeen, fortytwo
                        oneseven = seventeen()

                        def check_function(expect, ans):
                            if int(ans) == fortytwo(-22):
                                return True
                            else:
                                return False
                        </script>

                        <p>What is the sum of $oneseven and 3?</p>

                        <customresponse expect="20" cfn="check_function">
                            <textline/>
                        </customresponse>
                        </problem>
                        """
                    ))
                )
            )
        ).install()

        # Auto-auth register for the course
        AutoAuthPage(self.browser, course_id=self.course_id).visit()

    def test_python_execution_in_problem(self):
        # Navigate to the problem page
        self.course_home_page.visit()
        self.course_home_page.outline.go_to_section('Test Section', 'Test Subsection')

        problem_page = ProblemPage(self.browser)
        self.assertEqual(problem_page.problem_name.upper(), 'PYTHON PROBLEM')

        # Does the page have computation results?
        self.assertIn("What is the sum of 17 and 3?", problem_page.problem_text)

        # Fill in the answer correctly.
        problem_page.fill_answer("20")
        problem_page.click_submit()
        self.assertTrue(problem_page.is_correct())

        # Fill in the answer incorrectly.
        problem_page.fill_answer("4")
        problem_page.click_submit()
        self.assertFalse(problem_page.is_correct())


@attr(shard=1)
class NotLiveRedirectTest(UniqueCourseTest):
    """
    Test that a banner is shown when the user is redirected to
    the dashboard from a non-live course.
    """

    def setUp(self):
        """Create a course that isn't live yet and enroll for it."""
        super(NotLiveRedirectTest, self).setUp()
        CourseFixture(
            self.course_info['org'], self.course_info['number'],
            self.course_info['run'], self.course_info['display_name'],
            start_date=datetime(year=2099, month=1, day=1)
        ).install()
        AutoAuthPage(self.browser, course_id=self.course_id).visit()

    def test_redirect_banner(self):
        """
        Navigate to the course info page, then check that we're on the
        dashboard page with the appropriate message.
        """
        url = BASE_URL + "/courses/" + self.course_id + "/" + 'info'
        self.browser.get(url)
        page = DashboardPage(self.browser)
        page.wait_for_page()
        self.assertIn(
            'The course you are looking for does not start until',
            page.banner_text
        )


@attr(shard=1)
class EnrollmentClosedRedirectTest(UniqueCourseTest):
    """
    Test that a banner is shown when the user is redirected to the
    dashboard after trying to view the track selection page for a
    course after enrollment has ended.
    """

    def setUp(self):
        """Create a course that is closed for enrollment, and sign in as a user."""
        super(EnrollmentClosedRedirectTest, self).setUp()
        course = CourseFixture(
            self.course_info['org'], self.course_info['number'],
            self.course_info['run'], self.course_info['display_name']
        )
        now = datetime.now(pytz.UTC)
        course.add_course_details({
            'enrollment_start': (now - timedelta(days=30)).isoformat(),
            'enrollment_end': (now - timedelta(days=1)).isoformat()
        })
        course.install()

        # Add an honor mode to the course
        ModeCreationPage(self.browser, self.course_id).visit()

        # Add a verified mode to the course
        ModeCreationPage(
            self.browser,
            self.course_id,
            mode_slug=u'verified',
            mode_display_name=u'Verified Certificate',
            min_price=10,
            suggested_prices='10,20'
        ).visit()

    def _assert_dashboard_message(self):
        """
        Assert that the 'closed for enrollment' text is present on the
        dashboard.
        """
        page = DashboardPage(self.browser)
        page.wait_for_page()
        self.assertIn(
            'The course you are looking for is closed for enrollment',
            page.banner_text
        )

    def test_redirect_banner(self):
        """
        Navigate to the course info page, then check that we're on the
        dashboard page with the appropriate message.
        """
        AutoAuthPage(self.browser).visit()
        url = BASE_URL + "/course_modes/choose/" + self.course_id
        self.browser.get(url)
        self._assert_dashboard_message()


@attr(shard=19)
class RegisterCourseTests(EventsTestMixin, UniqueCourseTest):
    """Test that learner can enroll into a course from courses page"""

    TEST_INDEX_FILENAME = "test_root/index_file.dat"

    def setUp(self):
        """
        Initialize the test.

        Create the necessary page objects, create course page and courses to find.
        """
        super(RegisterCourseTests, self).setUp()

        # create test file in which index for this test will live
        with open(self.TEST_INDEX_FILENAME, "w+") as index_file:
            json.dump({}, index_file)
        self.addCleanup(remove_file, self.TEST_INDEX_FILENAME)

        self.course_discovery = CourseDiscoveryPage(self.browser)
        self.dashboard_page = DashboardPage(self.browser)
        self.course_about = CourseAboutPage(self.browser, self.course_id)

        # Create a course
        CourseFixture(
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run'],
            self.course_info['display_name'],
            settings={'enrollment_start': datetime(1970, 1, 1).isoformat()}
        ).install()

        # Create a user and log them in
        AutoAuthPage(self.browser).visit()

    def test_register_for_course(self):
        """
        Scenario: I can register for a course
        Given The course "6.002x" exists
            And I am logged in
            And I visit the courses page
        When I register for the course "6.002x"
            Then I should see the course numbered "6.002x" in my dashboard
            And a "edx.course.enrollment.activated" server event is emitted
        """
        # Navigate to the dashboard
        self.course_discovery.visit()
        self.course_discovery.click_course(self.course_id)
        self.course_about.wait_for_page()
        self.course_about.enroll_in_course()
        self.dashboard_page.wait_for_page()
        self.assertTrue(self.dashboard_page.is_course_present(self.course_id))
        self.assert_matching_events_were_emitted(
            event_filter={'name': u'edx.course.enrollment.activated', 'event_source': 'server'}
        )
