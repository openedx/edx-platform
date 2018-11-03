from os.path import join

from .. import run_nbgrader
from .base import BaseTestApp


class TestNbGraderValidate(BaseTestApp):

    def test_help(self):
        """Does the help display without error?"""
        run_nbgrader(["validate", "--help-all"])

    def test_validate_unchanged(self):
        """Does the validation fail on an unchanged notebook?"""
        self._copy_file(join("files", "submitted-unchanged.ipynb"), "submitted-unchanged.ipynb")
        output = run_nbgrader(["validate", "submitted-unchanged.ipynb"], stdout=True)
        assert output.splitlines()[0] == "VALIDATION FAILED ON 3 CELL(S)! If you submit your assignment as it is, you WILL NOT"

    def test_validate_changed(self):
        """Does the validation pass on an changed notebook?"""
        self._copy_file(join("files", "submitted-changed.ipynb"), "submitted-changed.ipynb")
        output = run_nbgrader(["validate", "submitted-changed.ipynb"], stdout=True)
        assert output.strip() == "Success! Your notebook passes all the tests."

    def test_invert_validate_unchanged(self):
        """Does the inverted validation pass on an unchanged notebook?"""
        self._copy_file(join("files", "submitted-unchanged.ipynb"), "submitted-unchanged.ipynb")
        output = run_nbgrader(["validate", "submitted-unchanged.ipynb", "--invert"], stdout=True)
        assert output.splitlines()[0] == "NOTEBOOK PASSED ON 1 CELL(S)!"

    def test_invert_validate_changed(self):
        """Does the inverted validation fail on a changed notebook?"""
        self._copy_file(join("files", "submitted-changed.ipynb"), "submitted-changed.ipynb")
        output = run_nbgrader(["validate", "submitted-changed.ipynb", "--invert"], stdout=True)
        assert output.splitlines()[0] == "NOTEBOOK PASSED ON 2 CELL(S)!"

    def test_grade_cell_changed(self):
        """Does the validate fail if a grade cell has changed?"""
        self._copy_file(join("files", "submitted-grade-cell-changed.ipynb"), "submitted-grade-cell-changed.ipynb")
        output = run_nbgrader(["validate", "submitted-grade-cell-changed.ipynb"], stdout=True)
        assert output.splitlines()[0] == "THE CONTENTS OF 1 TEST CELL(S) HAVE CHANGED! This might mean that even though the tests"

    def test_grade_cell_changed_ignore_checksums(self):
        """Does the validate pass if a grade cell has changed but we're ignoring checksums?"""
        self._copy_file(join("files", "submitted-grade-cell-changed.ipynb"), "submitted-grade-cell-changed.ipynb")
        output = run_nbgrader([
            "validate", "submitted-grade-cell-changed.ipynb",
            "--Validator.ignore_checksums=True"
        ], stdout=True)
        assert output.splitlines()[0] == "Success! Your notebook passes all the tests."

    def test_invert_grade_cell_changed(self):
        """Does the validate fail if a grade cell has changed, even with --invert?"""
        self._copy_file(join("files", "submitted-grade-cell-changed.ipynb"), "submitted-grade-cell-changed.ipynb")
        output = run_nbgrader(["validate", "submitted-grade-cell-changed.ipynb", "--invert"], stdout=True)
        assert output.splitlines()[0] == "THE CONTENTS OF 1 TEST CELL(S) HAVE CHANGED! This might mean that even though the tests"

    def test_invert_grade_cell_changed_ignore_checksums(self):
        """Does the validate fail if a grade cell has changed with --invert and ignoring checksums?"""
        self._copy_file(join("files", "submitted-grade-cell-changed.ipynb"), "submitted-grade-cell-changed.ipynb")
        output = run_nbgrader([
            "validate", "submitted-grade-cell-changed.ipynb",
            "--invert",
            "--Validator.ignore_checksums=True"
        ], stdout=True)
        assert output.splitlines()[0] == "NOTEBOOK PASSED ON 2 CELL(S)!"

    def test_validate_unchanged_ignore_checksums(self):
        """Does the validation fail on an unchanged notebook with ignoring checksums?"""
        self._copy_file(join("files", "submitted-unchanged.ipynb"), "submitted-unchanged.ipynb")
        output = run_nbgrader([
            "validate", "submitted-unchanged.ipynb",
            "--Validator.ignore_checksums=True"
        ], stdout=True)
        assert output.splitlines()[0] == "VALIDATION FAILED ON 1 CELL(S)! If you submit your assignment as it is, you WILL NOT"

    def test_locked_cell_changed(self):
        """Does the validate fail if a locked cell has changed?"""
        self._copy_file(join("files", "submitted-locked-cell-changed.ipynb"), "submitted-locked-cell-changed.ipynb")
        output = run_nbgrader(["validate", "submitted-locked-cell-changed.ipynb"], stdout=True)
        assert output.splitlines()[0] == "THE CONTENTS OF 2 TEST CELL(S) HAVE CHANGED! This might mean that even though the tests"

    def test_locked_cell_changed_ignore_checksums(self):
        """Does the validate pass if a locked cell has changed but we're ignoring checksums?"""
        self._copy_file(join("files", "submitted-locked-cell-changed.ipynb"), "submitted-locked-cell-changed.ipynb")
        output = run_nbgrader([
            "validate", "submitted-locked-cell-changed.ipynb",
            "--Validator.ignore_checksums=True"
        ], stdout=True)
        assert output.splitlines()[0] == "VALIDATION FAILED ON 1 CELL(S)! If you submit your assignment as it is, you WILL NOT"

    def test_invert_locked_cell_changed(self):
        """Does the validate fail if a locked cell has changed, even with --invert?"""
        self._copy_file(join("files", "submitted-locked-cell-changed.ipynb"), "submitted-locked-cell-changed.ipynb")
        output = run_nbgrader(["validate", "submitted-locked-cell-changed.ipynb", "--invert"], stdout=True)
        assert output.splitlines()[0] == "THE CONTENTS OF 2 TEST CELL(S) HAVE CHANGED! This might mean that even though the tests"

    def test_invert_locked_cell_changed_ignore_checksums(self):
        """Does the validate fail if a locked cell has changed with --invert and ignoring checksums?"""
        self._copy_file(join("files", "submitted-locked-cell-changed.ipynb"), "submitted-locked-cell-changed.ipynb")
        output = run_nbgrader([
            "validate", "submitted-locked-cell-changed.ipynb",
            "--invert",
            "--Validator.ignore_checksums=True"
        ], stdout=True)
        assert output.splitlines()[0] == "NOTEBOOK PASSED ON 1 CELL(S)!"

    def test_validate_glob(self):
        """Does the validation work when we glob filenames?"""
        self._copy_file(join("files", "submitted-unchanged.ipynb"), "nb1.ipynb")
        self._copy_file(join("files", "submitted-changed.ipynb"), "nb2.ipynb")
        self._copy_file(join("files", "submitted-changed.ipynb"), "nb3.ipynb")
        run_nbgrader(["validate", "*.ipynb"])
        run_nbgrader(["validate", "nb1.ipynb", "nb2.ipynb"])
        run_nbgrader(["validate", "nb1.ipynb", "nb2.ipynb", "nb3.ipynb"])
        run_nbgrader(["validate"], retcode=1)
