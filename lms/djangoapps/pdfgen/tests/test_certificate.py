from django.test import TestCase
from mock import MagicMock, patch, ANY, mock_open
from django.contrib.auth.models import User
from opaque_keys.edx.locator import CourseLocator
from student.tests.factories import UserFactory, UserProfileFactory
from pdfgen.tests.factories import GeneratedCertificateFactory
from pdfgen.certificate import CertificatePDF, CertPDFException
from django.test.client import RequestFactory
from student.models import UserStanding
from certificates.models import CertificateStatuses
from django.test.utils import override_settings
import json
import itertools


class CertificatePDF_create_TestCase(TestCase):
    def setUp(self):
        self.user = "testusername"
        self.course_id = CourseLocator.from_string("org/num/run")
        self.debug = False
        self.noop = False
        self.student = UserFactory.create()
        self.course_name = "testcoursename"
        self.cert = GeneratedCertificateFactory.build(status="downloadable")
        self.grade = {"grade": "Pass", "percent": 1}
        self.invalid_grade = {"grade": None, "percent": 1}
        self.file_prefix = ""
        self.exclude = None

        request_factory = RequestFactory()
        self.request = request_factory.get('/')
        self.request.session = {}

        patcher0 = patch('pdfgen.views.logging')
        self.log_mock = patcher0.start()
        self.addCleanup(patcher0.stop)

    @patch('pdfgen.certificate.CertificatePDF._create_cert_pdf')
    @patch('pdfgen.certificate.CertificatePDF._create_request')
    @patch('pdfgen.certificate.courses.get_course_by_id')
    @patch('pdfgen.certificate.CertificatePDF._get_students')
    def test_create(self, students_mock, course_mock, request_mock, pdf_mock):
        students_mock().iterator.return_value = itertools.repeat(self.student, 1)
        course_mock().has_ended.return_value = True

        cert = CertificatePDF(self.user, self.course_id, self.debug,
                              self.noop, self.file_prefix, self.exclude)
        cert.create()

        students_mock.assert_called_with()
        course_mock.assert_called_with(self.course_id)
        request_mock.assert_called_once_with()
        pdf_mock.assert_called_once_with(self.student, request_mock(), course_mock())

    @patch('pdfgen.certificate.CertificatePDF._create_request')
    @patch('pdfgen.certificate.courses.get_course_by_id')
    @patch('pdfgen.certificate.CertificatePDF._get_students')
    def test_create_not_ended(self, students_mock, course_mock, request_mock):
        course_mock().has_ended = lambda: False
        with self.assertRaises(CertPDFException) as e:
            cert = CertificatePDF(self.user, self.course_id, self.debug,
                                  self.noop, self.file_prefix, self.exclude)
            cert.create()

        self.assertEqual(e.exception.message, 'This couse is not ended.')
        students_mock.assert_called_once_with()
        course_mock.assert_called_with(self.course_id)
        request_mock.assert_called_once_with()

    @patch('pdfgen.certificate.create_cert_pdf',
           return_value=json.dumps({"download_url": "http://s3/test.pdf"}))
    @patch('pdfgen.certificate.CertificatePDF._make_hashkey')
    @patch('pdfgen.certificate.CertificateWhitelist.objects.filter')
    @patch('pdfgen.certificate.UserProfile.objects.get')
    @patch('pdfgen.certificate.grades.grade')
    @patch('pdfgen.certificate.GeneratedCertificate.objects.get_or_create')
    def test_create_cert_pdf(self, gen_mock, grade_mock, profile_mock,
                             white_mock, hash_mock, cert_mock):

        white_mock().exists = lambda: True
        gen_mock.return_value = (self.cert, True)
        grade_mock.return_value = self.grade
        course_mock = MagicMock()

        cert = CertificatePDF(self.user, self.course_id, self.debug,
                              self.noop, self.file_prefix, self.exclude)
        cert._create_cert_pdf(self.student, self.request, course_mock)

        gen_mock.assert_called_once_with(course_id=self.course_id, user=self.student)
        grade_mock.assert_called_with(ANY, self.request, course_mock)
        profile_mock.assert_called_once_with(user=self.student)
        white_mock.assert_called_with(
            user=self.student, course_id=self.course_id, whitelist=True)
        hash_mock.assert_called_once_with(self.course_id.to_deprecated_string() + self.student.username)
        cert_mock.assert_called_once_with(
            self.student.username, self.course_id, self.cert.key, self.cert.name,
            course_mock.display_name, self.grade['percent'], self.file_prefix)

    @patch('pdfgen.certificate.create_cert_pdf',
           return_value=json.dumps({"download_url": "http://s3/test.pdf"}))
    @patch('pdfgen.certificate.CertificatePDF._make_hashkey')
    @patch('pdfgen.certificate.CertificateWhitelist.objects.filter')
    @patch('pdfgen.certificate.UserProfile.objects.get')
    @patch('pdfgen.certificate.grades.grade')
    @patch('pdfgen.certificate.GeneratedCertificate.objects.get_or_create')
    def test_create_cert_pdf_not_in_whitelist_and_not_graded(
            self, gen_mock, grade_mock, profile_mock, white_mock,
            hash_mock, cert_mock):

        cert_dummy = MagicMock()
        white_mock().exists = lambda: False
        gen_mock.return_value = (cert_dummy, True)
        grade_mock.return_value = {"grade": None, "percent": 0}
        course_mock = MagicMock()

        cert = CertificatePDF(self.user, self.course_id, self.debug,
                              self.noop, self.file_prefix, self.exclude)
        cert._create_cert_pdf(self.student, self.request, course_mock)

        cert_dummy.save.assert_called_once_with()
        self.assertEqual(cert_dummy.status, CertificateStatuses.notpassing)

    @patch('pdfgen.certificate.create_cert_pdf',
           return_value=json.dumps({"download_url": "http://s3/test.pdf"}))
    @patch('pdfgen.certificate.CertificatePDF._make_hashkey')
    @patch('pdfgen.certificate.CertificateWhitelist.objects.filter')
    @patch('pdfgen.certificate.UserProfile.objects.get')
    @patch('pdfgen.certificate.grades.grade')
    @patch('pdfgen.certificate.GeneratedCertificate.objects.get_or_create')
    def test_create_cert_pdf_not_in_whitelist_and_not_graded_with_noop(
            self, gen_mock, grade_mock, profile_mock, white_mock,
            hash_mock, cert_mock):

        cert_dummy = MagicMock()
        white_mock().exists = lambda: False
        gen_mock.return_value = (cert_dummy, True)
        grade_mock.return_value = {"grade": None, "percent": 0}
        course_mock = MagicMock()

        cert = CertificatePDF(self.user, self.course_id, self.debug,
                              True, self.file_prefix, self.exclude)
        cert._create_cert_pdf(self.student, self.request, course_mock)

        self.assertEqual(cert_dummy.save.call_count, 0)
        self.assertEqual(cert_dummy.status, CertificateStatuses.notpassing)

    @patch('pdfgen.certificate.create_cert_pdf',
           return_value=json.dumps({"download_url": "http://s3/test.pdf"}))
    @patch('pdfgen.certificate.CertificatePDF._make_hashkey')
    @patch('pdfgen.certificate.CertificateWhitelist.objects.filter')
    @patch('pdfgen.certificate.UserProfile.objects.get')
    @patch('pdfgen.certificate.grades.grade')
    @patch('pdfgen.certificate.GeneratedCertificate.objects.get_or_create')
    def test_create_cert_pdf_allow_certificate_is_false(
            self, gen_mock, grade_mock, profile_mock, white_mock,
            hash_mock, cert_mock):

        cert_dummy = MagicMock()
        profile_mock.return_value = UserProfileFactory.build(
            user=self.student, allow_certificate=False)
        white_mock().exists = lambda: True
        gen_mock.return_value = (cert_dummy, True)
        grade_mock.return_value = self.grade
        course_mock = MagicMock()

        cert = CertificatePDF(self.user, self.course_id, self.debug,
                              self.noop, self.file_prefix, self.exclude)
        cert._create_cert_pdf(self.student, self.request, course_mock)

        gen_mock.assert_called_once_with(course_id=self.course_id, user=self.student)
        grade_mock.assert_called_with(ANY, self.request, course_mock)
        profile_mock.assert_called_once_with(user=self.student)
        white_mock.assert_called_with(
            user=self.student, course_id=self.course_id, whitelist=True)
        cert_dummy.save.assert_called_once_with()
        self.assertEqual(cert_dummy.status, CertificateStatuses.restricted)

    @patch('pdfgen.certificate.create_cert_pdf',
           return_value=json.dumps({"download_url": "http://s3/test.pdf"}))
    @patch('pdfgen.certificate.CertificatePDF._make_hashkey')
    @patch('pdfgen.certificate.CertificateWhitelist.objects.filter')
    @patch('pdfgen.certificate.UserProfile.objects.get')
    @patch('pdfgen.certificate.grades.grade')
    @patch('pdfgen.certificate.GeneratedCertificate.objects.get_or_create')
    def test_create_cert_pdf_allow_certificate_is_false_with_noop(
            self, gen_mock, grade_mock, profile_mock, white_mock,
            hash_mock, cert_mock):

        cert_dummy = MagicMock()
        profile_mock.return_value = UserProfileFactory.build(
            user=self.student, allow_certificate=False)
        white_mock().exists = lambda: True
        gen_mock.return_value = (cert_dummy, True)
        grade_mock.return_value = self.grade
        course_mock = MagicMock()

        cert = CertificatePDF(self.user, self.course_id, self.debug,
                              True, self.file_prefix, self.exclude)
        cert._create_cert_pdf(self.student, self.request, course_mock)

        gen_mock.assert_called_once_with(course_id=self.course_id, user=self.student)
        grade_mock.assert_called_with(ANY, self.request, course_mock)
        profile_mock.assert_called_once_with(user=self.student)
        white_mock.assert_called_with(
            user=self.student, course_id=self.course_id, whitelist=True)
        self.assertEqual(cert_dummy.save.call_count, 0)
        self.assertEqual(cert_dummy.status, CertificateStatuses.restricted)

    @patch('pdfgen.certificate.create_cert_pdf',
           return_value=json.dumps({"error": "error message"}))
    @patch('pdfgen.certificate.CertificatePDF._make_hashkey')
    @patch('pdfgen.certificate.CertificateWhitelist.objects.filter')
    @patch('pdfgen.certificate.UserProfile.objects.get')
    @patch('pdfgen.certificate.grades.grade')
    @patch('pdfgen.certificate.GeneratedCertificate.objects.get_or_create')
    def test_create_cert_pdf_return_error(
            self, gen_mock, grade_mock, profile_mock,
            white_mock, hash_mock, cert_mock):

        white_mock().exists = lambda: True
        gen_mock.return_value = (self.cert, True)
        grade_mock.return_value = self.grade
        course_mock = MagicMock()

        cert = CertificatePDF(self.user, self.course_id, self.debug,
                              self.noop, self.file_prefix, self.exclude)
        cert._create_cert_pdf(self.student, self.request, course_mock)

        gen_mock.assert_called_once_with(course_id=self.course_id, user=self.student)
        grade_mock.assert_called_with(ANY, self.request, course_mock)
        profile_mock.assert_called_once_with(user=self.student)
        white_mock.assert_called_with(
            user=self.student, course_id=self.course_id, whitelist=True)
        hash_mock.assert_called_once_with(self.course_id.to_deprecated_string() + self.student.username)
        cert_mock.assert_called_once_with(
            self.student.username, self.course_id, self.cert.key, self.cert.name,
            course_mock.display_name, self.grade['percent'], self.file_prefix)

        cert2 = CertificatePDF(self.user, self.course_id, self.debug,
                               True, self.file_prefix, self.exclude)
        cert2._create_cert_pdf(self.student, self.request, course_mock)


