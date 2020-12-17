"""Tests covering Credentials signals."""


import ddt
import mock
from django.conf import settings
from django.test import TestCase, override_settings
from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.certificates.tests.factories import GeneratedCertificateFactory
from lms.djangoapps.grades.course_grade_factory import CourseGradeFactory
from lms.djangoapps.grades.tests.utils import mock_passing_grade
from openedx.core.djangoapps.catalog.tests.factories import CourseFactory, CourseRunFactory, ProgramFactory
from openedx.core.djangoapps.credentials.helpers import is_learner_records_enabled
from openedx.core.djangoapps.credentials.signals import is_course_run_in_a_program, send_grade_if_interesting
from openedx.core.djangoapps.site_configuration.tests.factories import SiteConfigurationFactory, SiteFactory
from openedx.core.djangolib.testing.utils import skip_unless_lms
from common.djangoapps.student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory as XModuleCourseFactory

SIGNALS_MODULE = 'openedx.core.djangoapps.credentials.signals'


@ddt.ddt
@skip_unless_lms
@mock.patch(
    'openedx.core.djangoapps.credentials.models.CredentialsApiConfig.is_learner_issuance_enabled',
    new_callable=mock.PropertyMock,
    return_value=True,
)
@mock.patch(SIGNALS_MODULE + '.send_grade_to_credentials')
@mock.patch(SIGNALS_MODULE + '.is_course_run_in_a_program')
class TestCredentialsSignalsSendGrade(TestCase):
    """ Tests for send_grade_if_interesting, the main utility function that sends a grade """

    def setUp(self):
        super(TestCredentialsSignalsSendGrade, self).setUp()
        self.user = UserFactory()
        self.key = CourseKey.from_string(CourseRunFactory()['key'])

    @ddt.data(
        [True, 'verified', 'downloadable'],
        [True, 'professional', 'downloadable'],
        [True, 'no-id-professional', 'downloadable'],
        [True, 'credit', 'downloadable'],
        [True, 'verified', 'notpassing'],
        [True, 'masters', 'downloadable'],
        [True, 'masters', 'notpassing'],
        [False, 'audit', 'downloadable'],
        [False, 'professional', 'generating'],
        [False, 'no-id-professional', 'generating'],
    )
    @ddt.unpack
    def test_send_grade_if_right_cert(self, called, mode, status, mock_is_course_run_in_a_program,
                                      mock_send_grade_to_credentials, _mock_is_learner_issuance_enabled):
        mock_is_course_run_in_a_program.return_value = True

        # Test direct send
        send_grade_if_interesting(self.user, self.key, mode, status, 'A', 1.0)
        self.assertIs(mock_send_grade_to_credentials.delay.called, called)
        mock_send_grade_to_credentials.delay.reset_mock()

        # Test query
        GeneratedCertificateFactory(
            user=self.user,
            course_id=self.key,
            status=status,
            mode=mode
        )
        send_grade_if_interesting(self.user, self.key, None, None, 'A', 1.0)
        self.assertIs(mock_send_grade_to_credentials.delay.called, called)

    def test_send_grade_missing_cert(self, _, mock_send_grade_to_credentials, _mock_is_learner_issuance_enabled):
        send_grade_if_interesting(self.user, self.key, None, None, 'A', 1.0)
        self.assertFalse(mock_send_grade_to_credentials.delay.called)

    @ddt.data([True], [False])
    @ddt.unpack
    def test_send_grade_if_in_a_program(self, in_program, mock_is_course_run_in_a_program,
                                        mock_send_grade_to_credentials, _mock_is_learner_issuance_enabled):
        mock_is_course_run_in_a_program.return_value = in_program
        send_grade_if_interesting(self.user, self.key, 'verified', 'downloadable', 'A', 1.0)
        self.assertIs(mock_send_grade_to_credentials.delay.called, in_program)

    def test_send_grade_queries_grade(self, mock_is_course_run_in_a_program, mock_send_grade_to_credentials,
                                      _mock_is_learner_issuance_enabled):
        mock_is_course_run_in_a_program.return_value = True

        with mock_passing_grade('B', 0.81):
            send_grade_if_interesting(self.user, self.key, 'verified', 'downloadable', None, None)
        self.assertTrue(mock_send_grade_to_credentials.delay.called)
        self.assertEqual(mock_send_grade_to_credentials.delay.call_args[0],
                         (self.user.username, str(self.key), True, 'B', 0.81))
        mock_send_grade_to_credentials.delay.reset_mock()

    @mock.patch.dict(settings.FEATURES, {'ASSUME_ZERO_GRADE_IF_ABSENT_FOR_ALL_TESTS': False})
    def test_send_grade_without_grade(self, mock_is_course_run_in_a_program, mock_send_grade_to_credentials,
                                      _mock_is_learner_issuance_enabled):
        mock_is_course_run_in_a_program.return_value = True
        send_grade_if_interesting(self.user, self.key, 'verified', 'downloadable', None, None)
        self.assertFalse(mock_send_grade_to_credentials.delay.called)

    def test_send_grade_without_issuance_enabled(self, _mock_is_course_run_in_a_program,
                                                 mock_send_grade_to_credentials, mock_is_learner_issuance_enabled):
        mock_is_learner_issuance_enabled.return_value = False
        send_grade_if_interesting(self.user, self.key, 'verified', 'downloadable', None, None)
        self.assertTrue(mock_is_learner_issuance_enabled.called)
        self.assertFalse(mock_send_grade_to_credentials.delay.called)

    def test_send_grade_records_enabled(self, _mock_is_course_run_in_a_program, mock_send_grade_to_credentials,
                                        _mock_is_learner_issuance_enabled):
        site_config = SiteConfigurationFactory.create(
            site_values={'course_org_filter': [self.key.org]}
        )

        # Correctly sent
        send_grade_if_interesting(self.user, self.key, 'verified', 'downloadable', None, None)
        self.assertTrue(mock_send_grade_to_credentials.delay.called)
        mock_send_grade_to_credentials.delay.reset_mock()

        # Correctly not sent
        site_config.site_values['ENABLE_LEARNER_RECORDS'] = False
        site_config.save()
        send_grade_if_interesting(self.user, self.key, 'verified', 'downloadable', None, None)
        self.assertFalse(mock_send_grade_to_credentials.delay.called)

    def test_send_grade_records_disabled_globally(
        self, _mock_is_course_run_in_a_program, mock_send_grade_to_credentials,
        _mock_is_learner_issuance_enabled
    ):
        self.assertTrue(is_learner_records_enabled())
        with override_settings(FEATURES={"ENABLE_LEARNER_RECORDS": False}):
            self.assertFalse(is_learner_records_enabled())
            send_grade_if_interesting(self.user, self.key, 'verified', 'downloadable', None, None)
        self.assertFalse(mock_send_grade_to_credentials.delay.called)


