from os.path import join

from .. import run_nbgrader
from .base import BaseTestApp


class TestNbGraderUpdate(BaseTestApp):

    def test_help(self):
        """Does the help display without error?"""
        run_nbgrader(["update", "--help-all"])

    def test_no_args(self):
        """Is there an error if no arguments are given?"""
        run_nbgrader(["update"], retcode=1)

    def test_missing_file(self):
        """Is there an error if the file doesn't exist?"""
        run_nbgrader(["update", "foo"], retcode=1)

    def test_not_a_notebook(self):
        """Are non-notebooks ignored?"""
        with open("foo", "w") as fh:
            fh.write("blah")
        run_nbgrader(["update", "foo"])

    def test_single_notebook(self):
        """Does it work with just a single notebook?"""
        self._copy_file(join("files", "test-v0.ipynb"), "p1.ipynb")
        run_nbgrader(["update", "p1.ipynb"])

    def test_validate(self):
        """Does turning validation on/off work correctly?"""

        # updating shouldn't work if we're validating, too
        self._copy_file(join("files", "test-v0-invalid.ipynb"), "p1.ipynb")
        run_nbgrader(["update", "p1.ipynb"], retcode=1)

        # updating should work, but then validation should fail
        self._copy_file(join("files", "test-v0-invalid.ipynb"), "p1.ipynb")
        run_nbgrader(["update", "p1.ipynb", "--UpdateApp.validate=False"])
        run_nbgrader(["validate", "p1.ipynb"], retcode=1)

    def test_update_assign(self, db, course_dir):
        with open("nbgrader_config.py", "a") as fh:
            fh.write("""c.CourseDirectory.db_assignments = [dict(name='ps1', duedate='2015-02-02 14:58:23.948203 PST')]\n""")
            fh.write("""c.CourseDirectory.db_students = [dict(id="foo"), dict(id="bar")]""")

        self._copy_file(join("files", "test-v0.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_nbgrader(["assign", "ps1", "--db", db], retcode=1)

        # now update the metadata
        run_nbgrader(["update", course_dir])

        # now assign should suceed
        run_nbgrader(["assign", "ps1", "--db", db])

    def test_update_autograde(self, db, course_dir):
        with open("nbgrader_config.py", "a") as fh:
            fh.write("""c.CourseDirectory.db_assignments = [dict(name='ps1', duedate='2015-02-02 14:58:23.948203 PST')]\n""")
            fh.write("""c.CourseDirectory.db_students = [dict(id="foo"), dict(id="bar")]""")

        self._copy_file(join("files", "test.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_nbgrader(["assign", "ps1", "--db", db])

        # autograde should fail on old metadata, too
        self._copy_file(join("files", "test-v0.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        run_nbgrader(["autograde", "ps1", "--db", db], retcode=1)

        # now update the metadata
        run_nbgrader(["update", course_dir])

        # now autograde should suceed
        run_nbgrader(["autograde", "ps1", "--db", db])

    def test_update_autograde_old_assign(self, db, course_dir):
        with open("nbgrader_config.py", "a") as fh:
            fh.write("""c.CourseDirectory.db_assignments = [dict(name='ps1', duedate='2015-02-02 14:58:23.948203 PST')]\n""")
            fh.write("""c.CourseDirectory.db_students = [dict(id="foo"), dict(id="bar")]""")

        self._copy_file(join("files", "test-v0.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_nbgrader(["assign", "ps1", "--db", db, "--CheckCellMetadata.enabled=False"])

        # autograde should fail on old metadata, too
        self._copy_file(join(course_dir, "release", "ps1", "p1.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        run_nbgrader(["autograde", "ps1", "--db", db], retcode=1)

        # now update the metadata
        run_nbgrader(["update", join(course_dir, "submitted")])

        # now autograde should suceed
        run_nbgrader(["autograde", "ps1", "--db", db])