class CertificatePDF_delete_TestCase(TestCase):

    def setUp(self):
        self.user = "testusername"
        self.course_id = CourseLocator.from_string("org/num/run")
        self.debug = False
        self.noop = False
        self.file_prefix = ""
        self.exclude = None

        self.student = UserFactory.create()
        self.cert = GeneratedCertificateFactory.build(
            user=self.student, status="downloadable")

    @patch('pdfgen.certificate.delete_cert_pdf',
           return_value=json.dumps({"error": None}))
    @patch('pdfgen.certificate.GeneratedCertificate.objects.filter')
    @patch('pdfgen.certificate.CertificatePDF._get_students')
    def test_delete(self, st_mock, gen_mock, del_mock):
        gen_mock().iterator.return_value = itertools.repeat(self.cert, 1)
        st_mock().iterator.return_value = itertools.repeat(self.student, 1)

        cert = CertificatePDF(self.user, self.course_id, self.debug,
                              self.noop, self.file_prefix, self.exclude)
        cert.delete()

        st_mock.assert_called_with()
        gen_mock.assert_called_with(
            user=self.student, course_id=self.course_id)
        del_mock.assert_called_once_with(
            self.student.username, self.course_id, ANY)

    @patch('pdfgen.certificate.delete_cert_pdf',
           return_value=json.dumps({"error": None}))
    @patch('pdfgen.certificate.GeneratedCertificate.objects.filter')
    @patch('pdfgen.certificate.CertificatePDF._get_students')
    def test_delete_noop(self, st_mock, gen_mock, del_mock):
        gen_mock().iterator.return_value = itertools.repeat(self.cert, 1)
        st_mock().iterator.return_value = itertools.repeat(self.student, 1)

        cert = CertificatePDF(self.user, self.course_id, self.debug,
                              True, self.file_prefix, self.exclude)
        cert.delete()

        st_mock.assert_called_with()
        gen_mock.assert_called_with(
            user=self.student, course_id=self.course_id)
        self.assertEqual(del_mock.call_count, 0)

    @patch('pdfgen.certificate.delete_cert_pdf',
           return_value=json.dumps({"error": "error"}))
    @patch('pdfgen.certificate.GeneratedCertificate.objects.filter')
    @patch('pdfgen.certificate.CertificatePDF._get_students')
    def test_delete_response_error(self, st_mock, gen_mock, del_mock):
        gen_mock().iterator.return_value = itertools.repeat(self.cert, 1)
        st_mock().iterator.return_value = itertools.repeat(self.student, 1)

        cert = CertificatePDF(self.user, self.course_id, self.debug,
                              self.noop, self.file_prefix, self.exclude)
        cert.delete()

        st_mock.assert_called_with()
        gen_mock.assert_called_with(
            user=self.student, course_id=self.course_id)
        del_mock.assert_called_once_with(
            self.student.username, self.course_id, ANY)

    @patch('pdfgen.certificate.delete_cert_pdf',
           return_value=json.dumps({"error": None}))
    @patch('pdfgen.certificate.GeneratedCertificate.objects.filter')
    @patch('pdfgen.certificate.CertificatePDF._get_students')
    def test_delete_not_coverd_status(self, st_mock, gen_mock, del_mock):
        cert_dummy = MagicMock()
        cert_dummy.status = CertificateStatuses.notpassing
        gen_mock().iterator.return_value = itertools.repeat(cert_dummy, 1)
        st_mock().iterator.return_value = itertools.repeat(self.student, 1)

        cert = CertificatePDF(self.user, self.course_id, self.debug,
                              self.noop, self.file_prefix, self.exclude)
        cert.delete()

        st_mock.assert_called_with()
        gen_mock.assert_called_with(
            user=self.student, course_id=self.course_id)
        self.assertEqual(del_mock.call_count, 0)


