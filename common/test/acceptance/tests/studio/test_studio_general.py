"""
Acceptance tests for Studio.
"""
import uuid

from selenium.webdriver.common.keys import Keys

from base_studio_test import StudioCourseTest
from common.test.acceptance.fixtures.course import CourseFixture, XBlockFixtureDesc
from common.test.acceptance.pages.common.auto_auth import AutoAuthPage
from common.test.acceptance.pages.studio import LMS_URL
from common.test.acceptance.pages.studio.asset_index import AssetIndexPageStudioFrontend
from common.test.acceptance.pages.studio.course_info import CourseUpdatesPage
from common.test.acceptance.pages.studio.edit_tabs import PagesPage
from common.test.acceptance.pages.studio.import_export import ExportCoursePage, ImportCoursePage
from common.test.acceptance.pages.studio.index import DashboardPage, HomePage, IndexPage, AccessibilityPage
from common.test.acceptance.pages.studio.login import CourseOutlineSignInRedirectPage, LoginPage
from common.test.acceptance.pages.studio.overview import CourseOutlinePage
from common.test.acceptance.pages.studio.settings import SettingsPage
from common.test.acceptance.pages.studio.settings_advanced import AdvancedSettingsPage
from common.test.acceptance.pages.studio.settings_graders import GradingPage
from common.test.acceptance.pages.studio.signup import SignupPage
from common.test.acceptance.pages.studio.textbook_upload import TextbookUploadPage
from common.test.acceptance.pages.studio.users import CourseTeamPage
from common.test.acceptance.tests.helpers import AcceptanceTest, UniqueCourseTest


class LoggedOutTest(AcceptanceTest):
    """
    Smoke test for pages in Studio that are visible when logged out.
    """
    shard = 21

    def setUp(self):
        super(LoggedOutTest, self).setUp()
        self.pages = [LoginPage(self.browser), IndexPage(self.browser), SignupPage(self.browser),
                      AccessibilityPage(self.browser)]

    def test_page_existence(self):
        """
        Make sure that all the pages are accessible.
        Rather than fire up the browser just to check each url,
        do them all sequentially in this testcase.
        """
        for page in self.pages:
            page.visit()


class LoggedInPagesTest(AcceptanceTest):
    """
    Verify the pages in Studio that you can get to when logged in and do not have a course yet.
    """
    shard = 21

    def setUp(self):
        super(LoggedInPagesTest, self).setUp()
        self.auth_page = AutoAuthPage(self.browser, staff=True)
        self.dashboard_page = DashboardPage(self.browser)
        self.home_page = HomePage(self.browser)

    def test_logged_in_no_courses(self):
        """
        Make sure that you can get to the dashboard and home pages without a course.
        """
        self.auth_page.visit()
        self.dashboard_page.visit()
        self.home_page.visit()


class SignUpAndSignInTest(UniqueCourseTest):
    """
    Test studio sign-up and sign-in
    """
    shard = 21

    def setUp(self):
        super(SignUpAndSignInTest, self).setUp()
        self.sign_up_page = SignupPage(self.browser)
        self.login_page = LoginPage(self.browser)

        self.course_outline_page = CourseOutlinePage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )
        self.course_outline_sign_in_redirect_page = CourseOutlineSignInRedirectPage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

        self.course_fixture = CourseFixture(
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run'],
            self.course_info['display_name'],
        )
        self.user = None

    def install_course_fixture(self):
        """
        Install a course fixture
        """
        self.course_fixture.install()
        self.user = self.course_fixture.user

    def test_sign_up_from_home(self):
        """
        Scenario: Sign up from the homepage
        Given I visit the Studio homepage
        When I click the link with the text "Sign Up"
        And I fill in the registration form
        And I press the Create My Account button on the registration form
        Then I should see an email verification prompt
        """
        index_page = IndexPage(self.browser)
        index_page.visit()
        index_page.click_sign_up()

        # Register the user.
        unique_number = uuid.uuid4().hex[:4]
        self.sign_up_page.sign_up_user(
            '{}-email@host.com'.format(unique_number),
            '{}-name'.format(unique_number),
            '{}-username'.format(unique_number),
            '{}-password'.format(unique_number),
        )
        home = HomePage(self.browser)
        home.wait_for_page()

    def test_sign_up_with_bad_password(self):
        """
        Scenario: Sign up from the homepage
        Given I visit the Studio homepage
        When I click the link with the text "Sign Up"
        And I fill in the registration form
        When I enter an insufficient password and focus out
        I should see an error message
        """
        index_page = IndexPage(self.browser)
        index_page.visit()
        index_page.click_sign_up()

        password_input = self.sign_up_page.input_password('a')  # Arbitrary short password that will fail
        password_input.send_keys(Keys.TAB)  # Focus out of the element
        index_page.wait_for_element_visibility('#register-password-validation-error', 'Password Error Message')
        self.assertIsNotNone(index_page.q(css='#register-password-validation-error-msg'))  # Error message should exist

    def test_login_with_valid_redirect(self):
        """
        Scenario: Login with a valid redirect
        Given I have opened a new course in Studio
        And I am not logged in
        And I visit the url "/course/slashes:MITx+999+Robot_Super_Course"
        And I should see that the path is "/signin?next=/course/slashes%3AMITx%2B999%2BRobot_Super_Course"
        When I fill in and submit the signin form
        Then I should see that the path is "/course/slashes:MITx+999+Robot_Super_Course"
        """
        self.install_course_fixture()
        # Get the url, browser should land here after sign in.
        course_url = self.course_outline_sign_in_redirect_page.url
        self.course_outline_sign_in_redirect_page.visit()
        # Login
        self.course_outline_sign_in_redirect_page.login(self.user['email'], self.user['password'])
        self.course_outline_page.wait_for_page()
        # Verify that correct course is displayed after sign in.
        self.assertEqual(self.browser.current_url, course_url)

    def test_login_with_invalid_redirect(self):
        """
        Scenario: Login with an invalid redirect
        Given I have opened a new course in Studio
        And I am not logged in
        And I visit the url "/signin?next=http://www.google.com/"
        When I fill in and submit the signin form
        Then I should see that the path is "/home/"
        """
        self.install_course_fixture()
        # Visit course
        self.course_outline_sign_in_redirect_page.visit()
        # Change redirect url
        self.browser.get(self.browser.current_url.split('=')[0] + '=http://www.google.com')
        # Login
        self.course_outline_sign_in_redirect_page.login(self.user['email'], self.user['password'])
        # Verify that we land in LMS instead of the invalid redirect url
        self.assertEqual(self.browser.current_url, LMS_URL + "/dashboard")

    def test_login_with_mistyped_credentials(self):
        """
        Given I have opened a new course in Studio
        And I am not logged in
        And I visit the Studio homepage
        When I click the link with the text "Sign In"
        Then I should see that the path is "/signin"
        And I should not see a login error message
        And I fill in and submit the signin form incorrectly
        Then I should see a login error message
        And I edit the password field
        Then I should not see a login error message
        And I submit the signin form
        And I wait for "2" seconds
        Then I should see that the path is "/course/slashes:MITx+999+Robot_Super_Course"
        """
        self.install_course_fixture()
        self.course_outline_sign_in_redirect_page.visit()
        # Verify login_error is not present
        self.course_outline_sign_in_redirect_page.wait_for_element_absence(
            '#login_error',
            'Login error not be present'
        )
        # Login with wrong credentials
        self.course_outline_sign_in_redirect_page.login(
            self.user['email'],
            'wrong_password',
            expect_success=False
        )
        # Verify that login error is shown
        self.course_outline_sign_in_redirect_page.wait_for_element_visibility(
            ".js-form-errors.status.submission-error",
            'Login error is visible'
        )
        # Login with correct credentials
        self.course_outline_sign_in_redirect_page.login(self.user['email'], self.user['password'])
        self.course_outline_page.wait_for_page()
        # Verify that correct course is displayed after sign in.
        self.assertEqual(self.browser.current_url, self.course_outline_page.url)


