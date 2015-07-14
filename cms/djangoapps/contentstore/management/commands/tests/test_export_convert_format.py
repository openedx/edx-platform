"""
Test for export_convert_format.
"""
from unittest import TestCase
from django.core.management import call_command, CommandError
from django.conf import settings
from tempfile import mkdtemp
import shutil
from path import path
from contentstore.management.commands.export_convert_format import Command, extract_source
from xmodule.tests.helpers import directories_equal


class ConvertExportFormat(TestCase):
    """
    Tests converting between export formats.
    """
    def setUp(self):
        """ Common setup. """
        super(ConvertExportFormat, self).setUp()

        self.temp_dir = mkdtemp(dir=settings.DATA_DIR)
        self.addCleanup(shutil.rmtree, self.temp_dir)
        self.data_dir = path(__file__).realpath().parent / 'data'
        self.version0 = self.data_dir / "Version0_drafts.tar.gz"
        self.version1 = self.data_dir / "Version1_drafts.tar.gz"

        self.command = Command()

    def test_no_args(self):
        """ Test error condition of no arguments. """
        errstring = "export requires two arguments"
        with self.assertRaisesRegexp(CommandError, errstring):
            self.command.handle()

    def test_version1_archive(self):
        """
        Smoke test for creating a version 1 archive from a version 0.
        """
        call_command('export_convert_format', self.version0, self.temp_dir)
        output = path(self.temp_dir) / 'Version0_drafts_version_1.tar.gz'
        self.assertTrue(self._verify_archive_equality(output, self.version1))

    def test_version0_archive(self):
        """
        Smoke test for creating a version 0 archive from a version 1.
        """
        call_command('export_convert_format', self.version1, self.temp_dir)
        output = path(self.temp_dir) / 'Version1_drafts_version_0.tar.gz'
        self.assertTrue(self._verify_archive_equality(output, self.version0))

    def _verify_archive_equality(self, file1, file2):
        """
        Helper function for determining if 2 archives are equal.
        """
        temp_dir_1 = mkdtemp(dir=settings.DATA_DIR)
        temp_dir_2 = mkdtemp(dir=settings.DATA_DIR)
        try:
            extract_source(file1, temp_dir_1)
            extract_source(file2, temp_dir_2)
            return directories_equal(temp_dir_1, temp_dir_2)

        finally:
            shutil.rmtree(temp_dir_1)
            shutil.rmtree(temp_dir_2)
