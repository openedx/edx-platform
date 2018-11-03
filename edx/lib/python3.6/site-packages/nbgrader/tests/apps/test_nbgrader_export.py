import os

from os.path import join
from ...utils import remove
from .. import run_nbgrader
from .base import BaseTestApp


class TestNbGraderExport(BaseTestApp):

    def test_help(self):
        """Does the help display without error?"""
        run_nbgrader(["export", "--help-all"])

    def test_export(self, db, course_dir):
        with open("nbgrader_config.py", "a") as fh:
            fh.write("""c.CourseDirectory.db_assignments = [
                dict(name='ps1', duedate='2015-02-02 14:58:23.948203 PST'),
                dict(name='ps2', duedate='2015-02-02 14:58:23.948203 PST')]\n""")
            fh.write("""c.CourseDirectory.db_students = [dict(id="foo"), dict(id="bar")]""")

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps2", "p1.ipynb"))
        run_nbgrader(["assign", "ps1", "--db", db])
        run_nbgrader(["assign", "ps2", "--db", db])

        self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "submitted", "bar", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "submitted", "foo", "ps2", "p1.ipynb"))
        run_nbgrader(["autograde", "ps1", "--db", db])
        run_nbgrader(["autograde", "ps2", "--db", db])

        run_nbgrader(["export", "--db", db])
        assert os.path.isfile("grades.csv")
        with open("grades.csv", "r") as fh:
            contents = fh.readlines()
        assert len(contents) == 5

        run_nbgrader(["export", "--db", db, "--to", "mygrades.csv"])
        assert os.path.isfile("mygrades.csv")

        remove("grades.csv")
        run_nbgrader(["export", "--db", db, "--exporter", "nbgrader.plugins.CsvExportPlugin"])
        assert os.path.isfile("grades.csv")

        run_nbgrader(["export", "--db", db, "--exporter=nbgrader.tests.apps.files.myexporter.MyExporter", "--to", "foo.txt"])
        assert os.path.isfile("foo.txt")
