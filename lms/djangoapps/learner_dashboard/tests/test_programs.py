# -*- coding: utf-8 -*-
"""
Unit tests covering the program listing and detail pages.
"""
import json
import re
import unittest
from urlparse import urljoin

from bs4 import BeautifulSoup
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import override_settings
from django.utils.text import slugify
from edx_oauth2_provider.tests.factories import ClientFactory
import httpretty
import mock
from provider.constants import CONFIDENTIAL

from openedx.core.djangoapps.credentials.models import CredentialsApiConfig
from openedx.core.djangoapps.credentials.tests import factories as credentials_factories
from openedx.core.djangoapps.credentials.tests.mixins import CredentialsApiConfigMixin
from openedx.core.djangoapps.programs.models import ProgramsApiConfig
from openedx.core.djangoapps.programs.tests import factories as programs_factories
from openedx.core.djangoapps.programs.tests.mixins import ProgramsApiConfigMixin
from openedx.core.djangoapps.programs.utils import get_display_category
from student.tests.factories import UserFactory, CourseEnrollmentFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


UTILS_MODULE = 'openedx.core.djangoapps.programs.utils'
MARKETING_URL = 'https://www.example.com/marketing/path'


@httpretty.activate
@override_settings(MKTG_URLS={'ROOT': 'https://www.example.com'})
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TestProgramListing(ProgramsApiConfigMixin, CredentialsApiConfigMixin, SharedModuleStoreTestCase):
    """Unit tests for the program listing page."""
    maxDiff = None
    password = 'test'
    url = reverse('program_listing_view')

    @classmethod
    def setUpClass(cls):
        super(TestProgramListing, cls).setUpClass()

        for name in [ProgramsApiConfig.OAUTH2_CLIENT_NAME, CredentialsApiConfig.OAUTH2_CLIENT_NAME]:
            ClientFactory(name=name, client_type=CONFIDENTIAL)

        cls.course = CourseFactory()
        organization = programs_factories.Organization()
        run_mode = programs_factories.RunMode(course_key=unicode(cls.course.id))  # pylint: disable=no-member
        course_code = programs_factories.CourseCode(run_modes=[run_mode])

        cls.first_program = programs_factories.Program(
            organizations=[organization],
            course_codes=[course_code]
        )
        cls.second_program = programs_factories.Program(
            organizations=[organization],
            course_codes=[course_code]
        )

        cls.data = sorted([cls.first_program, cls.second_program], key=cls.program_sort_key)

        cls.marketing_root = urljoin(settings.MKTG_URLS.get('ROOT'), 'xseries').rstrip('/')

    def setUp(self):
        super(TestProgramListing, self).setUp()

        self.user = UserFactory()
        self.client.login(username=self.user.username, password=self.password)

    @classmethod
    def program_sort_key(cls, program):
        """
        Helper function used to sort dictionaries representing programs.
        """
        return program['id']

    def credential_sort_key(self, credential):
        """
        Helper function used to sort dictionaries representing credentials.
        """
        try:
            return credential['certificate_url']
        except KeyError:
            return credential['credential_url']

    def mock_programs_api(self, data):
        """Helper for mocking out Programs API URLs."""
        self.assertTrue(httpretty.is_enabled(), msg='httpretty must be enabled to mock Programs API calls.')

        url = ProgramsApiConfig.current().internal_api_url.strip('/') + '/programs/'
        body = json.dumps({'results': data})

        httpretty.register_uri(httpretty.GET, url, body=body, content_type='application/json')

    def mock_credentials_api(self, data):
        """Helper for mocking out Credentials API URLs."""
        self.assertTrue(httpretty.is_enabled(), msg='httpretty must be enabled to mock Credentials API calls.')

        url = '{base}/user_credentials/?username={username}'.format(
            base=CredentialsApiConfig.current().internal_api_url.strip('/'),
            username=self.user.username
        )
        body = json.dumps({'results': data})

        httpretty.register_uri(httpretty.GET, url, body=body, content_type='application/json')

    def load_serialized_data(self, response, key):
        """
        Extract and deserialize serialized data from the response.
        """
        pattern = re.compile(r'{key}: (?P<data>\[.*\])'.format(key=key))
        match = pattern.search(response.content)
        serialized = match.group('data')

        return json.loads(serialized)

    def assert_dict_contains_subset(self, superset, subset):
        """
        Verify that the dict superset contains the dict subset.

        Works like assertDictContainsSubset, deprecated since Python 3.2.
        See: https://docs.python.org/2.7/library/unittest.html#unittest.TestCase.assertDictContainsSubset.
        """
        superset_keys = set(superset.keys())
        subset_keys = set(subset.keys())
        intersection = {key: superset[key] for key in superset_keys & subset_keys}

        self.assertEqual(subset, intersection)

    def test_login_required(self):
        """
        Verify that login is required to access the page.
        """
        self.create_programs_config()
        self.mock_programs_api(self.data)

        self.client.logout()

        response = self.client.get(self.url)
        self.assertRedirects(
            response,
            '{}?next={}'.format(reverse('signin_user'), self.url)
        )

        self.client.login(username=self.user.username, password=self.password)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_404_if_disabled(self):
        """
        Verify that the page 404s if disabled.
        """
        self.create_programs_config(program_listing_enabled=False)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_empty_state(self):
        """
        Verify that the response contains no programs data when no programs are engaged.
        """
        self.create_programs_config()
        self.mock_programs_api(self.data)

        response = self.client.get(self.url)
        self.assertContains(response, 'programsData: []')

    def test_programs_listed(self):
        """
        Verify that the response contains accurate programs data when programs are engaged.
        """
        self.create_programs_config()
        self.mock_programs_api(self.data)

        CourseEnrollmentFactory(user=self.user, course_id=self.course.id)  # pylint: disable=no-member

        response = self.client.get(self.url)
        actual = self.load_serialized_data(response, 'programsData')
        actual = sorted(actual, key=self.program_sort_key)

        for index, actual_program in enumerate(actual):
            expected_program = self.data[index]

            self.assert_dict_contains_subset(actual_program, expected_program)
            self.assertEqual(
                actual_program['display_category'],
                get_display_category(expected_program)
            )

    def test_toggle_xseries_advertising(self):
        """
        Verify that when XSeries advertising is disabled, no link to the marketing site
        appears in the response (and vice versa).
        """
        # Verify the URL is present when advertising is enabled.
        self.create_programs_config()
        self.mock_programs_api(self.data)

        response = self.client.get(self.url)
        self.assertContains(response, self.marketing_root)

        # Verify the URL is missing when advertising is disabled.
        self.create_programs_config(xseries_ad_enabled=False)

        response = self.client.get(self.url)
        self.assertNotContains(response, self.marketing_root)

    def test_links_to_detail_pages(self):
        """
        Verify that links to detail pages are present when enabled, instead of
        links to the marketing site.
        """
        self.create_programs_config()
        self.mock_programs_api(self.data)

        CourseEnrollmentFactory(user=self.user, course_id=self.course.id)  # pylint: disable=no-member

        response = self.client.get(self.url)
        actual = self.load_serialized_data(response, 'programsData')
        actual = sorted(actual, key=self.program_sort_key)

        for index, actual_program in enumerate(actual):
            expected_program = self.data[index]

            base = reverse('program_details_view', args=[expected_program['id']]).rstrip('/')
            slug = slugify(expected_program['name'])
            self.assertEqual(
                actual_program['detail_url'],
                '{}/{}'.format(base, slug)
            )

        # Verify that links to the marketing site are present when detail pages are disabled.
        self.create_programs_config(program_details_enabled=False)

        response = self.client.get(self.url)
        actual = self.load_serialized_data(response, 'programsData')
        actual = sorted(actual, key=self.program_sort_key)

        for index, actual_program in enumerate(actual):
            expected_program = self.data[index]

            self.assertEqual(
                actual_program['detail_url'],
                '{}/{}'.format(self.marketing_root, expected_program['marketing_slug'])
            )

    def test_certificates_listed(self):
        """
        Verify that the response contains accurate certificate data when certificates are available.
        """
        self.create_programs_config()
        self.create_credentials_config(is_learner_issuance_enabled=True)

        self.mock_programs_api(self.data)

        first_credential = credentials_factories.UserCredential(
            username=self.user.username,
            credential=credentials_factories.ProgramCredential(
                program_id=self.first_program['id']
            )
        )
        second_credential = credentials_factories.UserCredential(
            username=self.user.username,
            credential=credentials_factories.ProgramCredential(
                program_id=self.second_program['id']
            )
        )

        credentials_data = sorted([first_credential, second_credential], key=self.credential_sort_key)

        self.mock_credentials_api(credentials_data)

        response = self.client.get(self.url)
        actual = self.load_serialized_data(response, 'certificatesData')
        actual = sorted(actual, key=self.credential_sort_key)

        for index, actual_credential in enumerate(actual):
            expected_credential = credentials_data[index]

            self.assertEqual(
                # TODO: certificate_url is needlessly transformed to credential_url. (╯°□°）╯︵ ┻━┻
                # Clean this up!
                actual_credential['credential_url'],
                expected_credential['certificate_url']
            )


