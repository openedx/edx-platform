from django.test import TestCase
from django.conf import settings
from django.test.utils import override_settings
from mock import Mock, patch, ANY, create_autospec, mock_open
from pdfgen.views import (CertificateBase, CertificateHonor, CertStoreBase,
                          CertS3Store, create_cert_pdf, delete_cert_pdf, CertPDF,
                          PDFBaseNotFound, PDFBaseIsNotPDF, PDFBaseIsNotImage,
                          InvalidSettings)
from boto.s3.connection import S3Connection, Location
from boto.exception import BotoClientError, BotoServerError, S3ResponseError
from boto.s3.key import Key

import hashlib
import json
import StringIO


class CertificationBaseTestCase(TestCase):

    def setUp(self):
        self.cert = CertificateBase()

    def test_create(self):
        with self.assertRaises(NotImplementedError):
            self.cert.create()

    def test_get(self):
        with self.assertRaises(NotImplementedError):
            self.cert.get()

    def test_delete(self):
        with self.assertRaises(NotImplementedError):
            self.cert.delete()

    def test_verify(self):
        with self.assertRaises(NotImplementedError):
            self.cert.verify()


@override_settings(
    PDFGEN_CERT_AUTHOR="author", PDFGEN_CERT_TITLE="title",
    PDFGEN_BASE_IMG_DIR="/tmp", PDFGEN_BASE_PDF_DIR="/tmp")
class CertificateHonorTestCase(TestCase):

    def setUp(self):
        self.username = "username"
        self.display_name = "display_name"
        self.course_id = "org/num/run"
        self.course_name = "course_name"
        self.file_prefix = "prefix-"
        self.grade = 1

        md5 = hashlib.md5()
        self.key = md5.hexdigest()

        patcher0 = patch('pdfgen.views.logging')
        self.log_mock = patcher0.start()
        self.addCleanup(patcher0.stop)

        patcher1 = patch('pdfgen.views.CertS3Store')
        self.s3_mock = patcher1.start()
        self.addCleanup(patcher1.stop)

    def teerDown(self):
        pass

    @patch('pdfgen.views.json')
    @patch('pdfgen.views.os')
    @patch('pdfgen.views.CertPDF')
    @patch('pdfgen.views.mkstemp', return_value=[Mock(), "/tmp/test"])
    def test_create(self, mkst_mock, cert_mock, os_mock, json_mock):
        m = mock_open()
        with patch('pdfgen.views.open', m, create=True):
            cert = CertificateHonor(
                self.username, self.course_id, self.key, self.display_name,
                self.course_name, self.grade, self.file_prefix)
            cert.create()

        mkst_mock.assert_called_once_with(suffix="-certificate.pdf")
        cert_mock.assert_called_once_with(
            ANY, self.display_name, self.course_id,
            self.course_name, self.file_prefix)
        os_mock.close.assert_called_once_with(ANY)
        os_mock.remove.assert_called_once_with(ANY)
        self.s3_mock().save.assert_called_once_with(
            "_".join([self.username, self.key[:5]]), self.course_id, ANY)

    @patch('pdfgen.views.json')
    @patch('pdfgen.views.os')
    @patch('pdfgen.views.CertPDF')
    @patch('pdfgen.views.mkstemp', side_effect=OSError())
    def test_create_raise_oserror(self, mkst_mock, cert_mock, os_mock, json_mock):
        m = mock_open()
        with patch('pdfgen.views.open', m, create=True):
            cert = CertificateHonor(
                self.username, self.course_id, self.key, self.display_name,
                self.course_name, self.grade, self.file_prefix)
            cert.create()

        msg = "OS Error: ()"
        json_mock.dumps.assert_called_once_with({"error": msg})

    @patch('pdfgen.views.json')
    def test_create_course_name_is_none(self, json_mock):
        cert = CertificateHonor(
            self.username, self.course_id, self.key, self.display_name,
            None, self.grade, self.file_prefix)
        response = cert.create()
        msg = "course_name is required."
        json_mock.dumps.assert_called_once_with({"error": msg})

    @patch('pdfgen.views.json')
    def test_create_grade_is_none(self, json_mock):
        cert = CertificateHonor(
            self.username, self.course_id, self.key, self.display_name,
            self.course_name, None, self.file_prefix)
        response = cert.create()
        msg = "grade is required."
        json_mock.dumps.assert_called_once_with({"error": msg})

    def test_delete(self):
        cert = CertificateHonor(
            self.username, self.course_id, self.key, self.display_name,
            self.course_name, self.grade, self.file_prefix)
        cert.delete()

        self.s3_mock().delete.assert_called_once_with(
            "_".join([self.username, self.key[:5]]), self.course_id)


