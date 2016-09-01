# -*- coding: utf-8 -*-
"""
End-to-end tests for the LMS.
"""
from datetime import datetime, timedelta
from flaky import flaky
from textwrap import dedent
from unittest import skip
from nose.plugins.attrib import attr
import pytz
import urllib

from bok_choy.promise import EmptyPromise
from common.test.acceptance.tests.helpers import (
    UniqueCourseTest,
    EventsTestMixin,
    load_data_str,
    generate_course_key,
    select_option_by_value,
    element_has_text,
    select_option_by_text,
    get_selected_option_text
)
from common.test.acceptance.pages.lms import BASE_URL
from common.test.acceptance.pages.lms.account_settings import AccountSettingsPage
from common.test.acceptance.pages.lms.auto_auth import AutoAuthPage
from common.test.acceptance.pages.lms.create_mode import ModeCreationPage
from common.test.acceptance.pages.common.logout import LogoutPage
from common.test.acceptance.pages.lms.course_info import CourseInfoPage
from common.test.acceptance.pages.lms.tab_nav import TabNavPage
from common.test.acceptance.pages.lms.course_nav import CourseNavPage
from common.test.acceptance.pages.lms.progress import ProgressPage
from common.test.acceptance.pages.lms.dashboard import DashboardPage
from common.test.acceptance.pages.lms.problem import ProblemPage
from common.test.acceptance.pages.lms.video.video import VideoPage
from common.test.acceptance.pages.lms.courseware import CoursewarePage
from common.test.acceptance.pages.studio.settings import SettingsPage
from common.test.acceptance.pages.lms.login_and_register import CombinedLoginAndRegisterPage, ResetPasswordPage
from common.test.acceptance.pages.lms.track_selection import TrackSelectionPage
from common.test.acceptance.pages.lms.pay_and_verify import PaymentAndVerificationFlow, FakePaymentPage
from common.test.acceptance.pages.lms.course_wiki import CourseWikiPage, CourseWikiEditPage
from common.test.acceptance.fixtures.course import CourseFixture, XBlockFixtureDesc, CourseUpdateDesc


@attr(shard=8)
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
        self.assertIn("Password Reset Email Sent", self.reset_password_page.get_success_message())


@attr(shard=8)
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

    @flaky  # ECOM-1165
    def test_password_reset_success(self):
        # Create a user account
        email, password = self._create_unique_user()  # pylint: disable=unused-variable

        # Navigate to the password reset form and try to submit it
        self.login_page.visit().password_reset(email=email)

        # Expect that we're shown a success message
        self.assertIn("Password Reset Email Sent", self.login_page.wait_for_success())

    def test_password_reset_no_user(self):
        # Navigate to the password reset form
        self.login_page.visit()

        # User account does not exist
        self.login_page.password_reset(email="nobody@nowhere.com")

        # Expect that we're shown a success message
        self.assertIn("Password Reset Email Sent", self.login_page.wait_for_success())

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
        self.assertIn("To link your accounts, sign in now using your edX password", msg_text)

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
        username = "test_{uuid}".format(uuid=self.unique_id[0:6])
        email = "{user}@example.com".format(user=username)
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


