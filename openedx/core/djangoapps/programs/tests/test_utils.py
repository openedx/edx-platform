"""Tests covering Programs utilities."""
import json
from unittest import skipUnless

import ddt
import httpretty
import mock
from django.conf import settings
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.test import TestCase
from edx_oauth2_provider.tests.factories import ClientFactory
from nose.plugins.attrib import attr
from opaque_keys.edx.keys import CourseKey
from provider.constants import CONFIDENTIAL

from lms.djangoapps.certificates.api import MODES
from openedx.core.djangoapps.credentials.tests import factories as credentials_factories
from openedx.core.djangoapps.credentials.tests.mixins import CredentialsApiConfigMixin, CredentialsDataMixin
from openedx.core.djangoapps.programs import utils
from openedx.core.djangoapps.programs.models import ProgramsApiConfig
from openedx.core.djangoapps.programs.tests import factories
from openedx.core.djangoapps.programs.tests.mixins import ProgramsApiConfigMixin, ProgramsDataMixin
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase
from student.tests.factories import UserFactory, CourseEnrollmentFactory

UTILS_MODULE = 'openedx.core.djangoapps.programs.utils'
CERTIFICATES_API_MODULE = 'lms.djangoapps.certificates.api'
ECOMMERCE_URL_ROOT = 'https://example-ecommerce.com'
MARKETING_URL = 'https://www.example.com/marketing/path'


@ddt.ddt
@attr(shard=2)
@httpretty.activate
@skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TestProgramRetrieval(ProgramsApiConfigMixin, ProgramsDataMixin, CredentialsDataMixin,
                           CredentialsApiConfigMixin, CacheIsolationTestCase):
    """Tests covering the retrieval of programs from the Programs service."""

    ENABLED_CACHES = ['default']

    def setUp(self):
        super(TestProgramRetrieval, self).setUp()

        ClientFactory(name=ProgramsApiConfig.OAUTH2_CLIENT_NAME, client_type=CONFIDENTIAL)
        self.user = UserFactory()

        cache.clear()

    def _expected_progam_credentials_data(self):
        """
        Dry method for getting expected program credentials response data.
        """
        return [
            credentials_factories.UserCredential(
                id=1,
                username='test',
                credential=credentials_factories.ProgramCredential(
                    program_id=1
                )
            ),
            credentials_factories.UserCredential(
                id=2,
                username='test',
                credential=credentials_factories.ProgramCredential(
                    program_id=2
                )
            )
        ]

    def test_get_programs(self):
        """Verify programs data can be retrieved."""
        self.create_programs_config()
        self.mock_programs_api()

        actual = utils.get_programs(self.user)
        self.assertEqual(
            actual,
            self.PROGRAMS_API_RESPONSE['results']
        )

        # Verify the API was actually hit (not the cache).
        self.assertEqual(len(httpretty.httpretty.latest_requests), 1)

    def test_get_programs_caching(self):
        """Verify that when enabled, the cache is used for non-staff users."""
        self.create_programs_config(cache_ttl=1)
        self.mock_programs_api()

        # Warm up the cache.
        utils.get_programs(self.user)

        # Hit the cache.
        utils.get_programs(self.user)

        # Verify only one request was made.
        self.assertEqual(len(httpretty.httpretty.latest_requests), 1)

        staff_user = UserFactory(is_staff=True)

        # Hit the Programs API twice.
        for _ in range(2):
            utils.get_programs(staff_user)

        # Verify that three requests have been made (one for student, two for staff).
        self.assertEqual(len(httpretty.httpretty.latest_requests), 3)

    def test_get_programs_programs_disabled(self):
        """Verify behavior when programs is disabled."""
        self.create_programs_config(enabled=False)

        actual = utils.get_programs(self.user)
        self.assertEqual(actual, [])

    @mock.patch('edx_rest_api_client.client.EdxRestApiClient.__init__')
    def test_get_programs_client_initialization_failure(self, mock_init):
        """Verify behavior when API client fails to initialize."""
        self.create_programs_config()
        mock_init.side_effect = Exception

        actual = utils.get_programs(self.user)
        self.assertEqual(actual, [])
        self.assertTrue(mock_init.called)

    def test_get_programs_data_retrieval_failure(self):
        """Verify behavior when data can't be retrieved from Programs."""
        self.create_programs_config()
        self.mock_programs_api(status_code=500)

        actual = utils.get_programs(self.user)
        self.assertEqual(actual, [])

    def test_get_program_for_certificates(self):
        """Verify programs data can be retrieved and parsed correctly for certificates."""
        self.create_programs_config()
        self.mock_programs_api()
        program_credentials_data = self._expected_progam_credentials_data()

        actual = utils.get_programs_for_credentials(self.user, program_credentials_data)
        expected = self.PROGRAMS_API_RESPONSE['results'][:2]
        expected[0]['credential_url'] = program_credentials_data[0]['certificate_url']
        expected[1]['credential_url'] = program_credentials_data[1]['certificate_url']

        self.assertEqual(len(actual), 2)
        self.assertEqual(actual, expected)

    def test_get_program_for_certificates_no_data(self):
        """Verify behavior when no programs data is found for the user."""
        self.create_programs_config()
        self.create_credentials_config()
        self.mock_programs_api(data={'results': []})
        program_credentials_data = self._expected_progam_credentials_data()

        actual = utils.get_programs_for_credentials(self.user, program_credentials_data)
        self.assertEqual(actual, [])

    def test_get_program_for_certificates_id_not_exist(self):
        """Verify behavior when no program with the given program_id in
        credentials exists.
        """
        self.create_programs_config()
        self.create_credentials_config()
        self.mock_programs_api()
        credential_data = [
            {
                "id": 1,
                "username": "test",
                "credential": {
                    "credential_id": 1,
                    "program_id": 100
                },
                "status": "awarded",
                "credential_url": "www.example.com"
            }
        ]
        actual = utils.get_programs_for_credentials(self.user, credential_data)
        self.assertEqual(actual, [])


@skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class GetProgramsByRunTests(TestCase):
    """Tests verifying that programs are inverted correctly."""
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        super(GetProgramsByRunTests, cls).setUpClass()

        cls.user = UserFactory()

        course_keys = [
            CourseKey.from_string('some/course/run'),
            CourseKey.from_string('some/other/run'),
        ]

        cls.enrollments = [CourseEnrollmentFactory(user=cls.user, course_id=c) for c in course_keys]
        cls.course_ids = [unicode(c) for c in course_keys]

        organization = factories.Organization()
        joint_programs = sorted([
            factories.Program(
                organizations=[organization],
                course_codes=[
                    factories.CourseCode(run_modes=[
                        factories.RunMode(course_key=cls.course_ids[0]),
                    ]),
                ]
            ) for __ in range(2)
        ], key=lambda p: p['name'])

        cls.programs = joint_programs + [
            factories.Program(
                organizations=[organization],
                course_codes=[
                    factories.CourseCode(run_modes=[
                        factories.RunMode(course_key=cls.course_ids[1]),
                    ]),
                ]
            ),
            factories.Program(
                organizations=[organization],
                course_codes=[
                    factories.CourseCode(run_modes=[
                        factories.RunMode(course_key='yet/another/run'),
                    ]),
                ]
            ),
        ]

    def test_get_programs_by_run(self):
        """Verify that programs are organized by run ID."""
        programs_by_run, course_ids = utils.get_programs_by_run(self.programs, self.enrollments)

        self.assertEqual(programs_by_run[self.course_ids[0]], self.programs[:2])
        self.assertEqual(programs_by_run[self.course_ids[1]], self.programs[2:3])

        self.assertEqual(course_ids, self.course_ids)

    def test_no_programs(self):
        """Verify that the utility can cope with missing programs data."""
        programs_by_run, course_ids = utils.get_programs_by_run([], self.enrollments)
        self.assertEqual(programs_by_run, {})
        self.assertEqual(course_ids, self.course_ids)

    def test_no_enrollments(self):
        """Verify that the utility can cope with missing enrollment data."""
        programs_by_run, course_ids = utils.get_programs_by_run(self.programs, [])
        self.assertEqual(programs_by_run, {})
        self.assertEqual(course_ids, [])


@skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class GetCompletedCoursesTestCase(TestCase):
    """
    Test the get_completed_courses function
    """

    def make_cert_result(self, **kwargs):
        """
        Helper to create dummy results from the certificates API
        """
        result = {
            'username': 'dummy-username',
            'course_key': 'dummy-course',
            'type': 'dummy-type',
            'status': 'dummy-status',
            'download_url': 'http://www.example.com/cert.pdf',
            'grade': '0.98',
            'created': '2015-07-31T00:00:00Z',
            'modified': '2015-07-31T00:00:00Z',
        }
        result.update(**kwargs)
        return result

    @mock.patch(UTILS_MODULE + '.certificate_api.get_certificates_for_user')
    def test_get_completed_courses(self, mock_get_certs_for_user):
        """
        Ensure the function correctly calls to and handles results from the
        certificates API
        """
        student = UserFactory(username='test-username')
        mock_get_certs_for_user.return_value = [
            self.make_cert_result(status='downloadable', type='verified', course_key='downloadable-course'),
            self.make_cert_result(status='generating', type='professional', course_key='generating-course'),
            self.make_cert_result(status='unknown', type='honor', course_key='unknown-course'),
        ]

        result = utils.get_completed_courses(student)
        self.assertEqual(mock_get_certs_for_user.call_args[0], (student.username, ))
        self.assertEqual(result, [
            {'course_id': 'downloadable-course', 'mode': 'verified'},
            {'course_id': 'generating-course', 'mode': 'professional'},
        ])