class CertificatePDF_report_TestCase(TestCase):

    def setUp(self):
        self.user = "testusername"
        self.course_id = CourseLocator.from_string("org/num/run")
        self.debug = False
        self.noop = False
        self.file_prefix = ""
        self.exclude = None

        self.student = UserFactory.create()
        self.cert = GeneratedCertificateFactory.build(
            user=self.student, status="downloadable")

        self.summary = [
            {"display_name": "section_name",
             "sections": [{
                 "display_name": "subsec_name",
                 "format": "HW", "section_total": [10, 10],
                 "scores": [
                     (10, 10, True, "unit_name")]}]}]
        self.grade = {"grade": "Pass", "percent": 1}
        self.invalid_grade = {"grade": None, "percent": 1}
        self.total = {'users': 0, 'pass': 0, 'notpass': 0}
        self.total_with_grade = {
            'users': 0, 'pass': 0, 'notpass': 0, 'Pass': 0}
        self.total_items = {
            'users': 3, 'pass': 2, 'notpass': 1, 'A': 1, 'B': 1}

    @patch('pdfgen.certificate.CertificatePDF._report_total')
    @patch('pdfgen.certificate.CertificatePDF._add_total')
    @patch('pdfgen.certificate.CertificatePDF._report_summary')
    @patch('pdfgen.certificate.grades.progress_summary')
    @patch('pdfgen.certificate.grades.grade')
    @patch('pdfgen.certificate.GeneratedCertificate.objects.filter')
    @patch('pdfgen.certificate.CertificatePDF._create_request')
    @patch('pdfgen.certificate.courses.get_course_by_id')
    @patch('pdfgen.certificate.CertificatePDF._get_students')
    def test_report(
            self, st_mock, crs_mock, req_mock,
            gen_mock, grade_mock, pg_mock, sum_mock, tot_mock, rep_mock):

        gen_mock().iterator.return_value = itertools.repeat(self.cert, 1)
        st_mock().iterator.return_value = itertools.repeat(self.student, 1)

        cert = CertificatePDF(self.user, self.course_id, self.debug,
                              self.noop, self.file_prefix, self.exclude)
        cert.report()

        st_mock.assert_called_with()
        crs_mock.assert_called_once_with(self.course_id)
        req_mock.assert_called_once_with()
        gen_mock.assert_called_with(
            user=self.student, course_id=self.course_id)
        grade_mock.assert_called_once_with(self.cert.user, ANY, ANY)
        pg_mock.assert_called_once_with(ANY, ANY, ANY)
        sum_mock.assert_called_once_with(ANY)
        tot_mock.assert_called_once_with(ANY, ANY, ANY)
        rep_mock.assert_called_once_with(ANY)

    @patch('pdfgen.certificate.CertificatePDF._dprint')
    def test_report_summary(self, dprint_mock):
        cert = CertificatePDF(self.user, self.course_id, self.debug,
                              self.noop, self.file_prefix, self.exclude)
        cert._report_summary(self.summary)

        dprint_mock.assert_called_once_with(ANY)

    def test_add_total(self):
        cert = CertificatePDF(self.user, self.course_id, self.debug,
                              self.noop, self.file_prefix, self.exclude)
        cert._add_total(self.user, self.grade, self.total)
        self.assertEqual(
            self.total, {'Pass': 1, 'notpass': 0, 'users': 0, 'pass': 1})

    def test_add_total_with_grade(self):
        cert = CertificatePDF(self.user, self.course_id, self.debug,
                              self.noop, self.file_prefix, self.exclude)
        cert._add_total(self.user, self.grade, self.total_with_grade)
        self.assertEqual(
            self.total_with_grade, {
                'Pass': 1, 'notpass': 0, 'users': 0, 'pass': 1})

    def test_add_total_invalid_grade(self):
        cert = CertificatePDF(self.user, self.course_id, self.debug,
                              self.noop, self.file_prefix, self.exclude)
        cert._add_total(self.user, self.invalid_grade, self.total_with_grade)
        self.assertEqual(
            self.total_with_grade, {
                'Pass': 0, 'notpass': 1, 'users': 0, 'pass': 0})

    def test_report_total(self):
        cert = CertificatePDF(self.user, self.course_id, self.debug,
                              self.noop, self.file_prefix, self.exclude)
        cert._report_total(self.total_items)
        self.assertEqual(self.total_items, {'A': 1, 'B': 1})

    def test_report_total_none(self):
        cert = CertificatePDF(self.user, self.course_id, self.debug,
                              self.noop, self.file_prefix, self.exclude)
        cert._report_total(self.total)
        self.assertEqual(self.total, {})


