"""
Acceptance tests for the certificate web view feature.
"""
from common.test.acceptance.tests.helpers import UniqueCourseTest, EventsTestMixin, load_data_str, get_element_padding
from nose.plugins.attrib import attr
from common.test.acceptance.fixtures.course import CourseFixture, XBlockFixtureDesc, CourseUpdateDesc
from common.test.acceptance.fixtures.certificates import CertificateConfigFixture
from common.test.acceptance.pages.lms.auto_auth import AutoAuthPage
from common.test.acceptance.pages.lms.certificate_page import CertificatePage
from common.test.acceptance.pages.lms.course_info import CourseInfoPage
from common.test.acceptance.pages.lms.tab_nav import TabNavPage
from common.test.acceptance.pages.lms.course_nav import CourseNavPage
from common.test.acceptance.pages.lms.progress import ProgressPage


@attr(shard=5)
class CertificateWebViewTest(EventsTestMixin, UniqueCourseTest):
    """
    Tests for verifying certificate web view features
    """

    def setUp(self):
        super(CertificateWebViewTest, self).setUp()
        # set same course number as we have in fixture json
        self.course_info['number'] = "335535897951379478207964576572017930000"
        test_certificate_config = {
            'id': 1,
            'name': 'Certificate name',
            'description': 'Certificate description',
            'course_title': 'Course title override',
            'signatories': [],
            'version': 1,
            'is_active': True
        }
        course_settings = {'certificates': test_certificate_config}
        self.course_fixture = CourseFixture(
            self.course_info["org"],
            self.course_info["number"],
            self.course_info["run"],
            self.course_info["display_name"],
            settings=course_settings
        )
        self.course_fixture.add_advanced_settings({
            "cert_html_view_enabled": {"value": "true"}
        })
        self.course_fixture.install()
        self.user_id = "99"  # we have created a user with this id in fixture
        self.cert_fixture = CertificateConfigFixture(self.course_id, test_certificate_config)

        # Load certificate web view page for use by the tests
        self.certificate_page = CertificatePage(self.browser, self.user_id, self.course_id)

    def log_in_as_unique_user(self):
        """
        Log in as a valid lms user.
        """
        AutoAuthPage(
            self.browser,
            username="testcert",
            email="cert@example.com",
            password="testuser",
            course_id=self.course_id
        ).visit()

    def test_page_has_accomplishments_banner(self):
        """
        Scenario: User accomplishment banner should be present if logged in user is the one who is awarded
         the certificate
        Given there is a course with certificate configuration
        And I have passed the course and certificate is generated
        When I view the certificate web view page
        Then I should see the accomplishment banner. banner should have linked-in and facebook share buttons
        And When I click on `Add to Profile` button `edx.certificate.shared` event should be emitted
        """
        self.cert_fixture.install()
        self.log_in_as_unique_user()
        self.certificate_page.visit()
        self.assertTrue(self.certificate_page.accomplishment_banner.visible)
        self.assertTrue(self.certificate_page.add_to_linkedin_profile_button.visible)
        self.assertTrue(self.certificate_page.add_to_facebook_profile_button.visible)
        self.certificate_page.add_to_linkedin_profile_button.click()
        actual_events = self.wait_for_events(
            event_filter={'event_type': 'edx.certificate.shared'},
            number_of_matches=1
        )
        expected_events = [
            {
                'event': {
                    'user_id': self.user_id,
                    'course_id': self.course_id
                }
            }
        ]
        self.assert_events_match(expected_events, actual_events)


