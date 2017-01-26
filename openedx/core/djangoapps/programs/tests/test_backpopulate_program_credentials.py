"""Tests for the backpopulate_program_credentials management command."""
import json

import ddt
from django.core.management import call_command, CommandError
from django.test import TestCase
import httpretty
import mock

from certificates.models import CertificateStatuses  # pylint: disable=import-error
from lms.djangoapps.certificates.api import MODES
from lms.djangoapps.certificates.tests.factories import GeneratedCertificateFactory
from openedx.core.djangoapps.programs.tests import factories
from openedx.core.djangoapps.catalog.tests.mixins import CatalogIntegrationMixin
from openedx.core.djangoapps.credentials.tests.mixins import CredentialsApiConfigMixin
from openedx.core.djangolib.testing.utils import skip_unless_lms
from student.tests.factories import UserFactory


COMMAND_MODULE = 'openedx.core.djangoapps.programs.management.commands.backpopulate_program_credentials'


@ddt.ddt
@mock.patch(COMMAND_MODULE + '.get_programs')
@mock.patch(COMMAND_MODULE + '.award_program_certificates.delay')
@skip_unless_lms
class BackpopulateProgramCredentialsTests(CatalogIntegrationMixin, CredentialsApiConfigMixin, TestCase):
    """Tests for the backpopulate_program_credentials management command."""
    course_id, alternate_course_id = 'org/course/run', 'org/alternate/run'

    def setUp(self):
        super(BackpopulateProgramCredentialsTests, self).setUp()

        self.alice = UserFactory()
        self.bob = UserFactory()

        # Disable certification to prevent the task from being triggered when
        # setting up test data (i.e., certificates with a passing status), thereby
        # skewing mock call counts.
        self.create_credentials_config(enable_learner_issuance=False)

        self.catalog_integration = self.create_catalog_integration()
        self.service_user = UserFactory(username=self.catalog_integration.service_username)

    @ddt.data(True, False)
    def test_handle(self, commit, mock_task, mock_get_programs):
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
        mock_get_programs.return_value = data

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
    def test_handle_flatten(self, data, mock_task, mock_get_programs):
        """Verify that program structures are flattened correctly."""
        mock_get_programs.return_value = data

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

    def test_handle_username_dedup(self, mock_task, mock_get_programs):
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
        mock_get_programs.return_value = data

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

    def test_handle_mode_slugs(self, mock_task, mock_get_programs):
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
        mock_get_programs.return_value = data

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

    def test_handle_passing_status(self, mock_task, mock_get_programs):
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
        mock_get_programs.return_value = data

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

    def test_handle_missing_service_user(self, mock_task, __):
        """Verify that the command fails when no service user exists."""
        self.catalog_integration = self.create_catalog_integration(service_username='test')
        with self.assertRaises(CommandError):
            call_command('backpopulate_program_credentials')

        mock_task.assert_not_called()

    @mock.patch(COMMAND_MODULE + '.logger.exception')
    def test_handle_enqueue_failure(self, mock_log, mock_task, mock_get_programs):
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
        mock_get_programs.return_value = data

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