class CertificatePDF_publish_TestCase(TestCase):
    def setUp(self):
        self.user = "testusername"
        self.course_id = CourseLocator.from_string("org/num/run")
        self.debug = False
        self.noop = False
        self.file_prefix = ""
        self.exclude = None

        self.student = UserFactory.create()
        self.cert = MagicMock()

    @patch('pdfgen.certificate.GeneratedCertificate.objects.filter')
    @patch('pdfgen.certificate.courses.get_course_by_id')
    @patch('pdfgen.certificate.CertificatePDF._get_students')
    def test_publish(self, st_mock, crs_mock, gen_mock):
        gen_mock().iterator.return_value = itertools.repeat(self.cert, 1)
        st_mock().iterator.return_value = itertools.repeat(self.student, 1)

        cert = CertificatePDF(self.user, self.course_id, self.debug,
                              self.noop, self.file_prefix, self.exclude)
        cert.publish()

        st_mock.assert_called_with()
        crs_mock.assert_called_once_with(self.course_id)
        gen_mock.assert_called_with(
            user=self.student, course_id=self.course_id,
            status=CertificateStatuses.generating)
        self.cert.save.assert_called_once_with()
        self.assertEqual(self.cert.status, CertificateStatuses.downloadable)

    @patch('pdfgen.certificate.GeneratedCertificate.objects.filter')
    @patch('pdfgen.certificate.courses.get_course_by_id')
    @patch('pdfgen.certificate.CertificatePDF._get_students')
    def test_publish_with_noop(self, st_mock, crs_mock, gen_mock):
        gen_mock().iterator.return_value = itertools.repeat(self.cert, 1)
        st_mock().iterator.return_value = itertools.repeat(self.student, 1)

        cert = CertificatePDF(self.user, self.course_id, self.debug,
                              True, self.file_prefix, self.exclude)
        cert.publish()

        st_mock.assert_called_with()
        crs_mock.assert_called_once_with(self.course_id)
        gen_mock.assert_called_with(
            user=self.student, course_id=self.course_id,
            status=CertificateStatuses.generating)
        self.assertEqual(self.cert.save.call_count, 0)

    @patch('pdfgen.certificate.GeneratedCertificate.objects.filter')
    @patch('pdfgen.certificate.courses.get_course_by_id')
    @patch('pdfgen.certificate.CertificatePDF._get_students')
    def test_publish_not_ended(self, st_mock, crs_mock, gen_mock):
        gen_mock().iterator.return_value = itertools.repeat(self.cert, 1)
        st_mock().iterator.return_value = itertools.repeat(self.student, 1)
        crs_mock().has_ended.return_value = False

        with self.assertRaises(CertPDFException) as e:
            cert = CertificatePDF(self.user, self.course_id, self.debug,
                                  self.noop, self.file_prefix, self.exclude)
            cert.publish()

        self.assertEqual(e.exception.message, 'This couse is not ended.')
        st_mock.assert_called_with()
        crs_mock.assert_called_with(self.course_id)

    @patch('pdfgen.certificate.GeneratedCertificate.objects.filter')
    @patch('pdfgen.certificate.courses.get_course_by_id')
    @patch('pdfgen.certificate.CertificatePDF._get_students')
    def test_publish_download_url_is_empty(self, st_mock, crs_mock, gen_mock):
        self.cert.download_url = ''
        gen_mock().iterator.return_value = itertools.repeat(self.cert, 1)
        st_mock().iterator.return_value = itertools.repeat(self.student, 1)

        cert = CertificatePDF(self.user, self.course_id, self.debug,
                              self.noop, self.file_prefix, self.exclude)
        cert.publish()

        st_mock.assert_called_with()
        crs_mock.assert_called_once_with(self.course_id)
        gen_mock.assert_called_with(
            user=self.student, course_id=self.course_id,
            status=CertificateStatuses.generating)
        self.assertEqual(self.cert.save.call_count, 0)


