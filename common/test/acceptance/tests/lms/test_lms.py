# -*- coding: utf-8 -*-
"""
End-to-end tests for the LMS.
"""

from textwrap import dedent
from unittest import skip
from nose.plugins.attrib import attr

from bok_choy.web_app_test import WebAppTest
from ..helpers import UniqueCourseTest, load_data_str
from ...pages.lms.auto_auth import AutoAuthPage
from ...pages.common.logout import LogoutPage
from ...pages.lms.course_info import CourseInfoPage
from ...pages.lms.tab_nav import TabNavPage
from ...pages.lms.course_nav import CourseNavPage
from ...pages.lms.progress import ProgressPage
from ...pages.lms.dashboard import DashboardPage
from ...pages.lms.problem import ProblemPage
from ...pages.lms.video.video import VideoPage
from ...pages.lms.courseware import CoursewarePage
from ...pages.lms.login_and_register import CombinedLoginAndRegisterPage
from ...fixtures.course import CourseFixture, XBlockFixtureDesc, CourseUpdateDesc


@attr('shard_1')
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
        email, password = self._create_unique_user()

        # Navigate to the password reset form and try to submit it
        self.login_page.visit().password_reset(email=email)

        # Expect that we're shown a success message
        self.assertIn("PASSWORD RESET EMAIL SENT", self.login_page.wait_for_success())

    def test_password_reset_failure(self):
        # Navigate to the password reset form
        self.login_page.visit()

        # User account does not exist
        self.login_page.password_reset(email="nobody@nowhere.com")

        # Expect that we're shown a failure message
        self.assertIn(
            "No active user with the provided email address exists.",
            self.login_page.wait_for_errors()
        )

    def _create_unique_user(self):
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


@attr('shard_1')
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
        self.assertIn(u'The Username field cannot be empty.', errors)
        self.assertIn(u'You must agree to the edX Terms of Service and Honor Code.', errors)
        self.assertIn(u'The Country field cannot be empty.', errors)

    def test_toggle_to_login_form(self):
        self.register_page.visit().toggle_form()
        self.assertEqual(self.register_page.current_form, "login")


class LanguageTest(WebAppTest):
    """
    Tests that the change language functionality on the dashboard works
    """

    def setUp(self):
        """
        Initiailize dashboard page
        """
        super(LanguageTest, self).setUp()
        self.dashboard_page = DashboardPage(self.browser)

        self.test_new_lang = 'eo'
        # This string is unicode for "ÇÜRRÉNT ÇØÜRSÉS", which should appear in our Dummy Esperanto page
        # We store the string this way because Selenium seems to try and read in strings from
        # the HTML in this format. Ideally we could just store the raw ÇÜRRÉNT ÇØÜRSÉS string here
        self.current_courses_text = u'\xc7\xdcRR\xc9NT \xc7\xd6\xdcRS\xc9S'

        self.username = "test"
        self.password = "testpass"
        self.email = "test@example.com"

    def test_change_lang(self):
        AutoAuthPage(self.browser).visit()
        self.dashboard_page.visit()
        # Change language to Dummy Esperanto
        self.dashboard_page.change_language(self.test_new_lang)

        changed_text = self.dashboard_page.current_courses_text

        # We should see the dummy-language text on the page
        self.assertIn(self.current_courses_text, changed_text)

    def test_language_persists(self):
        auto_auth_page = AutoAuthPage(self.browser, username=self.username, password=self.password, email=self.email)
        auto_auth_page.visit()

        self.dashboard_page.visit()
        # Change language to Dummy Esperanto
        self.dashboard_page.change_language(self.test_new_lang)

        # destroy session
        self.browser.delete_all_cookies()

        # log back in
        auto_auth_page.visit()

        self.dashboard_page.visit()

        changed_text = self.dashboard_page.current_courses_text

        # We should see the dummy-language text on the page
        self.assertIn(self.current_courses_text, changed_text)