@attr(shard=8)
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
        username = "test_{uuid}".format(uuid=self.unique_id[0:6])
        email = "{user}@example.com".format(user=username)
        self.register_page.register(
            email=email,
            password="password",
            username=username,
            full_name="Test User",
            country="US",
            favorite_movie="Mad Max: Fury Road",
            terms_of_service=True
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
        username = "test_{uuid}".format(uuid=self.unique_id[0:6])
        email = "{user}@example.com".format(user=username)
        self.register_page.register(
            email=email,
            password="password",
            username="",
            full_name="Test User",
            terms_of_service=False
        )

        # Verify that the expected errors are displayed.
        errors = self.register_page.wait_for_errors()
        self.assertIn(u'Please enter your Public username.', errors)
        self.assertIn(u'You must agree to the edX Terms of Service and Honor Code', errors)
        self.assertIn(u'Please select your Country.', errors)
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

        # Set country, accept the terms, and submit the form:
        self.register_page.register(country="US", favorite_movie="Battlestar Galactica", terms_of_service=True)

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


@attr(shard=8)
class PayAndVerifyTest(EventsTestMixin, UniqueCourseTest):
    """Test that we can proceed through the payment and verification flow."""
    def setUp(self):
        """Initialize the test.

        Create the necessary page objects, create a test course and configure its modes,
        create a user and log them in.
        """
        super(PayAndVerifyTest, self).setUp()

        self.track_selection_page = TrackSelectionPage(self.browser, self.course_id)
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

    @skip("Flaky 02/02/2015")
    def test_immediate_verification_enrollment(self):
        # Create a user and log them in
        student_id = AutoAuthPage(self.browser).visit().get_user_id()

        # Navigate to the track selection page
        self.track_selection_page.visit()

        # Enter the payment and verification flow by choosing to enroll as verified
        self.track_selection_page.enroll('verified')

        # Proceed to the fake payment page
        self.payment_and_verification_flow.proceed_to_payment()

        # Submit payment
        self.fake_payment_page.submit_payment()

        # Proceed to verification
        self.payment_and_verification_flow.immediate_verification()

        # Take face photo and proceed to the ID photo step
        self.payment_and_verification_flow.webcam_capture()
        self.payment_and_verification_flow.next_verification_step(self.immediate_verification_page)

        # Take ID photo and proceed to the review photos step
        self.payment_and_verification_flow.webcam_capture()
        self.payment_and_verification_flow.next_verification_step(self.immediate_verification_page)

        # Submit photos and proceed to the enrollment confirmation step
        self.payment_and_verification_flow.next_verification_step(self.immediate_verification_page)

        # Navigate to the dashboard
        self.dashboard_page.visit()

        # Expect that we're enrolled as verified in the course
        enrollment_mode = self.dashboard_page.get_enrollment_mode(self.course_info["display_name"])
        self.assertEqual(enrollment_mode, 'verified')

    def test_deferred_verification_enrollment(self):
        # Create a user and log them in
        student_id = AutoAuthPage(self.browser).visit().get_user_id()

        # Navigate to the track selection page
        self.track_selection_page.visit()

        # Enter the payment and verification flow by choosing to enroll as verified
        self.track_selection_page.enroll('verified')

        # Proceed to the fake payment page
        self.payment_and_verification_flow.proceed_to_payment()

        # Submit payment
        self.fake_payment_page.submit_payment()

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


@attr(shard=1)
class CourseWikiTest(UniqueCourseTest):
    """
    Tests that verify the course wiki.
    """

    def setUp(self):
        """
        Initialize pages and install a course fixture.
        """
        super(CourseWikiTest, self).setUp()

        # self.course_info['number'] must be shorter since we are accessing the wiki. See TNL-1751
        self.course_info['number'] = self.unique_id[0:6]

        self.course_info_page = CourseInfoPage(self.browser, self.course_id)
        self.course_wiki_page = CourseWikiPage(self.browser, self.course_id)
        self.course_info_page = CourseInfoPage(self.browser, self.course_id)
        self.course_wiki_edit_page = CourseWikiEditPage(self.browser, self.course_id, self.course_info)
        self.tab_nav = TabNavPage(self.browser)

        CourseFixture(
            self.course_info['org'], self.course_info['number'],
            self.course_info['run'], self.course_info['display_name']
        ).install()

        # Auto-auth register for the course
        AutoAuthPage(self.browser, course_id=self.course_id).visit()

        # Access course wiki page
        self.course_info_page.visit()
        self.tab_nav.go_to_tab('Wiki')

    def _open_editor(self):
        self.course_wiki_page.open_editor()
        self.course_wiki_edit_page.wait_for_page()

    def test_edit_course_wiki(self):
        """
        Wiki page by default is editable for students.

        After accessing the course wiki,
        Replace the content of the default page
        Confirm new content has been saved

        """
        content = "hello"
        self._open_editor()
        self.course_wiki_edit_page.replace_wiki_content(content)
        self.course_wiki_edit_page.save_wiki_content()
        actual_content = unicode(self.course_wiki_page.q(css='.wiki-article p').text[0])
        self.assertEqual(content, actual_content)


@attr(shard=1)
class HighLevelTabTest(UniqueCourseTest):
    """
    Tests that verify each of the high-level tabs available within a course.
    """

    def setUp(self):
        """
        Initialize pages and install a course fixture.
        """
        super(HighLevelTabTest, self).setUp()

        # self.course_info['number'] must be shorter since we are accessing the wiki. See TNL-1751
        self.course_info['number'] = self.unique_id[0:6]

        self.course_info_page = CourseInfoPage(self.browser, self.course_id)
        self.progress_page = ProgressPage(self.browser, self.course_id)
        self.course_nav = CourseNavPage(self.browser)
        self.tab_nav = TabNavPage(self.browser)
        self.video = VideoPage(self.browser)

        # Install a course with sections/problems, tabs, updates, and handouts
        course_fix = CourseFixture(
            self.course_info['org'], self.course_info['number'],
            self.course_info['run'], self.course_info['display_name']
        )

        course_fix.add_update(
            CourseUpdateDesc(date='January 29, 2014', content='Test course update1')
        )

        course_fix.add_handout('demoPDF.pdf')

        course_fix.add_children(
            XBlockFixtureDesc('static_tab', 'Test Static Tab', data=r"static tab data with mathjax \(E=mc^2\)"),
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc('problem', 'Test Problem 1', data=load_data_str('multiple_choice.xml')),
                    XBlockFixtureDesc('problem', 'Test Problem 2', data=load_data_str('formula_problem.xml')),
                    XBlockFixtureDesc('html', 'Test HTML'),
                )
            ),
            XBlockFixtureDesc('chapter', 'Test Section 2').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection 2'),
                XBlockFixtureDesc('sequential', 'Test Subsection 3'),
            )
        ).install()

        # Auto-auth register for the course
        AutoAuthPage(self.browser, course_id=self.course_id).visit()

    def test_course_info(self):
        """
        Navigate to the course info page.
        """

        # Navigate to the course info page from the progress page
        self.progress_page.visit()
        self.tab_nav.go_to_tab('Home')

        # Expect just one update
        self.assertEqual(self.course_info_page.num_updates, 1)

        # Expect a link to the demo handout pdf
        handout_links = self.course_info_page.handout_links
        self.assertEqual(len(handout_links), 1)
        self.assertIn('demoPDF.pdf', handout_links[0])

    def test_progress(self):
        """
        Navigate to the progress page.
        """
        # Navigate to the progress page from the info page
        self.course_info_page.visit()
        self.tab_nav.go_to_tab('Progress')

        # We haven't answered any problems yet, so assume scores are zero
        # Only problems should have scores; so there should be 2 scores.
        CHAPTER = 'Test Section'
        SECTION = 'Test Subsection'
        EXPECTED_SCORES = [(0, 3), (0, 1)]

        actual_scores = self.progress_page.scores(CHAPTER, SECTION)
        self.assertEqual(actual_scores, EXPECTED_SCORES)

    def test_static_tab(self):
        """
        Navigate to a static tab (course content)
        """
        # From the course info page, navigate to the static tab
        self.course_info_page.visit()
        self.tab_nav.go_to_tab('Test Static Tab')
        self.assertTrue(self.tab_nav.is_on_tab('Test Static Tab'))

    def test_static_tab_with_mathjax(self):
        """
        Navigate to a static tab (course content)
        """
        # From the course info page, navigate to the static tab
        self.course_info_page.visit()
        self.tab_nav.go_to_tab('Test Static Tab')
        self.assertTrue(self.tab_nav.is_on_tab('Test Static Tab'))

        # Verify that Mathjax has rendered
        self.tab_nav.mathjax_has_rendered()

    def test_wiki_tab_first_time(self):
        """
        Navigate to the course wiki tab. When the wiki is accessed for
        the first time, it is created on the fly.
        """

        course_wiki = CourseWikiPage(self.browser, self.course_id)
        # From the course info page, navigate to the wiki tab
        self.course_info_page.visit()
        self.tab_nav.go_to_tab('Wiki')
        self.assertTrue(self.tab_nav.is_on_tab('Wiki'))

        # Assert that a default wiki is created
        expected_article_name = "{org}.{course_number}.{course_run}".format(
            org=self.course_info['org'],
            course_number=self.course_info['number'],
            course_run=self.course_info['run']
        )
        self.assertEqual(expected_article_name, course_wiki.article_name)

    def test_courseware_nav(self):
        """
        Navigate to a particular unit in the course.
        """
        # Navigate to the course page from the info page
        self.course_info_page.visit()
        self.tab_nav.go_to_tab('Course')

        # Check that the course navigation appears correctly
        EXPECTED_SECTIONS = {
            'Test Section': ['Test Subsection'],
            'Test Section 2': ['Test Subsection 2', 'Test Subsection 3']
        }

        actual_sections = self.course_nav.sections
        for section, subsections in EXPECTED_SECTIONS.iteritems():
            self.assertIn(section, actual_sections)
            self.assertEqual(actual_sections[section], EXPECTED_SECTIONS[section])

        # Navigate to a particular section
        self.course_nav.go_to_section('Test Section', 'Test Subsection')

        # Check the sequence items
        EXPECTED_ITEMS = ['Test Problem 1', 'Test Problem 2', 'Test HTML']

        actual_items = self.course_nav.sequence_items
        self.assertEqual(len(actual_items), len(EXPECTED_ITEMS))
        for expected in EXPECTED_ITEMS:
            self.assertIn(expected, actual_items)