@override_settings(
    PDFGEN_CERT_AUTHOR="author", PDFGEN_CERT_TITLE="title",
    PDFGEN_BASE_IMG_DIR="/tmp", PDFGEN_BASE_PDF_DIR="/tmp")
class CertPDFTestCase(TestCase):

    def setUp(self):
        self.fp = StringIO.StringIO()
        self.username = "testusername"
        self.course_id = "org/num/run"
        self.course_name = "testcoursename"
        self.file_prefix = "prefix-"

        patcher0 = patch('pdfgen.views.logging')
        self.log_mock = patcher0.start()
        self.addCleanup(patcher0.stop)

    @patch('pdfgen.views.CertPDF.create_based_on_pdf')
    def test_create_pdf(self, pdf_mock):
        certpdf = CertPDF(
            self.fp, self.username, self.course_id,
            self.course_name, self.file_prefix)
        certpdf.create_pdf()
        pdf_mock.assert_called_once_with("/tmp/prefix-org-num-run.pdf")

    """
    @patch('pdfgen.views.CertPDF.create_based_on_image')
    @patch.multiple(settings, PDFGEN_BASE_PDF_DIR="not found",
        PDFGEN_BASE_IMG_DIR="/tmp")
    def test_create_based_on_image(self, img_mock):
        certpdf = CertPDF(self.fp, self.username, self.course_id,
            self.course_name, self.file_prefix)
        certpdf.create_pdf()
        img_mock.assert_called_once_with("/tmp/prefix-org-num-run.pdf")
    """

    @patch.multiple(
        settings, PDFGEN_BASE_PDF_DIR="not found",
        PDFGEN_BASE_IMG_DIR="not found")
    def test_create_pdf_directory_not_found(self):
        with self.assertRaises(PDFBaseNotFound):
            certpdf = CertPDF(
                self.fp, self.username, self.course_id,
                self.course_name, self.file_prefix)
            certpdf.create_pdf()

    @patch('__builtin__.file')
    @patch('pdfgen.views.PdfFileWriter')
    @patch('pdfgen.views.PdfFileReader')
    @patch('pdfgen.views.canvas')
    @patch('pdfgen.views.os.path.isfile', return_value=True)
    @patch.multiple(settings, PDFGEN_BASE_PDF_DIR="/tmp")
    def test_create_based_on_pdf(
            self, isfile_mock, cavs_mock, reader_mock, writer_mock, file_mock):

        certpdf = CertPDF(
            self.fp, self.username, self.course_id,
            self.course_name, self.file_prefix)
        certpdf.create_based_on_pdf(self.fp)

        isfile_mock.assert_called_once_with(self.fp)
        cavs_mock.Canvas.assert_called_once_with(
            ANY, bottomup=True, pageCompression=1, pagesize=ANY)
        reader_mock.assert_called_with(ANY)
        writer_mock.assert_called_once_with()

    @patch('pdfgen.views.os.path.isfile', return_value=False)
    def test_create_based_on_pdf_not_exists(self, isfile_mock):
        with self.assertRaises(PDFBaseNotFound):
            certpdf = CertPDF(
                self.fp, self.username, self.course_id,
                self.course_name, self.file_prefix)
            certpdf.create_based_on_pdf(self.fp)

    @patch('pdfgen.views.os.path.isfile', return_value=True)
    def test_create_based_on_pdf_not_file(self, isfile_mock):
        with self.assertRaises(PDFBaseIsNotPDF):
            certpdf = CertPDF(
                self.fp, self.username, self.course_id,
                self.course_name, self.file_prefix)
            certpdf.create_based_on_pdf(self.fp)

    @patch('pdfgen.views.ImageReader')
    @patch('pdfgen.views.canvas')
    @patch('pdfgen.views.os.path.isfile', return_value=True)
    def test_create_based_on_image(self, isfile_mock, cavs_mock, reader_mock):
        certpdf = CertPDF(
            self.fp, self.username, self.course_id,
            self.course_name, self.file_prefix)
        certpdf.create_based_on_image(self.fp)

        isfile_mock.assert_called_once_with(self.fp)
        cavs_mock.Canvas.assert_called_once_with(
            self.fp, bottomup=True, pageCompression=1, pagesize=ANY)
        reader_mock.assert_called_once_with(self.fp)

    @patch('pdfgen.views.os.path.isfile', return_value=False)
    def test_create_based_on_image_not_exists(self, isfile_mock):
        with self.assertRaises(PDFBaseNotFound):
            certpdf = CertPDF(
                self.fp, self.username, self.course_id,
                self.course_name, self.file_prefix)
            certpdf.create_based_on_image(self.fp)

    @patch('pdfgen.views.os.path.isfile', return_value=True)
    def test_create_based_on_image_isnot_image(self, isfile_mock):
        with self.assertRaises(PDFBaseIsNotImage):
            certpdf = CertPDF(
                self.fp, self.username, self.course_id,
                self.course_name, self.file_prefix)
            certpdf.create_based_on_image(self.fp)


