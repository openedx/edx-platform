# -*- coding: utf-8 -*-
"""
Tests for file.py
"""
import ddt
from io import StringIO

from django.test import TestCase
from datetime import datetime
from django.utils.timezone import UTC
from mock import patch, Mock
from django.http import HttpRequest
from django.core.files.uploadedfile import SimpleUploadedFile
import util.file
from util.file import (
    course_and_time_based_filename_generator,
    course_filename_prefix_generator,
    store_uploaded_file,
    FileValidationException,
    UniversalNewlineIterator
)
from opaque_keys.edx.locations import CourseLocator, SlashSeparatedCourseKey
from django.core import exceptions
import os


@ddt.ddt
class FilenamePrefixGeneratorTestCase(TestCase):
    """
    Tests for course_filename_prefix_generator
    """
    @ddt.data(CourseLocator, SlashSeparatedCourseKey)
    def test_locators(self, course_key_class):
        self.assertEqual(
            course_filename_prefix_generator(course_key_class(org='foo', course='bar', run='baz')),
            u'foo_bar_baz'
        )

    @ddt.data(CourseLocator, SlashSeparatedCourseKey)
    def test_custom_separator(self, course_key_class):
        self.assertEqual(
            course_filename_prefix_generator(course_key_class(org='foo', course='bar', run='baz'), separator='-'),
            u'foo-bar-baz'
        )


@ddt.ddt
class FilenameGeneratorTestCase(TestCase):
    """
    Tests for course_and_time_based_filename_generator
    """
    NOW = datetime.strptime('1974-06-22T01:02:03', '%Y-%m-%dT%H:%M:%S').replace(tzinfo=UTC())

    def setUp(self):
        super(FilenameGeneratorTestCase, self).setUp()
        datetime_patcher = patch.object(
            util.file, 'datetime',
            Mock(wraps=datetime)
        )
        mocked_datetime = datetime_patcher.start()
        mocked_datetime.now.return_value = self.NOW
        self.addCleanup(datetime_patcher.stop)

    @ddt.data(CourseLocator, SlashSeparatedCourseKey)
    def test_filename_generator(self, course_key_class):
        """
        Tests that the generator creates names based on course_id, base name, and date.
        """
        self.assertEqual(
            u'foo_bar_baz_file_1974-06-22-010203',
            course_and_time_based_filename_generator(course_key_class(org='foo', course='bar', run='baz'), 'file')
        )

        self.assertEqual(
            u'foo_bar_baz_base_name_ø_1974-06-22-010203',
            course_and_time_based_filename_generator(
                course_key_class(org='foo', course='bar', run='baz'), ' base` name ø '
            )
        )


