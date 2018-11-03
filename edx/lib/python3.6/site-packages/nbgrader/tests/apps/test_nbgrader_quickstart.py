import os
import sys

from .. import run_nbgrader
from .base import BaseTestApp


class TestNbGraderQuickStart(BaseTestApp):

    def test_help(self):
        """Does the help display without error?"""
        run_nbgrader(["quickstart", "--help-all"])

    def test_no_course_id(self):
        """Is the help displayed when no course id is given?"""
        run_nbgrader(["quickstart"], retcode=1)

    def test_quickstart(self):
        """Is the quickstart example properly generated?"""

        run_nbgrader(["quickstart", "example"])

        # it should fail if it already exists
        run_nbgrader(["quickstart", "example"], retcode=1)

        # it should succeed if --force is given
        os.remove(os.path.join("example", "nbgrader_config.py"))
        run_nbgrader(["quickstart", "example", "--force"])
        assert os.path.exists(os.path.join("example", "nbgrader_config.py"))

        # nbgrader validate should work
        os.chdir("example")
        for nb in os.listdir(os.path.join("source", "ps1")):
            if not nb.endswith(".ipynb"):
                continue
            output = run_nbgrader(["validate", os.path.join("source", "ps1", nb)], stdout=True)
            assert output.strip() == "Success! Your notebook passes all the tests."

        # nbgrader assign should work
        run_nbgrader(["assign", "ps1"])

