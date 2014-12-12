from django.test import TestCase
from django.core.management import call_command
from django.core.management.base import CommandError
from django.conf import settings
from django.test.utils import override_settings
from courseware.tests.tests import TEST_DATA_MONGO_MODULESTORE
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from capa.tests.response_xml_factory import OptionResponseXMLFactory
from opaque_keys.edx.locator import CourseLocator
from student.tests.factories import UserFactory, CourseEnrollmentFactory
from pdfgen.management.commands import create_certs as cc
from pdfgen.tests.factories import GeneratedCertificateFactory
from certificates.models import CertificateStatuses
from mock import patch, MagicMock, ANY
from StringIO import StringIO
import datetime
import os
#from pytz import UTC
from django.utils.timezone import UTC
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape


class GenerateCertCommandTestCase(TestCase):

    def setUp(self):
        self.args_create = ["create", "org/num/run"]
        self.args_delete = ["delete", "org/num/run"]
        self.args_report = ["report", "org/num/run"]
        self.args_publish = ["publish", "org/num/run"]
        self.args_invalid_operation = ["invalid", "org/num/run"]

        self.kwargs = {
            "noop": False, "username": "testuser",
            "debug": True, "prefix": "", "exclude": None}
        self.kwargs_exclusive = {
            "noop": False, "username": "testuser",
            "debug": True, "prefix": "prefix", "exclude": "exclude"}

        self.course_id = "org/num/run"
        self.invalid_course_id = "invalid_course_id"

        patcher0 = patch(
            'pdfgen.management.commands.create_certs.CertificatePDF')
        self.cert_mock = patcher0.start()
        self.addCleanup(patcher0.stop)

    def tearDown(self):
        pass

    @patch('pdfgen.management.commands.create_certs.check_course_id')
    def test_handle_create(self, check_mock):
        cc.Command().handle(*self.args_create, **self.kwargs)

        check_mock.assert_called_with(self.args_create[1])
        self.cert_mock.assert_called_with(
            self.kwargs['username'], CourseLocator.from_string(self.args_create[1]), self.kwargs['debug'],
            self.kwargs['noop'], self.kwargs['prefix'], self.kwargs['exclude'])
        self.cert_mock().create.assert_called_with()

    @patch('pdfgen.management.commands.create_certs.check_course_id')
    def test_handle_delete(self, check_mock):
        cc.Command().handle(*self.args_delete, **self.kwargs)

        check_mock.assert_called_with(self.args_delete[1])
        self.cert_mock.assert_called_with(
            self.kwargs['username'], CourseLocator.from_string(self.args_delete[1]), self.kwargs['debug'],
            self.kwargs['noop'], self.kwargs['prefix'], self.kwargs['exclude'])
        self.cert_mock().delete.assert_called_with()

    @patch('pdfgen.management.commands.create_certs.check_course_id')
    def test_handle_report(self, check_mock):
        cc.Command().handle(*self.args_report, **self.kwargs)

        check_mock.assert_called_with(self.args_report[1])
        self.cert_mock.assert_called_with(
            self.kwargs['username'], CourseLocator.from_string(self.args_report[1]), self.kwargs['debug'],
            self.kwargs['noop'], self.kwargs['prefix'], self.kwargs['exclude'])
        self.cert_mock().report.assert_called_with()

    @patch('pdfgen.management.commands.create_certs.check_course_id')
    def test_handle_publish(self, check_mock):
        cc.Command().handle(*self.args_publish, **self.kwargs)

        check_mock.assert_called_with(self.args_publish[1])
        self.cert_mock.assert_called_with(
            self.kwargs['username'], CourseLocator.from_string(self.args_publish[1]), self.kwargs['debug'],
            self.kwargs['noop'], self.kwargs['prefix'], self.kwargs['exclude'])
        self.cert_mock().publish.assert_called_with()

    @patch('pdfgen.management.commands.create_certs.check_course_id')
    def test_handle_invalid_operation(self, check_mock):
        with self.assertRaises(CommandError) as e:
            cc.Command().handle(*self.args_invalid_operation, **self.kwargs)
        self.assertEqual(e.exception.message, 'Invalid operation.')

    @patch('pdfgen.management.commands.create_certs.check_course_id')
    def test_handle_args_not_specified(self, check_mock):
        with self.assertRaises(CommandError) as e:
            cc.Command().handle(*[], **self.kwargs)

        self.assertEqual(
            e.exception.message,
            'course_id or operation is not specified.')

    @patch('pdfgen.management.commands.create_certs.check_course_id')
    def test_handle_exclusive_option(self, check_mock):
        with self.assertRaises(CommandError) as e:
            cc.Command().handle(*self.args_create, **self.kwargs_exclusive)
        self.assertEqual(
            e.exception.message,
            "-i option and -x option are not specified at the same time.")

    def test_check_course_id(self):
        cc.check_course_id(self.course_id)

        with self.assertRaises(CommandError) as e:
            cc.check_course_id(self.invalid_course_id)

        self.assertEqual(
            e.exception.message,
            "'{}' is an invalid course_id".format(self.invalid_course_id))


@override_settings(
    MODULESTORE=TEST_DATA_MONGO_MODULESTORE,
    PDFGEN_BUCKET_NAME='bucket', PDFGEN_ACCESS_KEY_ID='akey',
    PDFGEN_SECRET_ACCESS_KEY='skey', PDFGEN_CERT_AUTHOR='author',
    PDFGEN_CERT_TITLE='title', PDFGEN_BASE_PDF_DIR='/tmp')