class CoursePagesTest(StudioCourseTest):
    """
    Tests that verify the pages in Studio that you can get to when logged
    in and have a course.
    """
    shard = 21
    COURSE_ID_SEPARATOR = "."

    def setUp(self):
        """
        Install a course with no content using a fixture.
        """
        super(CoursePagesTest, self).setUp()

        self.pages = [
            clz(self.browser, self.course_info['org'], self.course_info['number'], self.course_info['run'])
            for clz in [
                AssetIndexPageStudioFrontend,
                CourseUpdatesPage,
                PagesPage, ExportCoursePage, ImportCoursePage, CourseTeamPage, CourseOutlinePage, SettingsPage,
                AdvancedSettingsPage, GradingPage, TextbookUploadPage
            ]
        ]

    def test_page_redirect(self):
        """
        /course/ is the base URL for all courses, but by itself, it should
        redirect to /home/.
        """
        self.dashboard_page = DashboardPage(self.browser)  # pylint: disable=attribute-defined-outside-init
        self.dashboard_page.visit()
        self.assertEqual(self.browser.current_url.strip('/').rsplit('/')[-1], 'home')

    def test_page_existence(self):
        """
        Make sure that all these pages are accessible once you have a course.
        Rather than fire up the browser just to check each url,
        do them all sequentially in this testcase.
        """

        # In the real workflow you will be at the dashboard page
        # after you log in. This test was intermittently failing on the
        # first (asset) page load with a 404.
        # Not exactly sure why, so adding in a visit
        # to the dashboard page here to replicate the usual flow.
        self.dashboard_page = DashboardPage(self.browser)
        self.dashboard_page.visit()

        # Verify that each page is available
        for page in self.pages:
            page.visit()


class DiscussionPreviewTest(StudioCourseTest):
    """
    Tests that Inline Discussions are rendered with a custom preview in Studio
    """
    shard = 21

    def setUp(self):
        super(DiscussionPreviewTest, self).setUp()
        cop = CourseOutlinePage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )
        cop.visit()
        self.unit = cop.section('Test Section').subsection('Test Subsection').expand_subsection().unit('Test Unit')
        self.unit.go_to()

    def populate_course_fixture(self, course_fixture):
        """
        Return a test course fixture containing a discussion component.
        """
        course_fixture.add_children(
            XBlockFixtureDesc("chapter", "Test Section").add_children(
                XBlockFixtureDesc("sequential", "Test Subsection").add_children(
                    XBlockFixtureDesc("vertical", "Test Unit").add_children(
                        XBlockFixtureDesc(
                            "discussion",
                            "Test Discussion",
                        )
                    )
                )
            )
        )

    def test_is_preview(self):
        """
        Ensure that the preview version of the discussion is rendered.
        """
        self.assertTrue(self.unit.q(css=".discussion-preview").present)
        self.assertFalse(self.unit.q(css=".discussion-show").present)
