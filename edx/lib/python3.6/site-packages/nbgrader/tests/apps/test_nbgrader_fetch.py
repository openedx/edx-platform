import os
from os.path import join

from .. import run_nbgrader
from .base import BaseTestApp
from .conftest import notwindows


@notwindows
class TestNbGraderFetch(BaseTestApp):

    def _release(self, assignment, exchange, course_dir, course="abc101"):
        self._copy_file(join("files", "test.ipynb"), join(course_dir, "release", "ps1", "p1.ipynb"))
        run_nbgrader([
            "release", assignment,
            "--course", course,
            "--Exchange.root={}".format(exchange)
        ])

    def _fetch(self, assignment, exchange, flags=None, retcode=0, course="abc101"):
        cmd = [
            "fetch", assignment,
            "--course", course,
            "--Exchange.root={}".format(exchange)
        ]

        if flags is not None:
            cmd.extend(flags)

        run_nbgrader(cmd, retcode=retcode)

    def test_help(self):
        """Does the help display without error?"""
        run_nbgrader(["fetch", "--help-all"])

    def test_no_course_id(self, exchange, course_dir):
        """Does releasing without a course id thrown an error?"""
        self._release("ps1", exchange, course_dir)
        cmd = [
            "fetch", "ps1",
            "--Exchange.root={}".format(exchange)
        ]
        run_nbgrader(cmd, retcode=1)

    def test_fetch(self, exchange, course_dir):
        self._release("ps1", exchange, course_dir)
        self._fetch("ps1", exchange)
        assert os.path.isfile(join("ps1", "p1.ipynb"))

        # make sure it fails if the assignment already exists
        self._fetch("ps1", exchange, retcode=1)

        # make sure it fails even if the assignment is incomplete
        os.remove(join("ps1", "p1.ipynb"))
        self._fetch("ps1", exchange, retcode=1)

        # make sure it passes if the --replace flag is given
        self._fetch("ps1", exchange, flags=["--replace"])
        assert os.path.isfile(join("ps1", "p1.ipynb"))

        # make sure the --replace flag doesn't overwrite files, though
        self._copy_file(join("files", "submitted-changed.ipynb"), join("ps1", "p1.ipynb"))
        with open(join("ps1", "p1.ipynb"), "r") as fh:
            contents1 = fh.read()
        self._fetch("ps1", exchange, flags=["--replace"])
        with open(join("ps1", "p1.ipynb"), "r") as fh:
            contents2 = fh.read()
        assert contents1 == contents2

    def test_fetch_with_assignment_flag(self, exchange, course_dir):
        self._release("ps1", exchange, course_dir)
        self._fetch("--assignment=ps1", exchange)
        assert os.path.isfile(join("ps1", "p1.ipynb"))

    def test_fetch_multiple_courses(self, exchange, course_dir):
        self._release("ps1", exchange, course_dir, course="abc101")
        self._fetch("ps1", exchange, course="abc101", flags=["--Exchange.path_includes_course=True"])
        assert os.path.isfile(join("abc101", "ps1", "p1.ipynb"))

        self._release("ps1", exchange, course_dir, course="abc102")
        self._fetch("ps1", exchange, course="abc102", flags=["--Exchange.path_includes_course=True"])
        assert os.path.isfile(join("abc102", "ps1", "p1.ipynb"))