@httpretty.activate
@override_settings(MKTG_URLS={'ROOT': 'https://www.example.com'})
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
@mock.patch(UTILS_MODULE + '.get_run_marketing_url', mock.Mock(return_value=MARKETING_URL))
class TestProgramDetails(ProgramsApiConfigMixin, SharedModuleStoreTestCase):
    """Unit tests for the program details page."""
    program_id = 123
    password = 'test'
    url = reverse('program_details_view', args=[program_id])

    @classmethod
    def setUpClass(cls):
        super(TestProgramDetails, cls).setUpClass()

        ClientFactory(name=ProgramsApiConfig.OAUTH2_CLIENT_NAME, client_type=CONFIDENTIAL)

        course = CourseFactory()
        organization = programs_factories.Organization()
        run_mode = programs_factories.RunMode(course_key=unicode(course.id))  # pylint: disable=no-member
        course_code = programs_factories.CourseCode(run_modes=[run_mode])

        cls.data = programs_factories.Program(
            organizations=[organization],
            course_codes=[course_code]
        )

    def setUp(self):
        super(TestProgramDetails, self).setUp()

        self.user = UserFactory()
        self.client.login(username=self.user.username, password=self.password)

    def mock_programs_api(self, data, status=200):
        """Helper for mocking out Programs API URLs."""
        self.assertTrue(httpretty.is_enabled(), msg='httpretty must be enabled to mock Programs API calls.')

        url = '{api_root}/programs/{id}/'.format(
            api_root=ProgramsApiConfig.current().internal_api_url.strip('/'),
            id=self.program_id
        )

        body = json.dumps(data)

        httpretty.register_uri(
            httpretty.GET,
            url,
            body=body,
            status=status,
            content_type='application/json',
        )

    def assert_program_data_present(self, response):
        """Verify that program data is present."""
        self.assertContains(response, 'programData')
        self.assertContains(response, 'urls')
        self.assertContains(response, 'program_listing_url')
        self.assertContains(response, self.data['name'])
        self.assert_programs_tab_present(response)

    def assert_programs_tab_present(self, response):
        """Verify that the programs tab is present in the nav."""
        soup = BeautifulSoup(response.content, 'html.parser')
        self.assertTrue(
            any(soup.find_all('a', class_='tab-nav-link', href=reverse('program_listing_view')))
        )

    def test_login_required(self):
        """
        Verify that login is required to access the page.
        """
        self.create_programs_config()
        self.mock_programs_api(self.data)

        self.client.logout()

        response = self.client.get(self.url)
        self.assertRedirects(
            response,
            '{}?next={}'.format(reverse('signin_user'), self.url)
        )

        self.client.login(username=self.user.username, password=self.password)

        response = self.client.get(self.url)
        self.assert_program_data_present(response)

    def test_404_if_disabled(self):
        """
        Verify that the page 404s if disabled.
        """
        self.create_programs_config(program_details_enabled=False)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_404_if_no_data(self):
        """Verify that the page 404s if no program data is found."""
        self.create_programs_config()

        self.mock_programs_api(self.data, status=404)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

        httpretty.reset()

        self.mock_programs_api({})
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_page_routing(self):
        """Verify that the page can be hit with or without a program name in the URL."""
        self.create_programs_config()
        self.mock_programs_api(self.data)

        response = self.client.get(self.url)
        self.assert_program_data_present(response)

        response = self.client.get(self.url + 'program_name/')
        self.assert_program_data_present(response)

        response = self.client.get(self.url + 'program_name/invalid/')
        self.assertEqual(response.status_code, 404)