class CertStoreBaseTestCase(TestCase):

    def setUp(self):
        self.store = CertStoreBase()

    def test_save(self):
        with self.assertRaises(NotImplementedError):
            self.store.save()

    def test_get(self):
        with self.assertRaises(NotImplementedError):
            self.store.get()

    def test_get_url(self):
        with self.assertRaises(NotImplementedError):
            self.store.get_url()

    def test_get_all(self):
        with self.assertRaises(NotImplementedError):
            self.store.get_all()

    def test_delete(self):
        with self.assertRaises(NotImplementedError):
            self.store.delete()


@override_settings(
    PDFGEN_BUCKET_NAME="bucket", PDFGEN_ACCESS_KEY_ID="akey",
    PDFGEN_SECRET_ACCESS_KEY="skey")
class CertS3StoreSuccesses(TestCase):

    def setUp(self):
        self.username = "testusername"
        self.course_id = "org/num/run"
        self.filepath = "/file/is/not/exists"
        self.bucket_name = settings.PDFGEN_BUCKET_NAME

        patcher0 = patch('pdfgen.views.logging')
        self.log = patcher0.start()
        self.addCleanup(patcher0.stop)

        self.s3class = create_autospec(S3Connection)
        config = {'return_value': self.s3class}
        patcher1 = patch('pdfgen.views.CertS3Store._connect', **config)
        self.s3conn = patcher1.start()
        self.addCleanup(patcher1.stop)

        self.keymethod = create_autospec(Key.set_contents_from_filename)
        patcher2 = patch('pdfgen.views.Key')
        self.s3key = patcher2.start()
        self.s3key().set_contents_from_filename.return_value = self.keymethod
        self.s3key().generate_url.return_value = "http://example.com/"
        self.addCleanup(patcher2.stop)

    def test_save(self):
        s3 = CertS3Store()
        response_json = s3.save(self.username, self.course_id, self.filepath)
        self.assertEqual(
            response_json, json.dumps({"download_url": "http://example.com/"}))
        self.s3key().set_contents_from_filename.assert_called_once_with(self.filepath)
        self.s3key().generate_url.assert_called_once_with(
            expires_in=0, query_auth=False, force_http=True)

    def test_delete(self):
        s3 = CertS3Store()
        response_json = s3.delete(self.username, self.course_id)
        self.assertEqual(response_json, json.dumps({"error": None}))
        self.s3key().delete.assert_called_once_with()

    def test_delete_file_not_found(self):
        s3 = CertS3Store()
        self.s3key().exists.return_value = False

        response_json = s3.delete(self.username, self.course_id)
        self.assertEqual(response_json, json.dumps(
            {"error": "file does not exists.(org/num/run/testusername.pdf)"}))
        self.assertEqual(self.s3key().delete.call_count, 0)


@override_settings(
    PDFGEN_BUCKET_NAME="bucket", PDFGEN_ACCESS_KEY_ID="akey",
    PDFGEN_SECRET_ACCESS_KEY="skey")