@attr(shard=1)
class PDFTextBooksTabTest(UniqueCourseTest):
    """
    Tests that verify each of the textbook tabs available within a course.
    """

    def setUp(self):
        """
        Initialize pages and install a course fixture.
        """
        super(PDFTextBooksTabTest, self).setUp()

        self.course_info_page = CourseInfoPage(self.browser, self.course_id)
        self.tab_nav = TabNavPage(self.browser)

        # Install a course with TextBooks
        course_fix = CourseFixture(
            self.course_info['org'], self.course_info['number'],
            self.course_info['run'], self.course_info['display_name']
        )

        # Add PDF textbooks to course fixture.
        for i in range(1, 3):
            course_fix.add_textbook("PDF Book {}".format(i), [{"title": "Chapter Of Book {}".format(i), "url": ""}])

        course_fix.install()

        # Auto-auth register for the course
        AutoAuthPage(self.browser, course_id=self.course_id).visit()

    def test_verify_textbook_tabs(self):
        """
        Test multiple pdf textbooks loads correctly in lms.
        """
        self.course_info_page.visit()

        # Verify each PDF textbook tab by visiting, it will fail if correct tab is not loaded.
        for i in range(1, 3):
            self.tab_nav.go_to_tab("PDF Book {}".format(i))


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

        self.courseware_page = CoursewarePage(self.browser, self.course_id)
        self.course_nav = CourseNavPage(self.browser)

    def test_visible_to_staff(self):
        """
        Scenario: All content is visible for a user marked is_staff (different from course staff)
            Given some of the course content has been marked 'visible_to_staff_only'
            And I am logged on with an account marked 'is_staff'
            Then I can see all course content
        """
        AutoAuthPage(self.browser, username="STAFF_TESTER", email="johndoe_staff@example.com",
                     course_id=self.course_id, staff=True).visit()

        self.courseware_page.visit()
        self.assertEqual(3, len(self.course_nav.sections['Test Section']))

        self.course_nav.go_to_section("Test Section", "Subsection With Locked Unit")
        self.assertEqual([u'Locked Unit', u'Unlocked Unit'], self.course_nav.sequence_items)

        self.course_nav.go_to_section("Test Section", "Unlocked Subsection")
        self.assertEqual([u'Test Unit'], self.course_nav.sequence_items)

        self.course_nav.go_to_section("Test Section", "Locked Subsection")
        self.assertEqual([u'Test Unit'], self.course_nav.sequence_items)

    def test_visible_to_student(self):
        """
        Scenario: Content marked 'visible_to_staff_only' is not visible for students in the course
            Given some of the course content has been marked 'visible_to_staff_only'
            And I am logged on with an authorized student account
            Then I can only see content without 'visible_to_staff_only' set to True
        """
        AutoAuthPage(self.browser, username="STUDENT_TESTER", email="johndoe_student@example.com",
                     course_id=self.course_id, staff=False).visit()

        self.courseware_page.visit()
        self.assertEqual(2, len(self.course_nav.sections['Test Section']))

        self.course_nav.go_to_section("Test Section", "Subsection With Locked Unit")
        self.assertEqual([u'Unlocked Unit'], self.course_nav.sequence_items)

        self.course_nav.go_to_section("Test Section", "Unlocked Subsection")
        self.assertEqual([u'Test Unit'], self.course_nav.sequence_items)


