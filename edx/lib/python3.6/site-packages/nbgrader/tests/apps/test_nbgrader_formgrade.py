from .. import run_nbgrader
from .base import BaseTestApp


class TestNbGraderFormgrade(BaseTestApp):

    def test_help(self):
        """Does the help display without error?"""
        run_nbgrader(["formgrade", "--help-all"])