class HighLevelTabTest(UniqueCourseTest):
    """
    Tests that verify each of the high-level tabs available within a course.
    """

    def setUp(self):
        """
        Initialize pages and install a course fixture.
        """
        super(HighLevelTabTest, self).setUp()

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
            XBlockFixtureDesc('static_tab', 'Test Static Tab'),
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
        self.tab_nav.go_to_tab('Course Info')

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

    def test_courseware_nav(self):
        """
        Navigate to a particular unit in the courseware.
        """
        # Navigate to the courseware page from the info page
        self.course_info_page.visit()
        self.tab_nav.go_to_tab('Courseware')

        # Check that the courseware navigation appears correctly
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


class VideoTest(UniqueCourseTest):
    """
    Navigate to a video in the courseware and play it.
    """
    def setUp(self):
        """
        Initialize pages and install a course fixture.
        """
        super(VideoTest, self).setUp()

        self.course_info_page = CourseInfoPage(self.browser, self.course_id)
        self.course_nav = CourseNavPage(self.browser)
        self.tab_nav = TabNavPage(self.browser)
        self.video = VideoPage(self.browser)

        # Install a course fixture with a video component
        course_fix = CourseFixture(
            self.course_info['org'], self.course_info['number'],
            self.course_info['run'], self.course_info['display_name']
        )

        course_fix.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc('vertical', 'Test Unit').add_children(
                        XBlockFixtureDesc('video', 'Video')
                    )))).install()

        # Auto-auth register for the course
        AutoAuthPage(self.browser, course_id=self.course_id).visit()

    @skip("BLD-563: Video Player Stuck on Pause")
    def test_video_player(self):
        """
        Play a video in the courseware.
        """

        # Navigate to a video
        self.course_info_page.visit()
        self.tab_nav.go_to_tab('Courseware')

        # The video should start off paused
        # Since the video hasn't loaded yet, it's elapsed time is 0
        self.assertFalse(self.video.is_playing)
        self.assertEqual(self.video.elapsed_time, 0)

        # Play the video
        self.video.play()

        # Now we should be playing
        self.assertTrue(self.video.is_playing)

        # Commented the below EmptyPromise, will move to its page once this test is working and stable
        # Also there is should be no Promise check in any test as this should be done in Page Object
        # Wait for the video to load the duration
        # EmptyPromise(
        #     lambda: self.video.duration > 0,
        #     'video has duration', timeout=20
        # ).fulfill()

        # Pause the video
        self.video.pause()

        # Expect that the elapsed time and duration are reasonable
        # Again, we can't expect the video to actually play because of
        # latency through the ssh tunnel
        self.assertGreaterEqual(self.video.elapsed_time, 0)
        self.assertGreaterEqual(self.video.duration, self.video.elapsed_time)


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
        self.assertEqual(["Html Child in locked unit", "Html Child in unlocked unit"], self.course_nav.sequence_items)

        self.course_nav.go_to_section("Test Section", "Unlocked Subsection")
        self.assertEqual(["Html Child in visible unit"], self.course_nav.sequence_items)

        self.course_nav.go_to_section("Test Section", "Locked Subsection")
        self.assertEqual(["Html Child in locked subsection"], self.course_nav.sequence_items)

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
        self.assertEqual(["Html Child in unlocked unit"], self.course_nav.sequence_items)

        self.course_nav.go_to_section("Test Section", "Unlocked Subsection")
        self.assertEqual(["Html Child in visible unit"], self.course_nav.sequence_items)


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
        self.tab_nav.go_to_tab('Courseware')

        self.assertTrue(self.courseware_page.tooltips_displayed())


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
        self.tab_nav.go_to_tab('Courseware')
        self.course_nav.go_to_section('Test Section', 'Test Subsection')

        problem_page = ProblemPage(self.browser)
        self.assertEqual(problem_page.problem_name, 'PYTHON PROBLEM')

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
