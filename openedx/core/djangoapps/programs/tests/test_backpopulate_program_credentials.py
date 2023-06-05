"""Tests for the backpopulate_program_credentials management command."""


import ddt
import mock
from django.core.management import call_command
from django.test import TestCase
from opaque_keys.edx.keys import CourseKey
from six.moves import range

from common.djangoapps.course_modes.models import CourseMode
from lms.djangoapps.certificates.api import MODES
from lms.djangoapps.certificates.models import CertificateStatuses
from lms.djangoapps.certificates.tests.factories import GeneratedCertificateFactory
from openedx.core.djangoapps.catalog.tests.factories import (
    CourseFactory,
    CourseRunFactory,
    ProgramFactory,
    generate_course_run_key
)
from openedx.core.djangoapps.catalog.tests.mixins import CatalogIntegrationMixin
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from openedx.core.djangoapps.credentials.tests.mixins import CredentialsApiConfigMixin
from openedx.core.djangolib.testing.utils import skip_unless_lms
from common.djangoapps.student.tests.factories import UserFactory

COMMAND_MODULE = 'openedx.core.djangoapps.programs.management.commands.backpopulate_program_credentials'


@ddt.ddt
@mock.patch(COMMAND_MODULE + '.get_programs')
@mock.patch(COMMAND_MODULE + '.award_program_certificates.delay')
@skip_unless_lms
class BackpopulateProgramCredentialsTests(CatalogIntegrationMixin, CredentialsApiConfigMixin, TestCase):
    """Tests for the backpopulate_program_credentials management command."""
    course_run_key, alternate_course_run_key, course_run_key_no_course_overview = (
        generate_course_run_key() for __ in range(3)
    )
    # Constants for the _get_programs_data hierarchy types used in test_flatten()
    SEPARATE_PROGRAMS = 'separate_programs'
    SEPARATE_COURSES = 'separate_courses'
    SAME_COURSE = 'same_course'

    def setUp(self):
        super(BackpopulateProgramCredentialsTests, self).setUp()

        self.alice = UserFactory()
        self.bob = UserFactory()

        # We need CourseOverview instances to exist for the test courses
        CourseOverviewFactory(id=CourseKey.from_string(self.course_run_key))
        CourseOverviewFactory(id=CourseKey.from_string(self.alternate_course_run_key))

        # Disable certification to prevent the task from being triggered when
        # setting up test data (i.e., certificates with a passing status), thereby
        # skewing mock call counts.
        self.create_credentials_config(enable_learner_issuance=False)

        catalog_integration = self.create_catalog_integration()
        UserFactory(username=catalog_integration.service_username)

    def _get_programs_data(self, hierarchy_type):
        """
        Generate a mock response for get_programs() with the given type of
        course hierarchy.  Dramatically simplifies (and makes consistent
        between test runs) the ddt-generated test_flatten methods.
        """
        if hierarchy_type == self.SEPARATE_PROGRAMS:
            return [
                ProgramFactory(
                    courses=[
                        CourseFactory(course_runs=[
                            CourseRunFactory(key=self.course_run_key),
                        ]),
                    ]
                ),
                ProgramFactory(
                    courses=[
                        CourseFactory(course_runs=[
                            CourseRunFactory(key=self.alternate_course_run_key),
                        ]),
                    ]
                ),
            ]
        elif hierarchy_type == self.SEPARATE_COURSES:
            return [
                ProgramFactory(
                    courses=[
                        CourseFactory(course_runs=[
                            CourseRunFactory(key=self.course_run_key),
                        ]),
                        CourseFactory(course_runs=[
                            CourseRunFactory(key=self.alternate_course_run_key),
                        ]),
                    ]
                ),
            ]
        else:  # SAME_COURSE
            return [
                ProgramFactory(
                    courses=[
                        CourseFactory(course_runs=[
                            CourseRunFactory(key=self.course_run_key),
                            CourseRunFactory(key=self.alternate_course_run_key),
                        ]),
                    ]
                ),
            ]

    @ddt.data(True, False)
    def test_handle(self, commit, mock_task, mock_get_programs):
        """
        Verify that relevant tasks are only enqueued when the commit option is passed.
        """
        data = [
            ProgramFactory(
                courses=[
                    CourseFactory(course_runs=[
                        CourseRunFactory(key=self.course_run_key),
                    ]),
                ]
            ),
        ]
        mock_get_programs.return_value = data

        GeneratedCertificateFactory(
            user=self.alice,
            course_id=self.course_run_key,
            mode=MODES.verified,
            status=CertificateStatuses.downloadable,
        )

        GeneratedCertificateFactory(
            user=self.bob,
            course_id=self.alternate_course_run_key,
            mode=MODES.verified,
            status=CertificateStatuses.downloadable,
        )

        call_command('backpopulate_program_credentials', commit=commit)

        if commit:
            mock_task.assert_called_once_with(self.alice.username)
        else:
            mock_task.assert_not_called()

    def test_handle_professional(self, mock_task, mock_get_programs):
        """ Verify the task can handle both professional and no-id-professional modes. """
        mock_get_programs.return_value = [
            ProgramFactory(
                courses=[
                    CourseFactory(course_runs=[
                        CourseRunFactory(key=self.course_run_key, type='professional'),
                    ]),
                ]
            ),
        ]

        GeneratedCertificateFactory(
            user=self.alice,
            course_id=self.course_run_key,
            mode=CourseMode.PROFESSIONAL,
            status=CertificateStatuses.downloadable,
        )

        GeneratedCertificateFactory(
            user=self.bob,
            course_id=self.course_run_key,
            mode=CourseMode.NO_ID_PROFESSIONAL_MODE,
            status=CertificateStatuses.downloadable,
        )

        call_command('backpopulate_program_credentials', commit=True)

        # The task should be called for both users since professional and no-id-professional are equivalent.
        mock_task.assert_has_calls([mock.call(self.alice.username), mock.call(self.bob.username)], any_order=True)

    @ddt.data(SEPARATE_PROGRAMS, SEPARATE_COURSES, SAME_COURSE)
    def test_handle_flatten(self, hierarchy_type, mock_task, mock_get_programs):
        """Verify that program structures are flattened correctly."""
        mock_get_programs.return_value = self._get_programs_data(hierarchy_type)

        GeneratedCertificateFactory(
            user=self.alice,
            course_id=self.course_run_key,
            mode=MODES.verified,
            status=CertificateStatuses.downloadable,
        )

        GeneratedCertificateFactory(
            user=self.bob,
            course_id=self.alternate_course_run_key,
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
        """
        Verify that only one task is enqueued for a user with multiple eligible
        course run certificates.
        """
        data = [
            ProgramFactory(
                courses=[
                    CourseFactory(course_runs=[
                        CourseRunFactory(key=self.course_run_key),
                        CourseRunFactory(key=self.alternate_course_run_key),
                    ]),
                ]
            ),
        ]
        mock_get_programs.return_value = data

        GeneratedCertificateFactory(
            user=self.alice,
            course_id=self.course_run_key,
            mode=MODES.verified,
            status=CertificateStatuses.downloadable,
        )

        GeneratedCertificateFactory(
            user=self.alice,
            course_id=self.alternate_course_run_key,
            mode=MODES.verified,
            status=CertificateStatuses.downloadable,
        )

        call_command('backpopulate_program_credentials', commit=True)

        mock_task.assert_called_once_with(self.alice.username)

    def test_handle_mode_slugs(self, mock_task, mock_get_programs):
        """
        Verify that course run types are taken into account when identifying
        qualifying course run certificates.
        """
        data = [
            ProgramFactory(
                courses=[
                    CourseFactory(course_runs=[
                        CourseRunFactory(key=self.course_run_key, type='honor'),
                    ]),
                ]
            ),
        ]
        mock_get_programs.return_value = data

        GeneratedCertificateFactory(
            user=self.alice,
            course_id=self.course_run_key,
            mode=MODES.honor,
            status=CertificateStatuses.downloadable,
        )

        GeneratedCertificateFactory(
            user=self.bob,
            course_id=self.course_run_key,
            mode=MODES.verified,
            status=CertificateStatuses.downloadable,
        )

        call_command('backpopulate_program_credentials', commit=True)

        mock_task.assert_called_once_with(self.alice.username)

    def test_handle_passing_status(self, mock_task, mock_get_programs):
        """
        Verify that only course run certificates with a passing status are selected.
        """
        data = [
            ProgramFactory(
                courses=[
                    CourseFactory(course_runs=[
                        CourseRunFactory(key=self.course_run_key),
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
            course_id=self.course_run_key,
            mode=MODES.verified,
            status=passing_status,
        )

        GeneratedCertificateFactory(
            user=self.bob,
            course_id=self.course_run_key,
            mode=MODES.verified,
            status=failing_status,
        )

        call_command('backpopulate_program_credentials', commit=True)

        mock_task.assert_called_once_with(self.alice.username)

    def test_handle_no_course_overview(self, mock_task, mock_get_programs):
        """
        Verify that the task is not enqueued for a user whose only certificate
        is for a course with no CourseOverview.
        """
        data = [
            ProgramFactory(
                courses=[
                    CourseFactory(course_runs=[
                        CourseRunFactory(key=self.course_run_key),
                        CourseRunFactory(key=self.course_run_key_no_course_overview),
                    ]),
                ]
            ),
        ]
        mock_get_programs.return_value = data

        GeneratedCertificateFactory(
            user=self.alice,
            course_id=self.course_run_key,
            mode=MODES.verified,
            status=CertificateStatuses.downloadable,
        )
        GeneratedCertificateFactory(
            user=self.bob,
            course_id=self.course_run_key_no_course_overview,
            mode=MODES.verified,
            status=CertificateStatuses.downloadable,
        )

        call_command('backpopulate_program_credentials', commit=True)

        mock_task.assert_called_once_with(self.alice.username)

    @mock.patch(COMMAND_MODULE + '.logger.exception')
    def test_handle_enqueue_failure(self, mock_log, mock_task, mock_get_programs):
        """Verify that failure to enqueue a task doesn't halt execution."""

        def side_effect(username):
            """Simulate failure to enqueue a task."""
            if username == self.alice.username:
                raise Exception

        mock_task.side_effect = side_effect

        data = [
            ProgramFactory(
                courses=[
                    CourseFactory(course_runs=[
                        CourseRunFactory(key=self.course_run_key),
                    ]),
                ]
            ),
        ]
        mock_get_programs.return_value = data

        GeneratedCertificateFactory(
            user=self.alice,
            course_id=self.course_run_key,
            mode=MODES.verified,
            status=CertificateStatuses.downloadable,
        )

        GeneratedCertificateFactory(
            user=self.bob,
            course_id=self.course_run_key,
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