@attr(shard=1)
class TooltipTest(UniqueCourseTest):
    """
    Tests that tooltips are displayed
    """

    def setUp(self):
        """
        Initialize pages and install a course fixture.
        """
        super(TooltipTest, self).setUp()

        self.course_info_page = CourseInfoPage(self.browser, self.course_id)
        self.tab_nav = TabNavPage(self.browser)

        course_fix = CourseFixture(
            self.course_info['org'], self.course_info['number'],
            self.course_info['run'], self.course_info['display_name']
        )

        course_fix.add_children(
            XBlockFixtureDesc('static_tab', 'Test Static Tab'),
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc('problem', 'Test Problem 1', data=load_data_str('multiple_choice.xml')),
                    XBlockFixtureDesc('problem', 'Test Problem 2', data=load_data_str('formula_problem.xml')),
                    XBlockFixtureDesc('html', 'Test HTML'),
                )
            )
        ).install()

        self.courseware_page = CoursewarePage(self.browser, self.course_id)
        # Auto-auth register for the course
        AutoAuthPage(self.browser, course_id=self.course_id).visit()

    def test_tooltip(self):
        """
        Verify that tooltips are displayed when you hover over the sequence nav bar.
        """
        self.course_info_page.visit()
        self.tab_nav.go_to_tab('Course')

        self.courseware_page.verify_tooltips_displayed()