@skip_unless_lms
@mock.patch(SIGNALS_MODULE + '.get_programs')
class TestCredentialsSignalsUtils(TestCase):
    """ Tests helper utility functions in our signal handling. """

    def setUp(self):
        super(TestCredentialsSignalsUtils, self).setUp()
        self.site = SiteFactory()
        self.course_run = CourseRunFactory()
        course = CourseFactory(course_runs=[self.course_run])
        self.data = [ProgramFactory(courses=[course])]

    def test_is_course_run_in_a_program_success(self, mock_get_programs):
        mock_get_programs.return_value = self.data
        self.assertTrue(is_course_run_in_a_program(self.course_run['key']))
        self.assertEqual(mock_get_programs.call_args[0], (self.site,))

    def test_is_course_run_in_a_program_failure(self, mock_get_programs):
        mock_get_programs.return_value = self.data
        course_run2 = CourseRunFactory()
        self.assertFalse(is_course_run_in_a_program(course_run2['key']))


@skip_unless_lms
@mock.patch(SIGNALS_MODULE + '.send_grade_if_interesting')
class TestCredentialsSignalsEmissions(ModuleStoreTestCase):
    """ Tests for whether we are receiving signal emissions correctly. """

    def test_cert_changed(self, mock_send_grade_if_interesting):
        user = UserFactory()

        self.assertFalse(mock_send_grade_if_interesting.called)
        GeneratedCertificateFactory(user=user)
        self.assertTrue(mock_send_grade_if_interesting.called)

    def test_grade_changed(self, mock_send_grade_if_interesting):
        user = UserFactory()
        course = XModuleCourseFactory()

        self.assertFalse(mock_send_grade_if_interesting.called)
        CourseGradeFactory().update(user, course=course)
        self.assertTrue(mock_send_grade_if_interesting.called)