class GenerateCertCommandIntegrationTestCase(TestCase):

    def setUp(self):
        start_date = datetime.datetime(2000, 1, 1, tzinfo=UTC())
        end_date = datetime.datetime(2010, 12, 31, tzinfo=UTC())
        self.course = CourseFactory.create(
            org='org', number='num',
            run='run', display_name='test_course',
            start=start_date, end=end_date)

        UserFactory.reset_sequence()
        self.students = UserFactory.create_batch(3)
        for student in self.students:
            CourseEnrollmentFactory.create(
                user=student, course_id=self.course.id)

        self.course.save()

        self.prog_name = "create_certs"
        self.args_create = ["create", self.course.id.to_deprecated_string()]
        self.args_delete = ["delete", self.course.id.to_deprecated_string()]
        self.args_report = ["report", self.course.id.to_deprecated_string()]
        self.args_publish = ["publish", self.course.id.to_deprecated_string()]
        self.kwargs = {
            "noop": False, "username": False,
            "debug": False, "prefix": "", "exclude": None}

        patcher0 = patch('pdfgen.views.logging')
        self.log_mock = patcher0.start()
        self.addCleanup(patcher0.stop)

        patcher1 = patch('pdfgen.views.S3Connection')
        self.s3conn_mock = patcher1.start()
        self.addCleanup(patcher1.stop)

        patcher2 = patch('pdfgen.views.Key')
        self.s3key_mock = patcher2.start()
        self.addCleanup(patcher2.stop)
        self.s3key_mock().generate_url.return_value = "http://example.com"

        self.pdf_path = settings.PDFGEN_BASE_PDF_DIR + "/" + self.kwargs['prefix'] + "-".join(
            self.course.id.to_deprecated_string().split('/')) + ".pdf"
        self.base_pdf = canvas.Canvas(self.pdf_path, pagesize=landscape(A4))
        self.base_pdf.showPage()
        self.base_pdf.save()

    def tearDown(self):
        os.remove(self.pdf_path)

    @patch('pdfgen.certificate.grades.grade')
    def test_create(self, grade_mock):
        grade_mock.return_value = {"grade": "Pass", "percent": 1}
        with patch('sys.stdout', new_callable=StringIO) as std_mock:
            call_command(self.prog_name, *self.args_create, **self.kwargs)

        grade_mock.assert_any_call(self.students[0], ANY, self.course)
        grade_mock.assert_any_call(self.students[1], ANY, self.course)
        grade_mock.assert_any_call(self.students[2], ANY, self.course)

        self.s3conn_mock.assert_any_call(
            settings.PDFGEN_ACCESS_KEY_ID,
            settings.PDFGEN_SECRET_ACCESS_KEY)
        self.s3conn_mock().get_bucket.assert_any_call(
            settings.PDFGEN_BUCKET_NAME)

        self.s3key_mock.assert_has_calls(ANY)
        self.s3key_mock().set_contents_from_filename.assert_any_call(ANY)
        self.s3key_mock().generate_url.assert_any_call(
            query_auth=False, expires_in=0, force_http=True)
        self.s3key_mock().close.assert_any_call()

        self.assertEqual(std_mock.getvalue(), '\nFetching course data for org/num/run.\nFetching enrollment for students(org/num/run).\nUser robot1: Grade 100% - Pass : Status generating\nUser robot2: Grade 100% - Pass : Status generating\nUser robot3: Grade 100% - Pass : Status generating\n')

    def test_delete(self):
        cert = GeneratedCertificateFactory(
            user=self.students[0], course_id=self.course.id,
            name=self.students[0].username)
        call_command(self.prog_name, *self.args_delete, **self.kwargs)

        self.s3conn_mock.assert_any_call(
            settings.PDFGEN_ACCESS_KEY_ID,
            settings.PDFGEN_SECRET_ACCESS_KEY)
        self.s3conn_mock().get_bucket.assert_any_call(
            settings.PDFGEN_BUCKET_NAME)

        self.s3key_mock.assert_has_calls(ANY)
        self.s3key_mock().exists.assert_any_call()
        self.s3key_mock().delete.assert_any_call()
        self.s3key_mock().close.assert_any_call()

    def test_report(self):
        cert = GeneratedCertificateFactory(
            user=self.students[0],
            course_id=self.course.id, name=self.students[0].username)
        with patch('sys.stdout', new_callable=StringIO) as std_mock:
            call_command(self.prog_name, *self.args_report, **self.kwargs)

        self.assertEqual(std_mock.getvalue(), '\nFetching course data for org/num/run\nSummary Report: Course Name [test_course]\n  User Name [robot1] (Grade :0.0% - None)\n\n\nTotal: Users 3, Pass 0( No grade.)\n')

    def test_publish(self):
        cert = GeneratedCertificateFactory(
            user=self.students[0], course_id=self.course.id,
            name=self.students[0].username, status=CertificateStatuses.generating)
        with patch('sys.stdout', new_callable=StringIO) as std_mock:
            call_command(self.prog_name, *self.args_publish, **self.kwargs)

        self.assertEqual(std_mock.getvalue(), "\nFetching course data for org/num/run\nFetching enrollment for students(org/num/run).\nPublish robot1's certificate : Status downloadable\n")