class CertS3StoreErrors(TestCase):
    def setUp(self):
        self.username = "testusername"
        self.course_id = "org/num/run"
        self.filepath = "/file/is/not/exists"
        self.bucket_name = settings.PDFGEN_BUCKET_NAME
        self.location = Location.APNortheast

        patcher0 = patch('pdfgen.views.logging')
        self.log = patcher0.start()
        self.addCleanup(patcher0.stop)

    @patch.multiple(settings, PDFGEN_BUCKET_NAME=None)
    def test_init_settings_None(self):
        with self.assertRaises(InvalidSettings):
            s3 = CertS3Store()

    @patch('pdfgen.views.Key.generate_url', return_value="http://example.com/")
    @patch('pdfgen.views.S3Connection.create_bucket')
    @patch('pdfgen.views.Key.set_contents_from_filename')
    def test_save_raise_S3ResponseError_with_404(self, moc1, moc2, moc3):
        s3 = CertS3Store()
        s3exception = S3ResponseError(status=404, reason="reason")
        with patch('pdfgen.views.S3Connection.get_bucket',
                   side_effect=s3exception) as bucket:

            response_json = s3.save(
                self.username, self.course_id, self.filepath)
            self.assertEqual(response_json, json.dumps(
                {"download_url": "http://example.com/"}))
            bucket.assert_called_once_with(self.bucket_name)
            moc1.assert_called_once_with(self.filepath)
            moc2.assert_called_once_with(
                self.bucket_name, location=self.location)
            moc3.assert_called_once_with(
                expires_in=0, query_auth=False, force_http=True)

    def test_save_raise_S3ResponseError(self):
        s3 = CertS3Store()
        s3exception = S3ResponseError(status="status", reason="reason")
        with patch('pdfgen.views.S3Connection.get_bucket',
                   side_effect=s3exception) as bucket:

            response_json = s3.save(
                self.username, self.course_id, self.filepath)
            self.assertEqual(response_json, json.dumps(
                {"error": "{}".format(s3exception)}))
            bucket.assert_called_once_with(self.bucket_name)


@override_settings(
    PDFGEN_BUCKET_NAME="bucket", PDFGEN_ACCESS_KEY_ID="akey",
    PDFGEN_SECRET_ACCESS_KEY="skey")
class MethodTestCase(TestCase):

    def setUp(self):
        self.display_name = "testusername"
        self.username = "testusername"
        self.course_id = "org/num/run"
        self.course_name = "testcoursename"
        self.grade = 1
        self.key = hashlib.md5()
        self.file_prefix = "prefix-"
        self.result = {"download_url": "http://exapmle.com"}
        self.result2 = {"error": None}

        patcher0 = patch('pdfgen.views.logging')
        self.log = patcher0.start()
        self.addCleanup(patcher0.stop)

    def test_create_cert_pdf(self):
        with patch('pdfgen.views.CertificateHonor.create', spec=True,
                   return_value=self.result) as moc1:
            contents = create_cert_pdf(self.username, self.course_id, self.key,
                                       self.display_name, self.course_name,
                                       self.grade, self.file_prefix)

        self.assertEqual(contents, self.result)
        moc1.assert_called_once_with()

    def test_create_cert_pdf_raise_BotoServerError(self):
        botoexception = BotoServerError(status=500, reason="reason")
        with patch('pdfgen.views.CertificateHonor.create', spec=True,
                   side_effect=botoexception) as moc1:

            contents = create_cert_pdf(self.username, self.course_id, self.key,
                                       self.display_name, self.course_name,
                                       self.grade, self.file_prefix)

        self.assertEqual(
            contents, json.dumps({"error": "BotoServerError: 500 reason\n"}))
        moc1.assert_called_once_with()

    def test_create_cert_pdf_raise_BotoClientError(self):
        botoexception = BotoClientError(reason="reason")
        with patch('pdfgen.views.CertificateHonor.create', spec=True,
                   side_effect=botoexception) as moc1:

            contents = create_cert_pdf(self.username, self.course_id, self.key,
                                       self.display_name, self.course_name,
                                       self.grade, self.file_prefix)

        self.assertEqual(
            contents, json.dumps({"error": "BotoClientError: reason"}))
        moc1.assert_called_once_with()

    def test_delete_pdf(self):
        with patch('pdfgen.views.CertificateHonor.delete', spec=True,
                   return_value=self.result2) as moc1:
            contents = delete_cert_pdf(self.username, self.course_id, self.key)

        self.assertEqual(contents, self.result2)
        moc1.assert_called_once_with()

    def test_delete_pdf_raise_BotoServerError(self):
        botoexception = BotoServerError(status=500, reason="reason")
        with patch('pdfgen.views.CertificateHonor.delete', spec=True,
                   side_effect=botoexception) as moc1:
            contents = delete_cert_pdf(self.username, self.course_id, self.key)

        self.assertEqual(
            contents, json.dumps({"error": "BotoServerError: 500 reason\n"}))
        moc1.assert_called_once_with()

    def test_delete_cert_pdf_raise_BotoClientError(self):
        botoexception = BotoClientError(reason="reason")
        with patch('pdfgen.views.CertificateHonor.delete', spec=True,
                   side_effect=botoexception) as moc1:
            contents = delete_cert_pdf(self.username, self.course_id, self.key)

        self.assertEqual(
            contents, json.dumps({"error": "BotoClientError: reason"}))
        moc1.assert_called_once_with()