class CertificatePDF_other_TestCase(TestCase):
    def setUp(self):
        self.user = "testusername"
        self.course_id = CourseLocator.from_string("org/num/run")
        self.debug = False
        self.noop = False
        self.file_prefix = ""
        self.exclude = None
        self.seed = "seed"

    def test_dprint(self):
        cert = CertificatePDF(self.user, self.course_id, True,
                              self.noop, self.file_prefix, self.exclude)
        cert._dprint(msg="message")

    def test_dprint_newline_false(self):
        cert = CertificatePDF(self.user, self.course_id, True,
                              self.noop, self.file_prefix, self.exclude)
        cert._dprint(msg="message", newline=False)

    def test_create_request(self):
        cert = CertificatePDF(self.user, self.course_id, self.debug,
                              self.noop, self.file_prefix, self.exclude)
        cert._create_request()

    def test_make_hashkey(self):
        cert = CertificatePDF(self.user, self.course_id, self.debug,
                              self.noop, self.file_prefix, self.exclude)
        result = cert._make_hashkey(self.seed)
        self.assertRegexpMatches(result, '[a-zA-Z0-9]{32}')

    def test_make_hashkey_no_args(self):
        with self.assertRaises(TypeError):
            cert = CertificatePDF(self.user, self.course_id, self.debug,
                                  self.noop, self.file_prefix, self.exclude)
            cert._make_hashkey()


