import pytest
import datetime
import shutil
import os

from textwrap import dedent
from os.path import join

from ...api import Gradebook, MissingEntry
from .. import run_nbgrader
from .base import BaseTestApp


class TestNbGraderDb(BaseTestApp):

    def test_help(self):
        """Does the help display without error?"""
        run_nbgrader(["db", "--help-all"])
        run_nbgrader(["db", "student", "--help-all"])
        run_nbgrader(["db", "student", "list", "--help-all"])
        run_nbgrader(["db", "student", "remove", "--help-all"])
        run_nbgrader(["db", "student", "add", "--help-all"])
        run_nbgrader(["db", "student", "import", "--help-all"])
        run_nbgrader(["db", "assignment", "--help-all"])
        run_nbgrader(["db", "assignment", "list", "--help-all"])
        run_nbgrader(["db", "assignment", "remove", "--help-all"])
        run_nbgrader(["db", "assignment", "add", "--help-all"])
        run_nbgrader(["db", "assignment", "import", "--help-all"])

    def test_no_args(self):
        """Is there an error if no arguments are given?"""
        run_nbgrader(["db"], retcode=0)
        run_nbgrader(["db", "student"], retcode=0)
        run_nbgrader(["db", "student", "remove"], retcode=1)
        run_nbgrader(["db", "student", "add"], retcode=1)
        run_nbgrader(["db", "student", "import"], retcode=1)
        run_nbgrader(["db", "assignment"], retcode=0)
        run_nbgrader(["db", "assignment", "remove"], retcode=1)
        run_nbgrader(["db", "assignment", "add"], retcode=1)
        run_nbgrader(["db", "assignment", "import"], retcode=1)

    def test_student_add(self, db):
        run_nbgrader(["db", "student", "add", "foo", "--db", db])
        with Gradebook(db) as gb:
            student = gb.find_student("foo")
            assert student.last_name is None
            assert student.first_name is None
            assert student.email is None

        run_nbgrader(["db", "student", "add", "foo", "--last-name=FooBar", "--db", db])
        with Gradebook(db) as gb:
            student = gb.find_student("foo")
            assert student.last_name == "FooBar"
            assert student.first_name is None
            assert student.email is None

        run_nbgrader(["db", "student", "add", "foo", "--first-name=FooBar", "--db", db])
        with Gradebook(db) as gb:
            student = gb.find_student("foo")
            assert student.last_name is None
            assert student.first_name == "FooBar"
            assert student.email is None

        run_nbgrader(["db", "student", "add", "foo", "--email=foo@bar.com", "--db", db])
        with Gradebook(db) as gb:
            student = gb.find_student("foo")
            assert student.last_name is None
            assert student.first_name is None
            assert student.email == "foo@bar.com"

    def test_student_remove(self, db):
        run_nbgrader(["db", "student", "add", "foo", "--db", db])
        with Gradebook(db) as gb:
            student = gb.find_student("foo")
            assert student.last_name is None
            assert student.first_name is None
            assert student.email is None

        run_nbgrader(["db", "student", "remove", "foo", "--db", db])
        with Gradebook(db) as gb:
            with pytest.raises(MissingEntry):
                gb.find_student("foo")

        # running it again should give an error
        run_nbgrader(["db", "student", "remove", "foo", "--db", db], retcode=1)

    def test_student_remove_with_submissions(self, db, course_dir):
        run_nbgrader(["db", "student", "add", "foo", "--db", db])
        run_nbgrader(["db", "assignment", "add", "ps1", "--db", db])
        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_nbgrader(["assign", "ps1", "--db", db])
        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        run_nbgrader(["autograde", "ps1", "--db", db])

        with Gradebook(db) as gb:
            gb.find_student("foo")

        # it should fail if we don't run with --force
        run_nbgrader(["db", "student", "remove", "foo", "--db", db], retcode=1)

        # make sure we can still find the student
        with Gradebook(db) as gb:
            gb.find_student("foo")

        # now force it to complete
        run_nbgrader(["db", "student", "remove", "foo", "--force", "--db", db])

            # student should be gone
        with Gradebook(db) as gb:
            with pytest.raises(MissingEntry):
                gb.find_student("foo")

    def test_student_list(self, db):
        run_nbgrader(["db", "student", "add", "foo", "--first-name=abc", "--last-name=xyz", "--email=foo@bar.com", "--db", db])
        run_nbgrader(["db", "student", "add", "bar", "--db", db])
        out = run_nbgrader(["db", "student", "list", "--db", db], stdout=True)
        assert out == dedent(
            """
            There are 2 students in the database:
            bar (None, None) -- None
            foo (xyz, abc) -- foo@bar.com
            """
        ).strip() + "\n"

    def test_student_import(self, db, temp_cwd):
        with open("students.csv", "w") as fh:
            fh.write(dedent(
                """
                id,first_name,last_name,email
                foo,abc,xyz,foo@bar.com
                bar,,,
                """
            ).strip())

        run_nbgrader(["db", "student", "import", "students.csv", "--db", db])
        with Gradebook(db) as gb:
            student = gb.find_student("foo")
            assert student.last_name == "xyz"
            assert student.first_name == "abc"
            assert student.email == "foo@bar.com"
            student = gb.find_student("bar")
            assert student.last_name is None
            assert student.first_name is None
            assert student.email is None

        # check that it fails when no id column is given
        with open("students.csv", "w") as fh:
            fh.write(dedent(
                """
                first_name,last_name,email
                abc,xyz,foo@bar.com
                ,,
                """
            ).strip())

        run_nbgrader(["db", "student", "import", "students.csv", "--db", db], retcode=1)

        # check that it works ok with extra and missing columns
        with open("students.csv", "w") as fh:
            fh.write(dedent(
                """
                id,first_name,last_name,foo
                foo,abc,xyzzzz,blah
                bar,,,
                """
            ).strip())

        run_nbgrader(["db", "student", "import", "students.csv", "--db", db])
        with Gradebook(db) as gb:
            student = gb.find_student("foo")
            assert student.last_name == "xyzzzz"
            assert student.first_name == "abc"
            assert student.email == "foo@bar.com"
            student = gb.find_student("bar")
            assert student.last_name is None
            assert student.first_name is None
            assert student.email is None


    def test_student_import_csv_spaces(self, db, temp_cwd):
        with open("students.csv", "w") as fh:
            fh.write(dedent(
                """
                id,first_name,last_name, email
                foo,abc,xyz,foo@bar.com
                bar,,,
                """
            ).strip())

        run_nbgrader(["db", "student", "import", "students.csv", "--db", db])
        with Gradebook(db) as gb:
            student = gb.find_student("foo")
            assert student.last_name == "xyz"
            assert student.first_name == "abc"
            assert student.email == "foo@bar.com"
            student = gb.find_student("bar")
            assert student.last_name is None
            assert student.first_name is None
            assert student.email is None

    def test_assignment_add(self, db):
        run_nbgrader(["db", "assignment", "add", "foo", "--db", db])
        with Gradebook(db) as gb:
            assignment = gb.find_assignment("foo")
            assert assignment.duedate is None

        run_nbgrader(["db", "assignment", "add", "foo", '--duedate="Sun Jan 8 2017 4:31:22 PM"', "--db", db])
        with Gradebook(db) as gb:
            assignment = gb.find_assignment("foo")
            assert assignment.duedate == datetime.datetime(2017, 1, 8, 16, 31, 22)

    def test_assignment_remove(self, db):
        run_nbgrader(["db", "assignment", "add", "foo", "--db", db])
        with Gradebook(db) as gb:
            assignment = gb.find_assignment("foo")
            assert assignment.duedate is None

        run_nbgrader(["db", "assignment", "remove", "foo", "--db", db])
        with Gradebook(db) as gb:
            with pytest.raises(MissingEntry):
                gb.find_assignment("foo")

        # running it again should give an error
        run_nbgrader(["db", "assignment", "remove", "foo", "--db", db], retcode=1)

    def test_assignment_remove_with_submissions(self, db, course_dir):
        run_nbgrader(["db", "student", "add", "foo", "--db", db])
        run_nbgrader(["db", "assignment", "add", "ps1", "--db", db])
        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        run_nbgrader(["assign", "ps1", "--db", db])
        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "submitted", "foo", "ps1", "p1.ipynb"))
        run_nbgrader(["autograde", "ps1", "--db", db])

        with Gradebook(db) as gb:
            gb.find_assignment("ps1")

        # it should fail if we don't run with --force
        run_nbgrader(["db", "assignment", "remove", "ps1", "--db", db], retcode=1)

        # make sure we can still find the assignment
        with Gradebook(db) as gb:
            gb.find_assignment("ps1")

        # now force it to complete
        run_nbgrader(["db", "assignment", "remove", "ps1", "--force", "--db", db])

            # assignment should be gone
        with Gradebook(db) as gb:
            with pytest.raises(MissingEntry):
                gb.find_assignment("ps1")

    def test_assignment_list(self, db):
        run_nbgrader(["db", "assignment", "add", "foo", '--duedate="Sun Jan 8 2017 4:31:22 PM"', "--db", db])
        run_nbgrader(["db", "assignment", "add", "bar", "--db", db])
        out = run_nbgrader(["db", "assignment", "list", "--db", db], stdout=True)
        assert out == dedent(
            """
            There are 2 assignments in the database:
            bar (due: None)
            foo (due: 2017-01-08 16:31:22)
            """
        ).strip() + "\n"

    def test_assignment_import(self, db, temp_cwd):
        with open("assignments.csv", "w") as fh:
            fh.write(dedent(
                """
                name,duedate
                foo,Sun Jan 8 2017 4:31:22 PM
                bar,
                """
            ).strip())

        run_nbgrader(["db", "assignment", "import", "assignments.csv", "--db", db])
        with Gradebook(db) as gb:
            assignment = gb.find_assignment("foo")
            assert assignment.duedate == datetime.datetime(2017, 1, 8, 16, 31, 22)
            assignment = gb.find_assignment("bar")
            assert assignment.duedate is None


    def test_assignment_import_csv_spaces(self, db, temp_cwd):
        with open("assignments.csv", "w") as fh:
            fh.write(dedent(
                """
                name, duedate
                foo,Sun Jan 8 2017 4:31:22 PM
                bar,
                """
            ).strip())

        run_nbgrader(["db", "assignment", "import", "assignments.csv", "--db", db])
        with Gradebook(db) as gb:
            assignment = gb.find_assignment("foo")
            assert assignment.duedate == datetime.datetime(2017, 1, 8, 16, 31, 22)
            assignment = gb.find_assignment("bar")
            assert assignment.duedate is None

        # check that it fails when no id column is given
        with open("assignments.csv", "w") as fh:
            fh.write(dedent(
                """
                duedate
                Sun Jan 8 2017 4:31:22 PM
                ,
                """
            ).strip())

        run_nbgrader(["db", "assignment", "import", "assignments.csv", "--db", db], retcode=1)

        # check that it works ok with extra and missing columns
        with open("assignments.csv", "w") as fh:
            fh.write(dedent(
                """
                name
                foo
                bar
                """
            ).strip())

        run_nbgrader(["db", "assignment", "import", "assignments.csv", "--db", db])
        with Gradebook(db) as gb:
            assignment = gb.find_assignment("foo")
            assert assignment.duedate == datetime.datetime(2017, 1, 8, 16, 31, 22)
            assignment = gb.find_assignment("bar")
            assert assignment.duedate is None
    def test_upgrade_nodb(self, temp_cwd):
        # test upgrading without a database
        run_nbgrader(["db", "upgrade"])

    def test_upgrade_current_db(self, course_dir):
        # add assignment files
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "source", "ps1", "p2.ipynb"))

        # check that nbgrader assign fails
        run_nbgrader(["assign", "ps1", "--create"])

        # test upgrading with a current database
        run_nbgrader(["db", "upgrade"])

    def test_upgrade_old_db(self, course_dir):
        # add assignment files
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "source", "ps1", "p2.ipynb"))

        # replace the gradebook with an old version
        self._copy_file(join("files", "gradebook.db"), join(course_dir, "gradebook.db"))

        # check that nbgrader assign fails
        run_nbgrader(["assign", "ps1", "--create"], retcode=1)

        # upgrade the database
        run_nbgrader(["db", "upgrade"])

        # check that nbgrader assign passes
        run_nbgrader(["assign", "ps1", "--create"])
