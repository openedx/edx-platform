"""
Acceptance tests for the certificate web view feature.
"""
from ..helpers import UniqueCourseTest, EventsTestMixin
from nose.plugins.attrib import attr
from ...fixtures.course import CourseFixture
from ...fixtures.certificates import CertificateConfigFixture
from ...pages.lms.auto_auth import AutoAuthPage
from ...pages.lms.certificate_page import CertificatePage


@attr('shard_5')
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
        self.course_fixture.install()
        self.user_id = "99"  # we have createad a user with this id in fixture
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
