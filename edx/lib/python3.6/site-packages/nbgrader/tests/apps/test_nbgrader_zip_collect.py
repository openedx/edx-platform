import os
import pytest
import zipfile

from textwrap import dedent
from os.path import join

from .base import BaseTestApp
from .. import run_nbgrader
from ...utils import rmtree


@pytest.fixture
def archive_dir(request, course_dir):
    path = os.path.join(course_dir, "downloaded", "ps1", "archive")
    os.makedirs(path)

    def fin():
        rmtree(path)
    request.addfinalizer(fin)

    return path


def _count_zip_files(path):
    with zipfile.ZipFile(path, 'r') as zip_file:
        return len(zip_file.namelist())


class TestNbGraderZipCollect(BaseTestApp):

    def _make_notebook(self, dest, *args):
        notebook = '{}_{}_attempt_{}_{}.ipynb'.format(*args)
        self._empty_notebook(join(dest, notebook))

    def test_help(self):
        """Does the help display without error?"""
        run_nbgrader(["zip_collect", "--help-all"])

    def test_args(self):
        # Should fail with no assignment id
        run_nbgrader(["zip_collect"], retcode=1)

    def test_no_archive_dir(self, course_dir):
        # Should not fail with no archive_directory
        run_nbgrader(["zip_collect", "ps1"])

    def test_empty_folders(self, course_dir, archive_dir):
        os.makedirs(join(archive_dir, "..", "extracted"))
        run_nbgrader(["zip_collect", "ps1"])
        assert not os.path.isdir(join(course_dir, "submitted"))

    def test_extract_single_notebook(self, course_dir, archive_dir):
        extracted_dir = join(archive_dir, "..", "extracted")
        self._make_notebook(archive_dir,
            'ps1', 'hacker', '2016-01-30-15-30-10', 'problem1')

        run_nbgrader(["zip_collect", "ps1"])
        assert os.path.isdir(extracted_dir)
        assert len(os.listdir(extracted_dir)) == 1

        # Run again should fail
        run_nbgrader(["zip_collect", "ps1"], retcode=1)
        assert os.path.isdir(extracted_dir)
        assert len(os.listdir(extracted_dir)) == 1

        # Run again with --force flag should pass
        run_nbgrader(["zip_collect", "--force", "ps1"])
        assert os.path.isdir(extracted_dir)
        assert len(os.listdir(extracted_dir)) == 1

    def test_extract_sub_dir_single_notebook(self, course_dir, archive_dir):
        extracted_dir = join(archive_dir, "..", "extracted")
        self._make_notebook(join(archive_dir, 'hacker'),
            'ps1', 'hacker', '2016-01-30-15-30-10', 'problem1')

        run_nbgrader(["zip_collect", "ps1"])
        assert os.path.isdir(extracted_dir)
        assert os.path.isdir(join(extracted_dir, "hacker"))
        assert len(os.listdir(join(extracted_dir, "hacker"))) == 1

    def test_extract_archive(self, course_dir, archive_dir):
        extracted_dir = join(archive_dir, "..", "extracted", "notebooks")
        archive = join(archive_dir, "notebooks.zip")
        self._copy_file(join("files", "notebooks.zip"), archive)

        run_nbgrader(["zip_collect", "ps1"])
        assert os.path.isdir(extracted_dir)
        assert len(os.listdir(extracted_dir)) == _count_zip_files(archive)

    def test_extract_archive_copies(self, course_dir, archive_dir):
        extracted_dir = join(archive_dir, "..", "extracted")
        archive1 = join(archive_dir, "notebooks.zip")
        archive2 = join(archive_dir, "notebooks_copy.zip")

        self._copy_file(join("files", "notebooks.zip"), archive1)
        self._copy_file(join("files", "notebooks.zip"), archive2)

        cnt = 0
        run_nbgrader(["zip_collect", "ps1"])
        nfiles = _count_zip_files(archive1) + _count_zip_files(archive2)
        assert os.path.isdir(extracted_dir)
        for _, _, files in os.walk(extracted_dir):
            cnt += len(files)
        assert cnt == nfiles

    def test_collect_no_regexp(self, course_dir, archive_dir):
        extracted_dir = join(archive_dir, "..", "extracted")
        submitted_dir = join(course_dir, "submitted")
        self._make_notebook(archive_dir,
            'ps1', 'hacker', '2016-01-30-15-30-10', 'problem1')

        run_nbgrader(["zip_collect", "--force", "ps1"])
        assert os.path.isdir(extracted_dir)
        assert len(os.listdir(extracted_dir)) == 1
        assert not os.path.isdir(submitted_dir)

    def test_collect_bad_regexp(self, course_dir, archive_dir):
        extracted_dir = join(archive_dir, "..", "extracted")
        submitted_dir = join(course_dir, "submitted")
        self._make_notebook(archive_dir,
            'ps1', 'hacker', '2016-01-30-15-30-10', 'problem1')

        with open("nbgrader_config.py", "a") as fh:
            fh.write(dedent(
                """
                c.FileNameCollectorPlugin.named_regexp = (
                    r"Peter piper picked ..."
                )
                """
            ))

        run_nbgrader(["zip_collect", "--force", "ps1"])
        assert os.path.isdir(extracted_dir)
        assert len(os.listdir(extracted_dir)) == 1
        assert not os.path.isdir(submitted_dir)

    def test_collect_regexp_missing_student_id(self, course_dir, archive_dir):
        extracted_dir = join(archive_dir, "..", "extracted")
        submitted_dir = join(course_dir, "submitted")
        self._make_notebook(archive_dir,
            'ps1', 'hacker', '2016-01-30-15-30-10', 'problem1')

        with open("nbgrader_config.py", "a") as fh:
            fh.write(dedent(
                """
                c.FileNameCollectorPlugin.named_regexp = (
                    r".+_(?P<foo>\w+)_attempt_(?P<timestamp>[0-9\-]+)_(?P<file_id>\w+)"
                )
                """
            ))

        run_nbgrader(["zip_collect", "ps1"], retcode=1)
        assert os.path.isdir(extracted_dir)
        assert len(os.listdir(extracted_dir)) == 1
        assert not os.path.isdir(submitted_dir)

    def test_collect_regexp_bad_student_id_type(self, course_dir, archive_dir):
        extracted_dir = join(archive_dir, "..", "extracted")
        submitted_dir = join(course_dir, "submitted")
        self._make_notebook(archive_dir,
            'ps1', 'hacker', '2016-01-30-15-30-10', 'problem1')

        with open('plugin_one.py', 'w') as fh:
            fh.write(dedent(
                """
                from nbgrader.plugins import FileNameCollectorPlugin

                class CustomPlugin(FileNameCollectorPlugin):
                    def collect(self, submitted_file):
                        info = super(CustomPlugin, self).collect(submitted_file)
                        if info is not None:
                            info['student_id'] = 111
                        return info
                """
            ))

        with open("nbgrader_config.py", "a") as fh:
            fh.write(dedent(
                """
                c.ZipCollectApp.collector_plugin = 'plugin_one.CustomPlugin'
                c.FileNameCollectorPlugin.named_regexp = (
                    r".+_(?P<student_id>\w+)_attempt_(?P<timestamp>[0-9\-]+)_(?P<file_id>\w+)"
                )
                """
            ))

        run_nbgrader(["zip_collect", "ps1"], retcode=1)
        assert os.path.isdir(extracted_dir)
        assert len(os.listdir(extracted_dir)) == 1
        assert not os.path.isdir(submitted_dir)

    def test_collect_single_notebook(self, course_dir, archive_dir):
        extracted_dir = join(archive_dir, "..", "extracted")
        submitted_dir = join(course_dir, "submitted")
        self._make_notebook(archive_dir,
            'ps1', 'hacker', '2016-01-30-15-30-10', 'problem1')

        with open("nbgrader_config.py", "a") as fh:
            fh.write(dedent(
                """
                c.FileNameCollectorPlugin.named_regexp = (
                    r".+_(?P<student_id>\w+)_attempt_(?P<timestamp>[0-9\-]+)_(?P<file_id>\w+)"
                )
                """
            ))

        run_nbgrader(["zip_collect", "ps1"])
        assert os.path.isdir(extracted_dir)
        assert len(os.listdir(extracted_dir)) == 1

        assert os.path.isdir(submitted_dir)
        assert os.path.isfile(join(submitted_dir, "hacker", "ps1", 'problem1.ipynb'))
        assert os.path.isfile(join(submitted_dir, "hacker", "ps1", 'timestamp.txt'))
        assert len(os.listdir(join(submitted_dir, "hacker", "ps1"))) == 2

    def test_collect_single_notebook_attempts(self, course_dir, archive_dir):
        extracted_dir = join(archive_dir, "..", "extracted")
        submitted_dir = join(course_dir, "submitted")

        self._make_notebook(archive_dir,
            'ps1', 'hacker', '2016-01-30-15-30-10', 'problem1')
        self._make_notebook(archive_dir,
            'ps1', 'hacker', '2016-01-30-15-40-10', 'problem1')
        self._make_notebook(archive_dir,
            'ps1', 'hacker', '2016-01-30-15-50-10', 'problem1')

        with open('plugin_two.py', 'w') as fh:
            fh.write(dedent(
                """
                from nbgrader.plugins import FileNameCollectorPlugin

                class CustomPlugin(FileNameCollectorPlugin):
                    def collect(self, submitted_file):
                        info = super(CustomPlugin, self).collect(submitted_file)
                        if info is not None:
                            info['timestamp'] = '{}-{}-{} {}:{}:{}'.format(
                                *tuple(info['timestamp'].split('-'))
                            )
                        return info
                """
            ))

        with open("nbgrader_config.py", "a") as fh:
            fh.write(dedent(
                """
                c.ZipCollectApp.collector_plugin = 'plugin_two.CustomPlugin'
                c.FileNameCollectorPlugin.named_regexp = (
                    r".+_(?P<student_id>\w+)_attempt_(?P<timestamp>[0-9\-]+)_(?P<file_id>\w+)"
                )
                """
            ))

        run_nbgrader(["zip_collect", "ps1"])
        assert os.path.isdir(extracted_dir)
        assert len(os.listdir(extracted_dir)) == 3

        assert os.path.isdir(submitted_dir)
        assert os.path.isfile(join(submitted_dir, "hacker", "ps1", 'problem1.ipynb'))
        assert os.path.isfile(join(submitted_dir, "hacker", "ps1", 'timestamp.txt'))
        assert len(os.listdir(join(submitted_dir, "hacker", "ps1"))) == 2

        with open(join(submitted_dir, "hacker", "ps1", 'timestamp.txt')) as ts:
            timestamp = ts.read()
        assert timestamp == '2016-01-30 15:50:10'

    def test_collect_multiple_notebooks(self, course_dir, archive_dir):
        extracted_dir = join(archive_dir, "..", "extracted")
        submitted_dir = join(course_dir, "submitted")
        self._make_notebook(archive_dir,
            'ps1', 'hacker', '2016-01-30-15-30-10', 'problem1')
        self._make_notebook(archive_dir,
            'ps1', 'hacker', '2016-01-30-15-30-10', 'problem2')
        self._make_notebook(archive_dir,
            'ps1', 'hacker', '2016-02-10-15-30-10', 'problem1')
        self._make_notebook(archive_dir,
            'ps1', 'hacker', '2016-02-10-15-30-10', 'problem2')

        with open("nbgrader_config.py", "a") as fh:
            fh.write(dedent(
                """
                c.FileNameCollectorPlugin.named_regexp = (
                    r".+_(?P<student_id>\w+)_attempt_(?P<timestamp>[0-9\-]+)_(?P<file_id>\w+)"
                )
                """
            ))

        output = run_nbgrader(["zip_collect", "ps1"])
        assert os.path.isdir(extracted_dir)
        assert len(os.listdir(extracted_dir)) == 4

        assert os.path.isdir(submitted_dir)
        assert os.path.isfile(join(submitted_dir, "hacker", "ps1", 'problem1.ipynb'))
        assert os.path.isfile(join(submitted_dir, "hacker", "ps1", 'problem2.ipynb'))
        assert os.path.isfile(join(submitted_dir, "hacker", "ps1", 'timestamp.txt'))
        assert len(os.listdir(join(submitted_dir, "hacker", "ps1"))) == 3

        # Issue #724 - check multiple attempts are collected properly
        assert "Skipped submission file" not in output
        msg = "Replacing previously collected submission file"
        assert sum([msg in line for line in output.splitlines()]) == 2

    def test_collect_sub_dir_single_notebook(self, course_dir, archive_dir):
        extracted_dir = join(archive_dir, "..", "extracted")
        submitted_dir = join(course_dir, "submitted")

        self._make_notebook(archive_dir,
            'ps1', 'hacker', '2016-01-30-15-30-10', 'problem1')
        self._make_notebook(join(archive_dir, 'bitdiddle'),
            'ps1', 'bitdiddle', '2016-01-30-15-30-10', 'problem1')

        with open("nbgrader_config.py", "a") as fh:
            fh.write(dedent(
                """
                c.FileNameCollectorPlugin.named_regexp = (
                    r".+_(?P<student_id>\w+)_attempt_(?P<timestamp>[0-9\-]+)_(?P<file_id>\w+)"
                )
                """
            ))

        run_nbgrader(["zip_collect", "ps1"])
        assert os.path.isdir(extracted_dir)
        assert os.path.isdir(submitted_dir)
        assert len(os.listdir(submitted_dir)) == 2

        assert os.path.isfile(join(submitted_dir, "hacker", "ps1", 'problem1.ipynb'))
        assert os.path.isfile(join(submitted_dir, "hacker", "ps1", 'timestamp.txt'))
        assert len(os.listdir(join(submitted_dir, "hacker", "ps1"))) == 2

        assert os.path.isfile(join(submitted_dir, "bitdiddle", "ps1", 'problem1.ipynb'))
        assert os.path.isfile(join(submitted_dir, "bitdiddle", "ps1", 'timestamp.txt'))
        assert len(os.listdir(join(submitted_dir, "bitdiddle", "ps1"))) == 2

    def test_collect_invalid_notebook(self, course_dir, archive_dir):
        extracted_dir = join(archive_dir, "..", "extracted")
        submitted_dir = join(course_dir, "submitted")
        self._empty_notebook(join(course_dir, 'source', 'ps1', 'problem1.ipynb'))

        with open("nbgrader_config.py", "a") as fh:
            fh.write(dedent(
                """
                c.CourseDirectory.db_assignments = [dict(name="ps1")]
                c.FileNameCollectorPlugin.named_regexp = (
                    r".+_(?P<student_id>\w+)_attempt_(?P<timestamp>[0-9\-]+)_(?P<file_id>\w+)"
                )
                """
            ))

        run_nbgrader(["assign", "ps1"])
        self._make_notebook(archive_dir,
            'ps1', 'hacker', '2016-01-30-15-30-10', 'myproblem1')

        # Should get collected without --strict flag
        run_nbgrader(["zip_collect", "ps1"])
        assert os.path.isdir(extracted_dir)
        assert len(os.listdir(extracted_dir)) == 1

        assert os.path.isdir(submitted_dir)
        assert os.path.isfile(join(submitted_dir, "hacker", "ps1", 'myproblem1.ipynb'))
        assert os.path.isfile(join(submitted_dir, "hacker", "ps1", 'timestamp.txt'))
        assert len(os.listdir(join(submitted_dir, "hacker", "ps1"))) == 2

        # Re-run with --strict flag
        self._make_notebook(archive_dir,
            'ps1', 'hacker', '2016-01-30-15-30-10', 'problem1')

        run_nbgrader(["zip_collect", "--force", "--strict", "ps1"])
        assert os.path.isdir(extracted_dir)
        assert len(os.listdir(extracted_dir)) == 2

        assert os.path.isdir(submitted_dir)
        assert os.path.isfile(join(submitted_dir, "hacker", "ps1", 'problem1.ipynb'))
        assert os.path.isfile(join(submitted_dir, "hacker", "ps1", 'timestamp.txt'))
        assert len(os.listdir(join(submitted_dir, "hacker", "ps1"))) == 2

    def test_collect_timestamp_none(self, course_dir, archive_dir):
        extracted_dir = join(archive_dir, "..", "extracted")
        submitted_dir = join(course_dir, "submitted")
        self._make_notebook(archive_dir,
            'ps1', 'hacker', '2016-01-30-15-30-10', 'problem1')

        with open("nbgrader_config.py", "a") as fh:
            fh.write(dedent(
                """
                c.FileNameCollectorPlugin.named_regexp = (
                    r".+_(?P<student_id>\w+)_attempt_(?P<blarg>[0-9\-]+)_(?P<file_id>\w+)"
                )
                """
            ))

        run_nbgrader(["zip_collect", "ps1"])
        assert os.path.isdir(extracted_dir)
        assert len(os.listdir(extracted_dir)) == 1

        assert os.path.isdir(submitted_dir)
        assert os.path.isfile(join(submitted_dir, "hacker", "ps1", 'problem1.ipynb'))
        assert not os.path.isfile(join(submitted_dir, "hacker", "ps1", 'timestamp.txt'))
        assert len(os.listdir(join(submitted_dir, "hacker", "ps1"))) == 1

    def test_collect_timestamp_empty_str(self, course_dir, archive_dir):
        extracted_dir = join(archive_dir, "..", "extracted")
        submitted_dir = join(course_dir, "submitted")
        self._make_notebook(archive_dir,
            'ps1', 'hacker', '2016-01-30-15-30-10', 'problem1')

        with open('plugin_three.py', 'w') as fh:
            fh.write(dedent(
                """
                from nbgrader.plugins import FileNameCollectorPlugin

                class CustomPlugin(FileNameCollectorPlugin):
                    def collect(self, submitted_file):
                        info = super(CustomPlugin, self).collect(submitted_file)
                        if info is not None:
                            info['timestamp'] = ""
                        return info
                """
            ))

        with open("nbgrader_config.py", "a") as fh:
            fh.write(dedent(
                """
                c.ZipCollectApp.collector_plugin = 'plugin_three.CustomPlugin'
                c.FileNameCollectorPlugin.named_regexp = (
                    r".+_(?P<student_id>\w+)_attempt_(?P<timestamp>[0-9\-]+)_(?P<file_id>\w+)"
                )
                """
            ))

        run_nbgrader(["zip_collect", "ps1"])
        assert os.path.isdir(extracted_dir)
        assert len(os.listdir(extracted_dir)) == 1

        assert os.path.isdir(submitted_dir)
        assert os.path.isfile(join(submitted_dir, "hacker", "ps1", 'problem1.ipynb'))
        assert not os.path.isfile(join(submitted_dir, "hacker", "ps1", 'timestamp.txt'))
        assert len(os.listdir(join(submitted_dir, "hacker", "ps1"))) == 1

    def test_collect_timestamp_bad_str(self, course_dir, archive_dir):
        extracted_dir = join(archive_dir, "..", "extracted")
        submitted_dir = join(course_dir, "submitted")
        self._make_notebook(archive_dir,
            'ps1', 'hacker', '2016-01-30-15-30-10', 'problem1')

        with open('plugin_four.py', 'w') as fh:
            fh.write(dedent(
                """
                from nbgrader.plugins import FileNameCollectorPlugin

                class CustomPlugin(FileNameCollectorPlugin):
                    def collect(self, submitted_file):
                        info = super(CustomPlugin, self).collect(submitted_file)
                        if info is not None:
                            info['timestamp'] = "I'm still trying to be a timestamp str"
                        return info
                """
            ))

        with open("nbgrader_config.py", "a") as fh:
            fh.write(dedent(
                """
                c.ZipCollectApp.collector_plugin = 'plugin_four.CustomPlugin'
                c.FileNameCollectorPlugin.named_regexp = (
                    r".+_(?P<student_id>\w+)_attempt_(?P<timestamp>[0-9\-]+)_(?P<file_id>\w+)"
                )
                """
            ))

        run_nbgrader(["zip_collect", "ps1"], retcode=1)
        assert os.path.isdir(extracted_dir)
        assert len(os.listdir(extracted_dir)) == 1
        assert not os.path.isdir(submitted_dir)

    def test_collect_timestamp_skip_older(self, course_dir, archive_dir):
        extracted_dir = join(archive_dir, "..", "extracted")
        submitted_dir = join(course_dir, "submitted")

        # submissions are sorted so a before b
        os.makedirs(join(archive_dir, 'ps1_hacker_a_2017-01-30-15-30-10'))
        with open(join(archive_dir, 'ps1_hacker_a_2017-01-30-15-30-10', 'problem1.ipynb'), 'w') as fh:
            fh.write('')
        os.makedirs(join(archive_dir, 'ps1_hacker_b_2016-01-30-15-30-10'))
        with open(join(archive_dir, 'ps1_hacker_b_2016-01-30-15-30-10', 'problem1.ipynb'), 'w') as fh:
            fh.write('')

        with open('plugin_five.py', 'w') as fh:
            fh.write(dedent(
                """
                from nbgrader.plugins import FileNameCollectorPlugin

                class CustomPlugin(FileNameCollectorPlugin):
                    def collect(self, submitted_file):
                        info = super(CustomPlugin, self).collect(submitted_file)
                        if info is not None:
                            info['timestamp'] = '{}-{}-{} {}:{}:{}'.format(
                                *tuple(info['timestamp'].split('-'))
                            )
                        return info
                """
            ))

        with open("nbgrader_config.py", "a") as fh:
            fh.write(dedent(
                """
                c.ZipCollectApp.collector_plugin = 'plugin_five.CustomPlugin'
                c.FileNameCollectorPlugin.valid_ext = ['.ipynb', '.txt']
                c.FileNameCollectorPlugin.named_regexp = (
                    r".+ps1_(?P<student_id>\w+)_[a|b]_(?P<timestamp>[0-9\-]+)\W+(?P<file_id>.+)"
                )
                """
            ))

        run_nbgrader(["zip_collect", "ps1"])
        assert os.path.isdir(extracted_dir)
        assert os.path.isdir(submitted_dir)
        assert len(os.listdir(submitted_dir)) == 1

        assert os.path.isfile(join(submitted_dir, "hacker", "ps1", 'problem1.ipynb'))
        assert os.path.isfile(join(submitted_dir, "hacker", "ps1", 'timestamp.txt'))
        assert len(os.listdir(join(submitted_dir, "hacker", "ps1"))) == 2

        with open(join(submitted_dir, "hacker", "ps1", 'timestamp.txt'), 'r') as fh:
            ts = fh.read()
        assert ts == '2017-01-30 15:30:10'

    def test_collect_timestamp_replace_newer(self, course_dir, archive_dir):
        extracted_dir = join(archive_dir, "..", "extracted")
        submitted_dir = join(course_dir, "submitted")

        # submissions are sorted so a before b
        os.makedirs(join(archive_dir, 'ps1_hacker_a_2016-01-30-15-30-10'))
        with open(join(archive_dir, 'ps1_hacker_a_2016-01-30-15-30-10', 'problem1.ipynb'), 'w') as fh:
            fh.write('')
        os.makedirs(join(archive_dir, 'ps1_hacker_b_2017-01-30-15-30-10'))
        with open(join(archive_dir, 'ps1_hacker_b_2017-01-30-15-30-10', 'problem1.ipynb'), 'w') as fh:
            fh.write('')

        with open('plugin_six.py', 'w') as fh:
            fh.write(dedent(
                """
                from nbgrader.plugins import FileNameCollectorPlugin

                class CustomPlugin(FileNameCollectorPlugin):
                    def collect(self, submitted_file):
                        info = super(CustomPlugin, self).collect(submitted_file)
                        if info is not None:
                            info['timestamp'] = '{}-{}-{} {}:{}:{}'.format(
                                *tuple(info['timestamp'].split('-'))
                            )
                        return info
                """
            ))

        with open("nbgrader_config.py", "a") as fh:
            fh.write(dedent(
                """
                c.ZipCollectApp.collector_plugin = 'plugin_six.CustomPlugin'
                c.FileNameCollectorPlugin.valid_ext = ['.ipynb', '.txt']
                c.FileNameCollectorPlugin.named_regexp = (
                    r".+ps1_(?P<student_id>\w+)_[a|b]_(?P<timestamp>[0-9\-]+)\W+(?P<file_id>.+)"
                )
                """
            ))

        run_nbgrader(["zip_collect", "ps1"])
        assert os.path.isdir(extracted_dir)
        assert os.path.isdir(submitted_dir)
        assert len(os.listdir(submitted_dir)) == 1

        assert os.path.isfile(join(submitted_dir, "hacker", "ps1", 'problem1.ipynb'))
        assert os.path.isfile(join(submitted_dir, "hacker", "ps1", 'timestamp.txt'))
        assert len(os.listdir(join(submitted_dir, "hacker", "ps1"))) == 2

        with open(join(submitted_dir, "hacker", "ps1", 'timestamp.txt'), 'r') as fh:
            ts = fh.read()
        assert ts == '2017-01-30 15:30:10'

    def test_collect_timestamp_file(self, course_dir, archive_dir):
        extracted_dir = join(archive_dir, "..", "extracted")
        submitted_dir = join(course_dir, "submitted")

        os.makedirs(join(archive_dir, 'ps1_hacker'))
        with open(join(archive_dir, 'ps1_hacker', 'problem1.ipynb'), 'w') as fh:
            fh.write('')
        with open(join(archive_dir, 'ps1_hacker', 'timestamp.txt'), 'w') as fh:
            fh.write('foo')

        with open("nbgrader_config.py", "a") as fh:
            fh.write(dedent(
                """
                c.FileNameCollectorPlugin.valid_ext = ['.ipynb', '.txt']
                c.FileNameCollectorPlugin.named_regexp = (
                    r".+ps1_(?P<student_id>\w+)\W+(?P<file_id>.+)"
                )
                """
            ))

        run_nbgrader(["zip_collect", "ps1"])
        assert os.path.isdir(extracted_dir)
        assert os.path.isdir(submitted_dir)
        assert len(os.listdir(submitted_dir)) == 1

        assert os.path.isfile(join(submitted_dir, "hacker", "ps1", 'problem1.ipynb'))
        assert os.path.isfile(join(submitted_dir, "hacker", "ps1", 'timestamp.txt'))
        assert len(os.listdir(join(submitted_dir, "hacker", "ps1"))) == 2

        with open(join(submitted_dir, "hacker", "ps1", 'timestamp.txt'), 'r') as fh:
            ts = fh.read()
        assert ts == 'foo'

    def test_collect_preserve_sub_dir(self, course_dir, archive_dir):
        extracted_dir = join(archive_dir, "..", "extracted")
        submitted_dir = join(course_dir, "submitted")

        os.makedirs(join(archive_dir, 'ps1_hacker', 'files'))
        with open(join(archive_dir, 'ps1_hacker', 'files', 'problem1.ipynb'), 'w') as fh:
            fh.write('')
        with open(join(archive_dir, 'ps1_hacker', 'timestamp.txt'), 'w') as fh:
            fh.write('foo')

        with open("nbgrader_config.py", "a") as fh:
            fh.write(dedent(
                """
                c.FileNameCollectorPlugin.valid_ext = ['.ipynb', '.txt']
                c.FileNameCollectorPlugin.named_regexp = (
                    r".+ps1_(?P<student_id>\w+)\W+(?P<file_id>.+)"
                )
                """
            ))

        run_nbgrader(["zip_collect", "ps1"])
        assert os.path.isdir(extracted_dir)
        assert os.path.isdir(submitted_dir)
        assert len(os.listdir(submitted_dir)) == 1

        assert os.path.isfile(join(submitted_dir, "hacker", "ps1", 'files', 'problem1.ipynb'))
        assert os.path.isfile(join(submitted_dir, "hacker", "ps1", 'timestamp.txt'))
        assert len(os.listdir(join(submitted_dir, "hacker", "ps1"))) == 2

        with open(join(submitted_dir, "hacker", "ps1", 'timestamp.txt'), 'r') as fh:
            ts = fh.read()
        assert ts == 'foo'

    def test_collect_duplicate_fail(self, course_dir, archive_dir):
        extracted_dir = join(archive_dir, "..", "extracted")
        submitted_dir = join(course_dir, "submitted")

        os.makedirs(join(archive_dir, 'ps1_hacker_01', 'files'))
        with open(join(archive_dir, 'ps1_hacker_01', 'files', 'problem1.ipynb'), 'w') as fh:
            fh.write('')

        os.makedirs(join(archive_dir, 'ps1_hacker_02', 'files'))
        with open(join(archive_dir, 'ps1_hacker_02', 'files', 'problem1.ipynb'), 'w') as fh:
            fh.write('')

        with open("nbgrader_config.py", "a") as fh:
            fh.write(dedent(
                """
                c.FileNameCollectorPlugin.valid_ext = ['.ipynb', '.txt']
                c.FileNameCollectorPlugin.named_regexp = (
                    r".+ps1_(?P<student_id>\w+)_[0-9]+\W+(?P<file_id>.+)"
                )
                """
            ))

        run_nbgrader(["zip_collect", "ps1"], retcode=1)
        assert os.path.isdir(extracted_dir)
        assert len(os.listdir(extracted_dir)) == 2
        assert not os.path.isdir(submitted_dir)
