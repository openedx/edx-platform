"""Tests for the backpopulate_program_credentials management command."""
import json

import ddt
from django.core.management import call_command, CommandError
from django.test import TestCase
from edx_oauth2_provider.tests.factories import ClientFactory
import httpretty
import mock
from provider.constants import CONFIDENTIAL

from certificates.models import CertificateStatuses  # pylint: disable=import-error
from lms.djangoapps.certificates.api import MODES
from lms.djangoapps.certificates.tests.factories import GeneratedCertificateFactory
from openedx.core.djangoapps.programs.models import ProgramsApiConfig
from openedx.core.djangoapps.programs.tests import factories
from openedx.core.djangoapps.programs.tests.mixins import ProgramsApiConfigMixin
from openedx.core.djangolib.testing.utils import skip_unless_lms
from student.tests.factories import UserFactory


COMMAND_MODULE = 'openedx.core.djangoapps.programs.management.commands.backpopulate_program_credentials'


@ddt.ddt
@httpretty.activate
@mock.patch(COMMAND_MODULE + '.award_program_certificates.delay')
@skip_unless_lms
class BackpopulateProgramCredentialsTests(ProgramsApiConfigMixin, TestCase):
    """Tests for the backpopulate_program_credentials management command."""
    course_id, alternate_course_id = 'org/course/run', 'org/alternate/run'

    def setUp(self):
        super(BackpopulateProgramCredentialsTests, self).setUp()

        self.alice = UserFactory()
        self.bob = UserFactory()
        self.oauth2_user = UserFactory()
        self.oauth2_client = ClientFactory(name=ProgramsApiConfig.OAUTH2_CLIENT_NAME, client_type=CONFIDENTIAL)

        # Disable certification to prevent the task from being triggered when
        # setting up test data (i.e., certificates with a passing status), thereby
        # skewing mock call counts.
        self.create_programs_config(enable_certification=False)

    def _link_oauth2_user(self):
        """Helper to link user and OAuth2 client."""
        self.oauth2_client.user = self.oauth2_user
        self.oauth2_client.save()  # pylint: disable=no-member

    def _mock_programs_api(self, data):
        """Helper for mocking out Programs API URLs."""
        self.assertTrue(httpretty.is_enabled(), msg='httpretty must be enabled to mock Programs API calls.')

        url = ProgramsApiConfig.current().internal_api_url.strip('/') + '/programs/'
        body = json.dumps({'results': data})

        httpretty.register_uri(httpretty.GET, url, body=body, content_type='application/json')

    @ddt.data(True, False)
    def test_handle(self, commit, mock_task):
        """Verify that relevant tasks are only enqueued when the commit option is passed."""
        data = [
            factories.Program(
                organizations=[factories.Organization()],
                course_codes=[
                    factories.CourseCode(run_modes=[
                        factories.RunMode(course_key=self.course_id),
                    ]),
                ]
            ),
        ]
        self._mock_programs_api(data)
        self._link_oauth2_user()

        GeneratedCertificateFactory(
            user=self.alice,
            course_id=self.course_id,
            mode=MODES.verified,
            status=CertificateStatuses.downloadable,
        )

        GeneratedCertificateFactory(
            user=self.bob,
            course_id=self.alternate_course_id,
            mode=MODES.verified,
            status=CertificateStatuses.downloadable,
        )

        call_command('backpopulate_program_credentials', commit=commit)

        if commit:
            mock_task.assert_called_once_with(self.alice.username)
        else:
            mock_task.assert_not_called()

    @ddt.data(
        [
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
                    factories.CourseCode(run_modes=[
                        factories.RunMode(course_key=alternate_course_id),
                    ]),
                ]
            ),
        ],
        [
            factories.Program(
                organizations=[factories.Organization()],
                course_codes=[
                    factories.CourseCode(run_modes=[
                        factories.RunMode(course_key=course_id),
                    ]),
                    factories.CourseCode(run_modes=[
                        factories.RunMode(course_key=alternate_course_id),
                    ]),
                ]
            ),
        ],
        [
            factories.Program(
                organizations=[factories.Organization()],
                course_codes=[
                    factories.CourseCode(run_modes=[
                        factories.RunMode(course_key=course_id),
                        factories.RunMode(course_key=alternate_course_id),
                    ]),
                ]
            ),
        ],
    )
    def test_handle_flatten(self, data, mock_task):
        """Verify that program structures are flattened correctly."""
        self._mock_programs_api(data)
        self._link_oauth2_user()

        GeneratedCertificateFactory(
            user=self.alice,
            course_id=self.course_id,
            mode=MODES.verified,
            status=CertificateStatuses.downloadable,
        )

        GeneratedCertificateFactory(
            user=self.bob,
            course_id=self.alternate_course_id,
            mode=MODES.verified,
            status=CertificateStatuses.downloadable,
        )

        call_command('backpopulate_program_credentials', commit=True)

        calls = [
            mock.call(self.alice.username),
            mock.call(self.bob.username)
        ]
        mock_task.assert_has_calls(calls, any_order=True)

    def test_handle_username_dedup(self, mock_task):
        """Verify that only one task is enqueued for a user with multiple eligible certs."""
        data = [
            factories.Program(
                organizations=[factories.Organization()],
                course_codes=[
                    factories.CourseCode(run_modes=[
                        factories.RunMode(course_key=self.course_id),
                        factories.RunMode(course_key=self.alternate_course_id),
                    ]),
                ]
            ),
        ]
        self._mock_programs_api(data)
        self._link_oauth2_user()

        GeneratedCertificateFactory(
            user=self.alice,
            course_id=self.course_id,
            mode=MODES.verified,
            status=CertificateStatuses.downloadable,
        )

        GeneratedCertificateFactory(
            user=self.alice,
            course_id=self.alternate_course_id,
            mode=MODES.verified,
            status=CertificateStatuses.downloadable,
        )

        call_command('backpopulate_program_credentials', commit=True)

        mock_task.assert_called_once_with(self.alice.username)

    def test_handle_mode_slugs(self, mock_task):
        """Verify that mode slugs are taken into account."""
        data = [
            factories.Program(
                organizations=[factories.Organization()],
                course_codes=[
                    factories.CourseCode(run_modes=[
                        factories.RunMode(
                            course_key=self.course_id,
                            mode_slug=MODES.honor
                        ),
                    ]),
                ]
            ),
        ]
        self._mock_programs_api(data)
        self._link_oauth2_user()

        GeneratedCertificateFactory(
            user=self.alice,
            course_id=self.course_id,
            status=CertificateStatuses.downloadable,
        )

        GeneratedCertificateFactory(
            user=self.bob,
            course_id=self.course_id,
            mode=MODES.verified,
            status=CertificateStatuses.downloadable,
        )

        call_command('backpopulate_program_credentials', commit=True)

        mock_task.assert_called_once_with(self.alice.username)

    def test_handle_passing_status(self, mock_task):
        """Verify that only certificates with a passing status are selected."""
        data = [
            factories.Program(
                organizations=[factories.Organization()],
                course_codes=[
                    factories.CourseCode(run_modes=[
                        factories.RunMode(course_key=self.course_id),
                        factories.RunMode(course_key=self.alternate_course_id),
                    ]),
                ]
            ),
        ]
        self._mock_programs_api(data)
        self._link_oauth2_user()

        passing_status = CertificateStatuses.downloadable
        failing_status = CertificateStatuses.notpassing

        self.assertIn(passing_status, CertificateStatuses.PASSED_STATUSES)
        self.assertNotIn(failing_status, CertificateStatuses.PASSED_STATUSES)

        GeneratedCertificateFactory(
            user=self.alice,
            course_id=self.course_id,
            mode=MODES.verified,
            status=passing_status,
        )

        # The alternate course is used here to verify that the status and run_mode
        # queries are being ANDed together correctly.
        GeneratedCertificateFactory(
            user=self.bob,
            course_id=self.alternate_course_id,
            mode=MODES.verified,
            status=failing_status,
        )

        call_command('backpopulate_program_credentials', commit=True)

        mock_task.assert_called_once_with(self.alice.username)

    def test_handle_unlinked_oauth2_user(self, mock_task):
        """Verify that the command fails when no user is associated with the OAuth2 client."""
        data = [
            factories.Program(
                organizations=[factories.Organization()],
                course_codes=[
                    factories.CourseCode(run_modes=[
                        factories.RunMode(course_key=self.course_id),
                    ]),
                ]
            ),
        ]
        self._mock_programs_api(data)

        GeneratedCertificateFactory(
            user=self.alice,
            course_id=self.course_id,
            mode=MODES.verified,
            status=CertificateStatuses.downloadable,
        )

        with self.assertRaises(CommandError):
            call_command('backpopulate_program_credentials')

        mock_task.assert_not_called()

    @mock.patch(COMMAND_MODULE + '.logger.exception')
    def test_handle_enqueue_failure(self, mock_log, mock_task):
        """Verify that failure to enqueue a task doesn't halt execution."""
        def side_effect(username):
            """Simulate failure to enqueue a task."""
            if username == self.alice.username:
                raise Exception

        mock_task.side_effect = side_effect

        data = [
            factories.Program(
                organizations=[factories.Organization()],
                course_codes=[
                    factories.CourseCode(run_modes=[
                        factories.RunMode(course_key=self.course_id),
                    ]),
                ]
            ),
        ]
        self._mock_programs_api(data)
        self._link_oauth2_user()

        GeneratedCertificateFactory(
            user=self.alice,
            course_id=self.course_id,
            mode=MODES.verified,
            status=CertificateStatuses.downloadable,
        )

        GeneratedCertificateFactory(
            user=self.bob,
            course_id=self.course_id,
            mode=MODES.verified,
            status=CertificateStatuses.downloadable,
        )

        call_command('backpopulate_program_credentials', commit=True)

        self.assertTrue(mock_log.called)

        calls = [
            mock.call(self.alice.username),
            mock.call(self.bob.username)
        ]
        mock_task.assert_has_calls(calls, any_order=True)