@attr(shard=2)
@httpretty.activate
@skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TestProgramProgressMeter(ProgramsApiConfigMixin, TestCase):
    """Tests of the program progress utility class."""
    def setUp(self):
        super(TestProgramProgressMeter, self).setUp()

        self.user = UserFactory()
        self.create_programs_config()

        ClientFactory(name=ProgramsApiConfig.OAUTH2_CLIENT_NAME, client_type=CONFIDENTIAL)

    def _mock_programs_api(self, data):
        """Helper for mocking out Programs API URLs."""
        self.assertTrue(httpretty.is_enabled(), msg='httpretty must be enabled to mock Programs API calls.')

        url = ProgramsApiConfig.current().internal_api_url.strip('/') + '/programs/'
        body = json.dumps({'results': data})

        httpretty.register_uri(httpretty.GET, url, body=body, content_type='application/json')

    def _create_enrollments(self, *course_ids):
        """Variadic helper used to create course enrollments."""
        for course_id in course_ids:
            CourseEnrollmentFactory(user=self.user, course_id=course_id)

    def _assert_progress(self, meter, *progresses):
        """Variadic helper used to verify progress calculations."""
        self.assertEqual(meter.progress, list(progresses))

    def _extract_names(self, program, *course_codes):
        """Construct a list containing the display names of the indicated course codes."""
        return [program['course_codes'][cc]['display_name'] for cc in course_codes]

    def _attach_detail_url(self, programs):
        """Add expected detail URLs to a list of program dicts."""
        for program in programs:
            program['detail_url'] = reverse('program_details_view', kwargs={'program_uuid': program['uuid']})

    def test_no_enrollments(self):
        """Verify behavior when programs exist, but no relevant enrollments do."""
        data = [
            factories.Program(
                organizations=[factories.Organization()],
                course_codes=[
                    factories.CourseCode(run_modes=[factories.RunMode()]),
                ]
            ),
        ]
        self._mock_programs_api(data)

        meter = utils.ProgramProgressMeter(self.user)

        self.assertEqual(meter.engaged_programs(), [])
        self._assert_progress(meter)
        self.assertEqual(meter.completed_programs, [])

    def test_no_programs(self):
        """Verify behavior when enrollments exist, but no matching programs do."""
        self._mock_programs_api([])

        self._create_enrollments('org/course/run')
        meter = utils.ProgramProgressMeter(self.user)

        self.assertEqual(meter.engaged_programs(), [])
        self._assert_progress(meter)
        self.assertEqual(meter.completed_programs, [])

    def test_single_program_engagement(self):
        """
        Verify that correct program is returned when the user has a single enrollment
        appearing in one program.
        """
        course_id = 'org/course/run'
        data = [
            factories.Program(
                organizations=[factories.Organization()],
                course_codes=[
                    factories.CourseCode(run_modes=[
                        factories.RunMode(course_key=course_id),
                    ]),
                ]
            ),
            factories.Program(
                organizations=[factories.Organization()],
                course_codes=[
                    factories.CourseCode(run_modes=[factories.RunMode()]),
                ]
            ),
        ]
        self._mock_programs_api(data)

        self._create_enrollments(course_id)
        meter = utils.ProgramProgressMeter(self.user)

        self._attach_detail_url(data)
        program = data[0]
        self.assertEqual(meter.engaged_programs(), [program])
        self._assert_progress(
            meter,
            factories.Progress(
                id=program['id'],
                in_progress=self._extract_names(program, 0)
            )
        )
        self.assertEqual(meter.completed_programs, [])

    def test_mutiple_program_engagement(self):
        """
        Verify that correct programs are returned in the correct order when the user
        has multiple enrollments.
        """
        first_course_id, second_course_id = 'org/first-course/run', 'org/second-course/run'
        data = [
            factories.Program(
                organizations=[factories.Organization()],
                course_codes=[
                    factories.CourseCode(run_modes=[
                        factories.RunMode(course_key=first_course_id),
                    ]),
                ]
            ),
            factories.Program(
                organizations=[factories.Organization()],
                course_codes=[
                    factories.CourseCode(run_modes=[
                        factories.RunMode(course_key=second_course_id),
                    ]),
                ]
            ),
            factories.Program(
                organizations=[factories.Organization()],
                course_codes=[
                    factories.CourseCode(run_modes=[factories.RunMode()]),
                ]
            ),
        ]
        self._mock_programs_api(data)

        self._create_enrollments(second_course_id, first_course_id)
        meter = utils.ProgramProgressMeter(self.user)

        self._attach_detail_url(data)
        programs = data[:2]
        self.assertEqual(meter.engaged_programs(), programs)
        self._assert_progress(
            meter,
            factories.Progress(id=programs[0]['id'], in_progress=self._extract_names(programs[0], 0)),
            factories.Progress(id=programs[1]['id'], in_progress=self._extract_names(programs[1], 0))
        )
        self.assertEqual(meter.completed_programs, [])

    def test_shared_enrollment_engagement(self):
        """
        Verify that correct programs are returned when the user has a single enrollment
        appearing in multiple programs.
        """
        shared_course_id, solo_course_id = 'org/shared-course/run', 'org/solo-course/run'

        joint_programs = sorted([
            factories.Program(
                organizations=[factories.Organization()],
                course_codes=[
                    factories.CourseCode(run_modes=[
                        factories.RunMode(course_key=shared_course_id),
                    ]),
                ]
            ) for __ in range(2)
        ], key=lambda p: p['name'])

        data = joint_programs + [
            factories.Program(
                organizations=[factories.Organization()],
                course_codes=[
                    factories.CourseCode(run_modes=[
                        factories.RunMode(course_key=solo_course_id),
                    ]),
                ]
            ),
            factories.Program(
                organizations=[factories.Organization()],
                course_codes=[
                    factories.CourseCode(run_modes=[factories.RunMode()]),
                ]
            ),
        ]

        self._mock_programs_api(data)

        # Enrollment for the shared course ID created last (most recently).
        self._create_enrollments(solo_course_id, shared_course_id)
        meter = utils.ProgramProgressMeter(self.user)

        self._attach_detail_url(data)
        programs = data[:3]
        self.assertEqual(meter.engaged_programs(), programs)
        self._assert_progress(
            meter,
            factories.Progress(id=programs[0]['id'], in_progress=self._extract_names(programs[0], 0)),
            factories.Progress(id=programs[1]['id'], in_progress=self._extract_names(programs[1], 0)),
            factories.Progress(id=programs[2]['id'], in_progress=self._extract_names(programs[2], 0))
        )
        self.assertEqual(meter.completed_programs, [])

    @mock.patch(UTILS_MODULE + '.get_completed_courses')
    def test_simulate_progress(self, mock_get_completed_courses):
        """Simulate the entirety of a user's progress through a program."""
        first_course_id, second_course_id = 'org/first-course/run', 'org/second-course/run'
        data = [
            factories.Program(
                organizations=[factories.Organization()],
                course_codes=[
                    factories.CourseCode(run_modes=[
                        factories.RunMode(course_key=first_course_id),
                    ]),
                    factories.CourseCode(run_modes=[
                        factories.RunMode(course_key=second_course_id),
                    ]),
                ]
            ),
            factories.Program(
                organizations=[factories.Organization()],
                course_codes=[
                    factories.CourseCode(run_modes=[factories.RunMode()]),
                ]
            ),
        ]
        self._mock_programs_api(data)

        # No enrollments, no program engaged.
        meter = utils.ProgramProgressMeter(self.user)
        self._assert_progress(meter)
        self.assertEqual(meter.completed_programs, [])

        # One enrollment, program engaged.
        self._create_enrollments(first_course_id)
        meter = utils.ProgramProgressMeter(self.user)
        program, program_id = data[0], data[0]['id']
        self._assert_progress(
            meter,
            factories.Progress(
                id=program_id,
                in_progress=self._extract_names(program, 0),
                not_started=self._extract_names(program, 1)
            )
        )
        self.assertEqual(meter.completed_programs, [])

        # Two enrollments, program in progress.
        self._create_enrollments(second_course_id)
        meter = utils.ProgramProgressMeter(self.user)
        self._assert_progress(
            meter,
            factories.Progress(
                id=program_id,
                in_progress=self._extract_names(program, 0, 1)
            )
        )
        self.assertEqual(meter.completed_programs, [])

        # One valid certificate earned, one course code complete.
        mock_get_completed_courses.return_value = [
            {'course_id': first_course_id, 'mode': MODES.verified},
        ]
        meter = utils.ProgramProgressMeter(self.user)
        self._assert_progress(
            meter,
            factories.Progress(
                id=program_id,
                completed=self._extract_names(program, 0),
                in_progress=self._extract_names(program, 1)
            )
        )
        self.assertEqual(meter.completed_programs, [])

        # Invalid certificate earned, still one course code to complete.
        mock_get_completed_courses.return_value = [
            {'course_id': first_course_id, 'mode': MODES.verified},
            {'course_id': second_course_id, 'mode': MODES.honor},
        ]
        meter = utils.ProgramProgressMeter(self.user)
        self._assert_progress(
            meter,
            factories.Progress(
                id=program_id,
                completed=self._extract_names(program, 0),
                in_progress=self._extract_names(program, 1)
            )
        )
        self.assertEqual(meter.completed_programs, [])

        # Second valid certificate obtained, all course codes complete.
        mock_get_completed_courses.return_value = [
            {'course_id': first_course_id, 'mode': MODES.verified},
            {'course_id': second_course_id, 'mode': MODES.verified},
        ]
        meter = utils.ProgramProgressMeter(self.user)
        self._assert_progress(
            meter,
            factories.Progress(
                id=program_id,
                completed=self._extract_names(program, 0, 1)
            )
        )
        self.assertEqual(meter.completed_programs, [program_id])

    @mock.patch(UTILS_MODULE + '.get_completed_courses')
    def test_nonstandard_run_mode_completion(self, mock_get_completed_courses):
        """
        A valid run mode isn't necessarily verified. Verify that a program can
        still be completed when this is the case.
        """
        course_id = 'org/course/run'
        data = [
            factories.Program(
                organizations=[factories.Organization()],
                course_codes=[
                    factories.CourseCode(run_modes=[
                        factories.RunMode(
                            course_key=course_id,
                            mode_slug=MODES.honor
                        ),
                        factories.RunMode(),
                    ]),
                ]
            ),
            factories.Program(
                organizations=[factories.Organization()],
                course_codes=[
                    factories.CourseCode(run_modes=[factories.RunMode()]),
                ]
            ),
        ]
        self._mock_programs_api(data)

        self._create_enrollments(course_id)
        mock_get_completed_courses.return_value = [
            {'course_id': course_id, 'mode': MODES.honor},
        ]
        meter = utils.ProgramProgressMeter(self.user)

        program, program_id = data[0], data[0]['id']
        self._assert_progress(
            meter,
            factories.Progress(id=program_id, completed=self._extract_names(program, 0))
        )
        self.assertEqual(meter.completed_programs, [program_id])

    @mock.patch(UTILS_MODULE + '.get_completed_courses')
    def test_completed_programs(self, mock_get_completed_courses):
        """Verify that completed programs are correctly identified."""
        program_count, course_code_count, run_mode_count = 3, 2, 2
        data = [
            factories.Program(
                organizations=[factories.Organization()],
                course_codes=[
                    factories.CourseCode(run_modes=[factories.RunMode() for _ in range(run_mode_count)])
                    for _ in range(course_code_count)
                ]
            )
            for _ in range(program_count)
        ]
        self._mock_programs_api(data)

        program_ids = []
        course_ids = []
        for program in data:
            program_ids.append(program['id'])

            for course_code in program['course_codes']:
                for run_mode in course_code['run_modes']:
                    course_ids.append(run_mode['course_key'])

        # Verify that no programs are complete.
        meter = utils.ProgramProgressMeter(self.user)
        self.assertEqual(meter.completed_programs, [])

        # "Complete" all programs.
        self._create_enrollments(*course_ids)
        mock_get_completed_courses.return_value = [
            {'course_id': course_id, 'mode': MODES.verified} for course_id in course_ids
        ]

        # Verify that all programs are complete.
        meter = utils.ProgramProgressMeter(self.user)
        self.assertEqual(meter.completed_programs, program_ids)