@attr(shard=1)
class PreRequisiteCourseTest(UniqueCourseTest):
    """
    Tests that pre-requisite course messages are displayed
    """

    def setUp(self):
        """
        Initialize pages and install a course fixture.
        """
        super(PreRequisiteCourseTest, self).setUp()

        CourseFixture(
            self.course_info['org'], self.course_info['number'],
            self.course_info['run'], self.course_info['display_name']
        ).install()

        self.prc_info = {
            'org': 'test_org',
            'number': self.unique_id,
            'run': 'prc_test_run',
            'display_name': 'PR Test Course' + self.unique_id
        }

        CourseFixture(
            self.prc_info['org'], self.prc_info['number'],
            self.prc_info['run'], self.prc_info['display_name']
        ).install()

        pre_requisite_course_key = generate_course_key(
            self.prc_info['org'],
            self.prc_info['number'],
            self.prc_info['run']
        )
        self.pre_requisite_course_id = unicode(pre_requisite_course_key)

        self.dashboard_page = DashboardPage(self.browser)
        self.settings_page = SettingsPage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']

        )
        # Auto-auth register for the course
        AutoAuthPage(self.browser, course_id=self.course_id).visit()

    def test_dashboard_message(self):
        """
         Scenario: Any course where there is a Pre-Requisite course Student dashboard should have
         appropriate messaging.
            Given that I am on the Student dashboard
            When I view a course with a pre-requisite course set
            Then At the bottom of course I should see course requirements message.'
        """

        # visit dashboard page and make sure there is not pre-requisite course message
        self.dashboard_page.visit()
        self.assertFalse(self.dashboard_page.pre_requisite_message_displayed())

        # Logout and login as a staff.
        LogoutPage(self.browser).visit()
        AutoAuthPage(self.browser, course_id=self.course_id, staff=True).visit()

        # visit course settings page and set pre-requisite course
        self.settings_page.visit()
        self._set_pre_requisite_course()

        # Logout and login as a student.
        LogoutPage(self.browser).visit()
        AutoAuthPage(self.browser, course_id=self.course_id, staff=False).visit()

        # visit dashboard page again now it should have pre-requisite course message
        self.dashboard_page.visit()
        EmptyPromise(lambda: self.dashboard_page.available_courses > 0, 'Dashboard page loaded').fulfill()
        self.assertTrue(self.dashboard_page.pre_requisite_message_displayed())

    def _set_pre_requisite_course(self):
        """
        set pre-requisite course
        """
        select_option_by_value(self.settings_page.pre_requisite_course_options, self.pre_requisite_course_id)
        self.settings_page.save_changes()


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

        self.course_info_page = CourseInfoPage(self.browser, self.course_id)
        self.course_nav = CourseNavPage(self.browser)
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
        self.course_info_page.visit()
        self.tab_nav.go_to_tab('Course')
        self.course_nav.go_to_section('Test Section', 'Test Subsection')

        problem_page = ProblemPage(self.browser)
        self.assertEqual(problem_page.problem_name.upper(), 'PYTHON PROBLEM')

        # Does the page have computation results?
        self.assertIn("What is the sum of 17 and 3?", problem_page.problem_text)

        # Fill in the answer correctly.
        problem_page.fill_answer("20")
        problem_page.click_check()
        self.assertTrue(problem_page.is_correct())

        # Fill in the answer incorrectly.
        problem_page.fill_answer("4")
        problem_page.click_check()
        self.assertFalse(problem_page.is_correct())