class CertificatePDF_get_students_TestCase(TestCase):
    def setUp(self):
        self.user = "testusername"
        self.course_id = CourseLocator.from_string("org/num/run")
        self.debug = False
        self.noop = False
        self.file_prefix = ""
        self.exclude = None

        self.mail = "testusername@example.com"
        self.students = UserFactory.create_batch(3)

    @patch('pdfgen.certificate.User.objects.filter')
    def test_get_students_all(self, user_mock):
        user_mock().filter().exclude.return_value = self.students
        cert = CertificatePDF(None, self.course_id, self.debug,
                              self.noop, self.file_prefix, self.exclude)
        return_students = cert._get_students()

        self.assertEqual(return_students, self.students)
        user_mock.assert_called_with(
            courseenrollment__course_id__exact=self.course_id)
        user_mock().filter.assert_called_with(is_active=1)
        user_mock().filter().exclude.assert_called_with(
            standing__account_status__exact=UserStanding.ACCOUNT_DISABLED)

    @patch('pdfgen.certificate.User.objects.filter')
    def test_get_students_by_username(self, user_mock):
        user_mock.return_value = self.students
        cert = CertificatePDF(self.user, self.course_id, self.debug,
                              self.noop, self.file_prefix, self.exclude)
        return_students = cert._get_students()

        self.assertEqual(return_students, self.students)
        user_mock.assert_called_once_with(
            username=self.user, courseenrollment__course_id=self.course_id)

    @patch('pdfgen.certificate.User.objects.filter')
    def test_get_students_by_email(self, user_mock):
        user_mock.return_value = self.students
        cert = CertificatePDF(self.mail, self.course_id, self.debug,
                              self.noop, self.file_prefix, self.exclude)
        return_students = cert._get_students()

        self.assertEqual(return_students, self.students)
        user_mock.assert_called_once_with(
            email=self.mail, courseenrollment__course_id=self.course_id)

    @override_settings(PDFGEN_BASE_PDF_DIR="/tmp")
    @patch('pdfgen.certificate.CertificatePDF._get_students_list')
    @patch('pdfgen.certificate.User.objects.filter')
    def test_get_students_with_include_list(self, user_mock, list_mock):
        act_mock = MagicMock()
        act_mock.filter.return_value = self.students
        user_mock().filter().exclude.return_value = act_mock

        cert = CertificatePDF(None, self.course_id, self.debug,
                              self.noop, "prefix-", self.exclude)
        return_students = cert._get_students()

        self.assertEqual(return_students, self.students)
        list_mock.assert_called_with("/tmp/prefix-org-num-run.list")
        user_mock.assert_called_with(
            courseenrollment__course_id__exact=self.course_id)

    @override_settings(PDFGEN_BASE_PDF_DIR="/tmp")
    @patch('pdfgen.certificate.CertificatePDF._get_students_list')
    @patch('pdfgen.certificate.User.objects.filter')
    def test_get_students_with_exclude_list(self, user_mock, list_mock):
        act_mock = MagicMock()
        act_mock.exclude.return_value = self.students
        user_mock().filter().exclude.return_value = act_mock

        cert = CertificatePDF(None, self.course_id, self.debug,
                              self.noop, self.file_prefix, "/tmp/exclude")
        return_students = cert._get_students()

        self.assertEqual(return_students, self.students)
        list_mock.assert_called_with("/tmp/exclude")
        user_mock.assert_called_with(
            courseenrollment__course_id__exact=self.course_id)

    @patch('pdfgen.certificate.User.objects.filter')
    def test_get_students_dose_not_exists(self, user_mock):
        user_mock().filter().exclude.return_value = []

        with self.assertRaises(CertPDFException) as e:
            cert = CertificatePDF(None, self.course_id, self.debug,
                                  self.noop, self.file_prefix, self.exclude)
            return_students = cert._get_students()

        self.assertEqual(e.exception.message,
                         "A user targeted for the issuance of certificate does not exist.")
        user_mock.assert_called_with(
            courseenrollment__course_id__exact=self.course_id)
        user_mock().filter.assert_called_with(is_active=1)
        user_mock().filter().exclude.assert_called_with(
            standing__account_status__exact=UserStanding.ACCOUNT_DISABLED)

    @patch('pdfgen.certificate.os.path.isfile', return_value=True)
    def test_get_students_list(self, isf_mock):
        with patch('pdfgen.certificate.open',
                   mock_open(), create=True) as open_mock:

            open_mock().__iter__.return_value = iter(
                ['user1\n', 'user2\n', 'user3\n'])
            cert = CertificatePDF(
                None, self.course_id, self.debug,
                self.noop, self.file_prefix, self.exclude)
            return_list = cert._get_students_list("/tmp/dummy")

        isf_mock.assert_called_once_with("/tmp/dummy")
        open_mock.assert_called_with("/tmp/dummy", 'r')
        self.assertEqual(return_list, ['user1', 'user2', 'user3'])

    @patch('pdfgen.certificate.os.path.isfile', return_value=False)
    def test_get_students_list_file_not_found(self, isf_mock):
        with self.assertRaises(CertPDFException) as e:
            cert = CertificatePDF(None, self.course_id, self.debug,
                                  self.noop, self.file_prefix, self.exclude)
            cert._get_students_list("/tmp/dummy")

        isf_mock.assert_called_once_with("/tmp/dummy")
        self.assertEqual(e.exception.message, '/tmp/dummy is not found.')