class StoreUploadedFileTestCase(TestCase):
    """
    Tests for store_uploaded_file.
    """

    def setUp(self):
        super(StoreUploadedFileTestCase, self).setUp()
        self.request = Mock(spec=HttpRequest)
        self.file_content = "test file content"
        self.stored_file_name = None
        self.file_storage = None
        self.default_max_size = 2000000

    def tearDown(self):
        super(StoreUploadedFileTestCase, self).tearDown()
        if self.file_storage and self.stored_file_name:
            self.file_storage.delete(self.stored_file_name)

    def verify_exception(self, expected_message, error):
        """
        Helper method to verify exception text.
        """
        self.assertEqual(expected_message, error.exception.message)

    def test_error_conditions(self):
        """
        Verifies that exceptions are thrown in the expected cases.
        """
        with self.assertRaises(ValueError) as error:
            self.request.FILES = {"uploaded_file": SimpleUploadedFile("tempfile.csv", self.file_content)}
            store_uploaded_file(self.request, "wrong_key", [".txt", ".csv"], "stored_file", self.default_max_size)
        self.verify_exception("No file uploaded with key 'wrong_key'.", error)

        with self.assertRaises(exceptions.PermissionDenied) as error:
            self.request.FILES = {"uploaded_file": SimpleUploadedFile("tempfile.csv", self.file_content)}
            store_uploaded_file(self.request, "uploaded_file", [], "stored_file", self.default_max_size)
        self.verify_exception("The file must end with one of the following extensions: ''.", error)

        with self.assertRaises(exceptions.PermissionDenied) as error:
            self.request.FILES = {"uploaded_file": SimpleUploadedFile("tempfile.csv", self.file_content)}
            store_uploaded_file(self.request, "uploaded_file", [".bar"], "stored_file", self.default_max_size)
        self.verify_exception("The file must end with the extension '.bar'.", error)

        with self.assertRaises(exceptions.PermissionDenied) as error:
            self.request.FILES = {"uploaded_file": SimpleUploadedFile("tempfile.csv", self.file_content)}
            store_uploaded_file(self.request, "uploaded_file", [".xxx", ".bar"], "stored_file", self.default_max_size)
        self.verify_exception("The file must end with one of the following extensions: '.xxx', '.bar'.", error)

        with self.assertRaises(exceptions.PermissionDenied) as error:
            self.request.FILES = {"uploaded_file": SimpleUploadedFile("tempfile.csv", self.file_content)}
            store_uploaded_file(self.request, "uploaded_file", [".csv"], "stored_file", 2)
        self.verify_exception("Maximum upload file size is 2 bytes.", error)

    def test_validator(self):
        """
        Verify that a validator function can throw an exception.
        """
        validator_data = {}

        def verify_file_presence(should_exist):
            """ Verify whether or not the stored file, passed to the validator, exists. """
            self.assertEqual(should_exist, validator_data["storage"].exists(validator_data["filename"]))

        def store_file_data(storage, filename):
            """ Stores file validator data for testing after validation is complete. """
            validator_data["storage"] = storage
            validator_data["filename"] = filename
            verify_file_presence(True)

        def exception_validator(storage, filename):
            """ Validation test function that throws an exception """
            self.assertEqual("error_file.csv", os.path.basename(filename))
            with storage.open(filename, 'rU') as f:
                self.assertEqual(self.file_content, f.read())
            store_file_data(storage, filename)
            raise FileValidationException("validation failed")

        def success_validator(storage, filename):
            """ Validation test function that is a no-op """
            self.assertTrue("success_file" in os.path.basename(filename))
            store_file_data(storage, filename)

        with self.assertRaises(FileValidationException) as error:
            self.request.FILES = {"uploaded_file": SimpleUploadedFile("tempfile.csv", self.file_content)}
            store_uploaded_file(
                self.request, "uploaded_file", [".csv"], "error_file",
                self.default_max_size, validator=exception_validator
            )
        self.verify_exception("validation failed", error)
        # Verify the file was deleted.
        verify_file_presence(False)

        self.request.FILES = {"uploaded_file": SimpleUploadedFile("tempfile.csv", self.file_content)}
        store_uploaded_file(
            self.request, "uploaded_file", [".csv"], "success_file", self.default_max_size, validator=success_validator
        )
        # Verify the file still exists
        verify_file_presence(True)

    def test_file_upload_lower_case_extension(self):
        """
        Tests uploading a file with lower case extension. Verifies that the stored file contents are correct.
        """
        self.request.FILES = {"uploaded_file": SimpleUploadedFile("tempfile.csv", self.file_content)}
        file_storage, stored_file_name = store_uploaded_file(
            self.request, "uploaded_file", [".csv"], "stored_file", self.default_max_size
        )
        self._verify_successful_upload(file_storage, stored_file_name, self.file_content)

    def test_file_upload_upper_case_extension(self):
        """
        Tests uploading a file with upper case extension. Verifies that the stored file contents are correct.
        """
        file_content = "uppercase"
        self.request.FILES = {"uploaded_file": SimpleUploadedFile("tempfile.CSV", file_content)}
        file_storage, stored_file_name = store_uploaded_file(
            self.request, "uploaded_file", [".gif", ".csv"], "second_stored_file", self.default_max_size
        )
        self._verify_successful_upload(file_storage, stored_file_name, file_content)

    def test_unique_filenames(self):
        """
        Test that the file storage method will create a unique filename if the file already exists.
        """
        requested_file_name = "nonunique_store"
        file_content = "copy"

        self.request.FILES = {"nonunique_file": SimpleUploadedFile("nonunique.txt", file_content)}
        _, first_stored_file_name = store_uploaded_file(
            self.request, "nonunique_file", [".txt"], requested_file_name, self.default_max_size
        )

        self.request.FILES = {"nonunique_file": SimpleUploadedFile("nonunique.txt", file_content)}
        file_storage, second_stored_file_name = store_uploaded_file(
            self.request, "nonunique_file", [".txt"], requested_file_name, self.default_max_size
        )
        self.assertNotEqual(first_stored_file_name, second_stored_file_name)
        self.assertTrue(requested_file_name in second_stored_file_name)
        self._verify_successful_upload(file_storage, second_stored_file_name, file_content)

    def _verify_successful_upload(self, storage, file_name, expected_content):
        """ Helper method that checks that the stored version of the uploaded file has the correct content """
        self.assertTrue(storage.exists(file_name))
        with storage.open(file_name, 'r') as f:
            self.assertEqual(expected_content, f.read())