@attr(shard=1)
class EntranceExamTest(UniqueCourseTest):
    """
    Tests that course has an entrance exam.
    """

    def setUp(self):
        """
        Initialize pages and install a course fixture.
        """
        super(EntranceExamTest, self).setUp()

        CourseFixture(
            self.course_info['org'], self.course_info['number'],
            self.course_info['run'], self.course_info['display_name']
        ).install()

        self.courseware_page = CoursewarePage(self.browser, self.course_id)
        self.settings_page = SettingsPage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

        # Auto-auth register for the course
        AutoAuthPage(self.browser, course_id=self.course_id).visit()

    def test_entrance_exam_section(self):
        """
         Scenario: Any course that is enabled for an entrance exam, should have entrance exam chapter at course
         page.
            Given that I am on the course page
            When I view the course that has an entrance exam
            Then there should be an "Entrance Exam" chapter.'
        """
        entrance_exam_link_selector = '.accordion .course-navigation .chapter .group-heading'
        # visit course page and make sure there is not entrance exam chapter.
        self.courseware_page.visit()
        self.courseware_page.wait_for_page()
        self.assertFalse(element_has_text(
            page=self.courseware_page,
            css_selector=entrance_exam_link_selector,
            text='Entrance Exam'
        ))

        # Logout and login as a staff.
        LogoutPage(self.browser).visit()
        AutoAuthPage(self.browser, course_id=self.course_id, staff=True).visit()

        # visit course settings page and set/enabled entrance exam for that course.
        self.settings_page.visit()
        self.settings_page.wait_for_page()
        self.assertTrue(self.settings_page.is_browser_on_page())
        self.settings_page.entrance_exam_field.click()
        self.settings_page.save_changes()

        # Logout and login as a student.
        LogoutPage(self.browser).visit()
        AutoAuthPage(self.browser, course_id=self.course_id, staff=False).visit()

        # visit course info page and make sure there is an "Entrance Exam" section.
        self.courseware_page.visit()
        self.courseware_page.wait_for_page()
        self.assertTrue(element_has_text(
            page=self.courseware_page,
            css_selector=entrance_exam_link_selector,
            text='Entrance Exam'
        ))


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

    def test_login_redirect(self):
        """
        Test that the user is correctly redirected after logistration when
        attempting to enroll in a closed course.
        """
        url = '{base_url}/register?{params}'.format(
            base_url=BASE_URL,
            params=urllib.urlencode({
                'course_id': self.course_id,
                'enrollment_action': 'enroll',
                'email_opt_in': 'false'
            })
        )
        self.browser.get(url)
        register_page = CombinedLoginAndRegisterPage(
            self.browser,
            start_page="register",
            course_id=self.course_id
        )
        register_page.wait_for_page()
        register_page.register(
            email="email@example.com",
            password="password",
            username="username",
            full_name="Test User",
            country="US",
            favorite_movie="Mad Max: Fury Road",
            terms_of_service=True
        )
        self._assert_dashboard_message()


