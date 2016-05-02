"""
Tests for viewing the programs enrolled by a learner.
"""
import datetime
import httpretty
import unittest
from urlparse import urljoin

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.test import override_settings
from edx_oauth2_provider.tests.factories import ClientFactory
from opaque_keys.edx import locator
from provider.constants import CONFIDENTIAL

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
        ProgramsDataMixin):

    """
    Unit tests for getting the list of programs enrolled by a logged in user
    """
    PASSWORD = 'test'

    def setUp(self):
        """
            Add a student
        """
        super(TestProgramListing, self).setUp()
        ClientFactory(name=ProgramsApiConfig.OAUTH2_CLIENT_NAME, client_type=CONFIDENTIAL)
        self.student = UserFactory()
        self.create_programs_config(xseries_ad_enabled=True)

    def _create_course_and_enroll(self, student, org, course, run):
        """
        Creates a course and associated enrollment.
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
        response = self.client.get(reverse("program_listing_view"))
        self.assertEqual(response.status_code, 200)
        x_series_url = urljoin(settings.MKTG_URLS.get('ROOT'), 'xseries')
        self.assertIn(x_series_url, response.content)
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

    @httpretty.activate
    def test_get_program_with_no_enrollment(self):
        response = self._setup_and_get_program()
        for program_element in self._get_program_checklist(0):
            self.assertNotIn(program_element, response.content)
        for program_element in self._get_program_checklist(1):
            self.assertNotIn(program_element, response.content)

    @httpretty.activate
    def test_get_one_program(self):
        self._create_course_and_enroll(self.student, *self.COURSE_KEYS[0].split('/'))
        response = self._setup_and_get_program()
        for program_element in self._get_program_checklist(0):
            self.assertIn(program_element, response.content)
        for program_element in self._get_program_checklist(1):
            self.assertNotIn(program_element, response.content)

    @httpretty.activate
    def test_get_both_program(self):
        self._create_course_and_enroll(self.student, *self.COURSE_KEYS[0].split('/'))
        self._create_course_and_enroll(self.student, *self.COURSE_KEYS[5].split('/'))
        response = self._setup_and_get_program()
        for program_element in self._get_program_checklist(0):
            self.assertIn(program_element, response.content)
        for program_element in self._get_program_checklist(1):
            self.assertIn(program_element, response.content)

    def test_get_programs_dashboard_not_enabled(self):
        self.create_programs_config(enable_student_dashboard=False)
        self.client.login(username=self.student.username, password=self.PASSWORD)
        response = self.client.get(reverse("program_listing_view"))
        self.assertEqual(response.status_code, 404)

    def test_xseries_advertise_disabled(self):
        self.create_programs_config(xseries_ad_enabled=False)
        self.client.login(username=self.student.username, password=self.PASSWORD)
        response = self.client.get(reverse("program_listing_view"))
        self.assertEqual(response.status_code, 200)
        x_series_url = urljoin(settings.MKTG_URLS.get('ROOT'), 'xseries')
        self.assertNotIn(x_series_url, response.content)

    def test_get_programs_not_logged_in(self):
        self.create_programs_config()
        response = self.client.get(reverse("program_listing_view"))
        self.assertEqual(response.status_code, 302)
        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertIn('login', response.url)  # pylint: disable=no-member