@ddt.ddt
class TestUniversalNewlineIterator(TestCase):
    """
    Tests for the UniversalNewlineIterator class.
    """
    @ddt.data(1, 2, 999)
    def test_line_feeds(self, buffer_size):
        self.assertEqual(
            [thing for thing in UniversalNewlineIterator(StringIO(u'foo\nbar\n'), buffer_size=buffer_size)],
            ['foo\n', 'bar\n']
        )

    @ddt.data(1, 2, 999)
    def test_carriage_returns(self, buffer_size):
        self.assertEqual(
            [thing for thing in UniversalNewlineIterator(StringIO(u'foo\rbar\r'), buffer_size=buffer_size)],
            ['foo\n', 'bar\n']
        )

    @ddt.data(1, 2, 999)
    def test_carriage_returns_and_line_feeds(self, buffer_size):
        self.assertEqual(
            [thing for thing in UniversalNewlineIterator(StringIO(u'foo\r\nbar\r\n'), buffer_size=buffer_size)],
            ['foo\n', 'bar\n']
        )

    @ddt.data(1, 2, 999)
    def test_no_trailing_newline(self, buffer_size):
        self.assertEqual(
            [thing for thing in UniversalNewlineIterator(StringIO(u'foo\nbar'), buffer_size=buffer_size)],
            ['foo\n', 'bar']
        )

    @ddt.data(1, 2, 999)
    def test_only_one_line(self, buffer_size):
        self.assertEqual(
            [thing for thing in UniversalNewlineIterator(StringIO(u'foo\n'), buffer_size=buffer_size)],
            ['foo\n']
        )

    @ddt.data(1, 2, 999)
    def test_only_one_line_no_trailing_newline(self, buffer_size):
        self.assertEqual(
            [thing for thing in UniversalNewlineIterator(StringIO(u'foo'), buffer_size=buffer_size)],
            ['foo']
        )

    @ddt.data(1, 2, 999)
    def test_empty_file(self, buffer_size):
        self.assertEqual(
            [thing for thing in UniversalNewlineIterator(StringIO(u''), buffer_size=buffer_size)],
            []
        )

    @ddt.data(1, 2, 999)
    def test_unicode_data(self, buffer_size):
        self.assertEqual(
            [thing for thing in UniversalNewlineIterator(StringIO(u'héllø wo®ld'), buffer_size=buffer_size)],
            [u'héllø wo®ld']
        )