@attr(shard=1)
class LMSLanguageTest(UniqueCourseTest):
    """ Test suite for the LMS Language """
    def setUp(self):
        super(LMSLanguageTest, self).setUp()
        self.dashboard_page = DashboardPage(self.browser)
        self.account_settings = AccountSettingsPage(self.browser)
        AutoAuthPage(self.browser).visit()

    def test_lms_language_change(self):
        """
        Scenario: Ensure that language selection is working fine.
        First I go to the user dashboard page in LMS. I can see 'English' is selected by default.
        Then I choose 'Dummy Language' from drop down (at top of the page).
        Then I visit the student account settings page and I can see the language has been updated to 'Dummy Language'
        in both drop downs.
        After that I select the 'English' language and visit the dashboard page again.
        Then I can see that top level language selector persist its value to 'English'.
        """
        self.dashboard_page.visit()
        language_selector = self.dashboard_page.language_selector
        self.assertEqual(
            get_selected_option_text(language_selector),
            u'English'
        )

        select_option_by_text(language_selector, 'Dummy Language (Esperanto)')
        self.dashboard_page.wait_for_ajax()
        self.account_settings.visit()
        self.assertEqual(self.account_settings.value_for_dropdown_field('pref-lang'), u'Dummy Language (Esperanto)')
        self.assertEqual(
            get_selected_option_text(language_selector),
            u'Dummy Language (Esperanto)'
        )

        # changed back to English language.
        select_option_by_text(language_selector, 'English')
        self.account_settings.wait_for_ajax()
        self.assertEqual(self.account_settings.value_for_dropdown_field('pref-lang'), u'English')

        self.dashboard_page.visit()
        self.assertEqual(
            get_selected_option_text(language_selector),
            u'English'
        )


@attr('a11y')
class CourseInfoA11yTest(UniqueCourseTest):
    """Accessibility test for course home/info page."""

    def setUp(self):
        super(CourseInfoA11yTest, self).setUp()
        self.course_fixture = CourseFixture(
            self.course_info['org'], self.course_info['number'],
            self.course_info['run'], self.course_info['display_name']
        )
        self.course_fixture.add_update(
            CourseUpdateDesc(date='January 29, 2014', content='Test course update1')
        )
        self.course_fixture.add_update(
            CourseUpdateDesc(date='February 5th, 2014', content='Test course update2')
        )
        self.course_fixture.add_update(
            CourseUpdateDesc(date='March 31st, 2014', content='Test course update3')
        )
        self.course_fixture.install()
        self.course_info_page = CourseInfoPage(self.browser, self.course_id)
        AutoAuthPage(self.browser, course_id=self.course_id).visit()

    def test_course_home_a11y(self):
        self.course_info_page.visit()
        self.course_info_page.a11y_audit.check_for_accessibility_errors()