@attr(shard=5)
class CertificateProgressPageTest(UniqueCourseTest):
    """
    Tests for verifying Certificate info on Progress tab of course page.
    """

    def setUp(self):
        super(CertificateProgressPageTest, self).setUp()

        # set same course number as we have in fixture json
        self.course_info['number'] = "3355358979513794782079645765720179311111"

        test_certificate_config = {
            'id': 1,
            'name': 'Certificate name',
            'description': 'Certificate description',
            'course_title': 'Course title override',
            'signatories': [],
            'version': 1,
            'is_active': True
        }
        course_settings = {'certificates': test_certificate_config}

        self.course_fixture = CourseFixture(
            self.course_info["org"],
            self.course_info["number"],
            self.course_info["run"],
            self.course_info["display_name"],
            settings=course_settings
        )

        self.course_fixture.add_advanced_settings({
            "cert_html_view_enabled": {"value": "true"}
        })

        self.course_fixture.add_update(
            CourseUpdateDesc(date='January 29, 2014', content='Test course update1')
        )

        self.course_fixture.add_children(
            XBlockFixtureDesc('static_tab', 'Test Static Tab'),
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection', grader_type='Final Exam').add_children(
                    XBlockFixtureDesc('problem', 'Test Problem 1', data=load_data_str('multiple_choice.xml')),
                    XBlockFixtureDesc('html', 'Test HTML'),
                )
            ),
            XBlockFixtureDesc('chapter', 'Test Section 2').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection 2', grader_type='Midterm Exam').add_children(
                    XBlockFixtureDesc('problem', 'Test Problem 2', data=load_data_str('formula_problem.xml')),
                )
            )
        )

        self.course_fixture.install()
        self.user_id = "99"  # we have created a user with this id in fixture
        self.cert_fixture = CertificateConfigFixture(self.course_id, test_certificate_config)

        self.course_info_page = CourseInfoPage(self.browser, self.course_id)
        self.progress_page = ProgressPage(self.browser, self.course_id)
        self.course_nav = CourseNavPage(self.browser)
        self.tab_nav = TabNavPage(self.browser)

    def log_in_as_unique_user(self):
        """
        Log in as a valid lms user.
        """
        AutoAuthPage(
            self.browser,
            username="testprogress",
            email="progress@example.com",
            password="testuser",
            course_id=self.course_id
        ).visit()

    def test_progress_page_has_view_certificate_button(self):
        """
        Scenario: View Certificate option should be present on Course Progress menu if the user is
        awarded a certificate.
        And their should be no padding around the box containing certificate info. (See SOL-1196 for details on this)

        As a Student
        Given there is a course with certificate configuration
        And I have passed the course and certificate is generated
        When I go on the Progress tab for the course
        Then I should see a 'View Certificate' button
        And their should be no padding around Certificate info box.
        """
        self.cert_fixture.install()
        self.log_in_as_unique_user()

        self.complete_course_problems()

        self.course_info_page.visit()
        self.tab_nav.go_to_tab('Progress')

        self.assertTrue(self.progress_page.q(css='.auto-cert-message').first.visible)

        actual_padding = get_element_padding(self.progress_page, '.wrapper-msg.wrapper-auto-cert')
        actual_padding = [int(padding) for padding in actual_padding.itervalues()]
        expected_padding = [0, 0, 0, 0]

        # Verify that their is no padding around the box containing certificate info.
        self.assertEqual(actual_padding, expected_padding)

    def complete_course_problems(self):
        """
        Complete Course Problems.

        Problems were added in the setUp
        """
        self.course_info_page.visit()
        self.tab_nav.go_to_tab('Course')

        # Navigate to Test Subsection in Test Section Section
        self.course_nav.go_to_section('Test Section', 'Test Subsection')

        # Navigate to Test Problem 1
        self.course_nav.go_to_vertical('Test Problem 1')

        # Select correct value for from select menu
        self.course_nav.q(css='select option[value="{}"]'.format('blue')).first.click()

        # Select correct radio button for the answer
        self.course_nav.q(css='fieldset div.field:nth-child(3) input').nth(0).click()

        # Select correct radio buttons for the answer
        self.course_nav.q(css='fieldset div.field:nth-child(1) input').nth(1).click()
        self.course_nav.q(css='fieldset div.field:nth-child(3) input').nth(1).click()

        # Submit the answer
        self.course_nav.q(css='button.check.Check').click()
        self.course_nav.wait_for_ajax()

        # Navigate to the 'Test Subsection 2' of 'Test Section 2'
        self.course_nav.go_to_section('Test Section 2', 'Test Subsection 2')

        # Navigate to Test Problem 2
        self.course_nav.go_to_vertical('Test Problem 2')

        # Fill in the answer of the problem
        self.course_nav.q(css='input[id^=input_][id$=_2_1]').fill('A*x^2 + sqrt(y)')

        # Submit the answer
        self.course_nav.q(css='button.check.Check').click()
        self.course_nav.wait_for_ajax()
