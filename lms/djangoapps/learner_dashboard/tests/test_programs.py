"""
Tests for viewing the programs enrolled by a learner.
"""
import datetime
import httpretty
import unittest
from urlparse import urljoin

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import override_settings
from edx_oauth2_provider.tests.factories import ClientFactory
from opaque_keys.edx import locator
from provider.constants import CONFIDENTIAL

from openedx.core.djangoapps.credentials.models import CredentialsApiConfig
from openedx.core.djangoapps.credentials.tests.mixins import CredentialsDataMixin, CredentialsApiConfigMixin
from openedx.core.djangoapps.programs.tests.mixins import (
    ProgramsApiConfigMixin,
    ProgramsDataMixin)
from openedx.core.djangoapps.programs.models import ProgramsApiConfig
from student.models import CourseEnrollment
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
@override_settings(MKTG_URLS={'ROOT': 'http://edx.org'})
class TestProgramListing(
        ModuleStoreTestCase,
        ProgramsApiConfigMixin,
        ProgramsDataMixin,
        CredentialsDataMixin,
        CredentialsApiConfigMixin):

    """
    Unit tests for getting the list of programs enrolled by a logged in user
    """
    PASSWORD = 'test'
    url = reverse('program_listing_view')

    def setUp(self):
        """
            Add a student
        """
        super(TestProgramListing, self).setUp()
        ClientFactory(name=CredentialsApiConfig.OAUTH2_CLIENT_NAME, client_type=CONFIDENTIAL)
        ClientFactory(name=ProgramsApiConfig.OAUTH2_CLIENT_NAME, client_type=CONFIDENTIAL)
        self.student = UserFactory()
        self.create_programs_config(xseries_ad_enabled=True, program_listing_enabled=True)

    def _create_course_and_enroll(self, student, org, course, run):
        """
        Creates a course and associated enrollment.

        TODO: Use CourseEnrollmentFactory to avoid course creation.
        """
        course_location = locator.CourseLocator(org, course, run)
        course = CourseFactory.create(
            org=course_location.org,
            number=course_location.course,
            run=course_location.run
        )
        enrollment = CourseEnrollment.enroll(student, course.id)
        enrollment.created = datetime.datetime(2000, 12, 31, 0, 0, 0, 0)
        enrollment.save()

    def _get_program_url(self, marketing_slug):
        """
        Helper function to get the program card url
        """
        return urljoin(
            settings.MKTG_URLS.get('ROOT'),
            'xseries' + '/{}'
        ).format(marketing_slug)

    def _setup_and_get_program(self):
        """
        The core function to setup the mock program api,
        then call the django test client to get the actual program listing page
        make sure the request suceeds and make sure x_series_url is on the page
        """
        self.mock_programs_api()
        self.client.login(username=self.student.username, password=self.PASSWORD)
        response = self.client.get(self.url)
        x_series_url = urljoin(settings.MKTG_URLS.get('ROOT'), 'xseries')
        self.assertContains(response, x_series_url)
        return response

    def _get_program_checklist(self, program_id):
        """
        The convenience function to get all the program related page element we would like to check against
        """
        return [
            self.PROGRAM_NAMES[program_id],
            self._get_program_url(self.PROGRAMS_API_RESPONSE['results'][program_id]['marketing_slug']),
            self.PROGRAMS_API_RESPONSE['results'][program_id]['organizations'][0]['display_name'],
        ]

    def _assert_progress_data_present(self, response):
        """Verify that progress data is present."""
        self.assertContains(response, 'userProgress')

    @httpretty.activate
    def test_get_program_with_no_enrollment(self):
        response = self._setup_and_get_program()
        for program_element in self._get_program_checklist(0):
            self.assertNotContains(response, program_element)
        for program_element in self._get_program_checklist(1):
            self.assertNotContains(response, program_element)

    @httpretty.activate
    def test_get_one_program(self):
        self._create_course_and_enroll(self.student, *self.COURSE_KEYS[0].split('/'))
        response = self._setup_and_get_program()
        for program_element in self._get_program_checklist(0):
            self.assertContains(response, program_element)
        for program_element in self._get_program_checklist(1):
            self.assertNotContains(response, program_element)

        self._assert_progress_data_present(response)

    @httpretty.activate
    def test_get_both_program(self):
        self._create_course_and_enroll(self.student, *self.COURSE_KEYS[0].split('/'))
        self._create_course_and_enroll(self.student, *self.COURSE_KEYS[5].split('/'))
        response = self._setup_and_get_program()
        for program_element in self._get_program_checklist(0):
            self.assertContains(response, program_element)
        for program_element in self._get_program_checklist(1):
            self.assertContains(response, program_element)

        self._assert_progress_data_present(response)

    def test_get_programs_dashboard_not_enabled(self):
        self.create_programs_config(program_listing_enabled=False)
        self.client.login(username=self.student.username, password=self.PASSWORD)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_xseries_advertise_disabled(self):
        self.create_programs_config(program_listing_enabled=True, xseries_ad_enabled=False)
        self.client.login(username=self.student.username, password=self.PASSWORD)
        response = self.client.get(self.url)
        x_series_url = urljoin(settings.MKTG_URLS.get('ROOT'), 'xseries')
        self.assertNotContains(response, x_series_url)

    def test_get_programs_not_logged_in(self):
        self.create_programs_config()
        response = self.client.get(self.url)

        self.assertRedirects(
            response,
            '{}?next={}'.format(reverse('signin_user'), self.url)
        )

    # TODO: Use a factory to generate this data.
    def _expected_credentials_data(self):
        """ Dry method for getting expected credentials."""

        return [
            {
                "display_name": "Test Program A",
                "credential_url": "http://credentials.edx.org/credentials/dummy-uuid-1/"
            },
            {
                "display_name": "Test Program B",
                "credential_url": "http://credentials.edx.org/credentials/dummy-uuid-2/"
            }
        ]

    @httpretty.activate
    def test_get_xseries_certificates_with_data(self):

        self.create_programs_config(program_listing_enabled=True)
        self.create_credentials_config(is_learner_issuance_enabled=True)

        self.client.login(username=self.student.username, password=self.PASSWORD)

        # mock programs and credentials apis
        self.mock_programs_api()
        self.mock_credentials_api(self.student, data=self.CREDENTIALS_API_RESPONSE, reset_url=False)

        response = self.client.get(reverse("program_listing_view"))
        for certificate in self._expected_credentials_data():
            self.assertContains(response, certificate['display_name'])
            self.assertContains(response, certificate['credential_url'])

        self.assertContains(response, 'images/xseries-certificate-visual.png')

    @httpretty.activate
    def test_get_xseries_certificates_without_data(self):

        self.create_programs_config(program_listing_enabled=True)
        self.create_credentials_config(is_learner_issuance_enabled=True)

        self.client.login(username=self.student.username, password=self.PASSWORD)

        # mock programs and credentials apis
        self.mock_programs_api()
        self.mock_credentials_api(self.student, data={"results": []}, reset_url=False)

        response = self.client.get(reverse("program_listing_view"))
        for certificate in self._expected_credentials_data():
            self.assertNotContains(response, certificate['display_name'])
            self.assertNotContains(response, certificate['credential_url'])
