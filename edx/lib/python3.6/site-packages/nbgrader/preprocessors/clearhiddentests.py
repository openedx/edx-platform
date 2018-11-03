import re

from traitlets import Bool, Unicode
from textwrap import dedent

from . import NbGraderPreprocessor
from .. import utils


class ClearHiddenTests(NbGraderPreprocessor):

    begin_test_delimeter = Unicode(
        "BEGIN HIDDEN TESTS",
        help="The delimiter marking the beginning of hidden tests cases"
    ).tag(config=True)

    end_test_delimeter = Unicode(
        "END HIDDEN TESTS",
        help="The delimiter marking the end of hidden tests cases"
    ).tag(config=True)

    enforce_metadata = Bool(
        True,
        help=dedent(
            """
            Whether or not to complain if cells containing hidden test regions
            are not marked as grade cells. WARNING: this will potentially cause
            things to break if you are using the full nbgrader pipeline. ONLY
            disable this option if you are only ever planning to use nbgrader
            assign.
            """
        )
    ).tag(config=True)

    def _remove_hidden_test_region(self, cell):
        """Find a region in the cell that is delimeted by
        `self.begin_test_delimeter` and `self.end_test_delimeter` (e.g.  ###
        BEGIN HIDDEN TESTS and ### END HIDDEN TESTS). Remove that region
        depending the cell type.

        This modifies the cell in place, and then returns True if a
        hidden test region was removed, and False otherwise.
        """
        # pull out the cell input/source
        lines = cell.source.split("\n")

        new_lines = []
        in_test = False
        removed_test = False

        for line in lines:
            # begin the test area
            if self.begin_test_delimeter in line:

                # check to make sure this isn't a nested BEGIN HIDDEN TESTS
                # region
                if in_test:
                    raise RuntimeError(
                        "Encountered nested begin hidden tests statements")
                in_test = True
                removed_test = True

            # end the solution area
            elif self.end_test_delimeter in line:
                in_test = False

            # add lines as long as it's not in the hidden tests region
            elif not in_test:
                new_lines.append(line)

        # we finished going through all the lines, but didn't find a
        # matching END HIDDEN TESTS statment
        if in_test:
            raise RuntimeError("No end hidden tests statement found")

        # replace the cell source
        cell.source = "\n".join(new_lines)

        return removed_test

    def preprocess(self, nb, resources):
        nb, resources = super(ClearHiddenTests, self).preprocess(nb, resources)
        if 'celltoolbar' in nb.metadata:
            del nb.metadata['celltoolbar']
        return nb, resources

    def preprocess_cell(self, cell, resources, cell_index):
        # remove hidden test regions
        removed_test = self._remove_hidden_test_region(cell)

        # determine whether the cell is a grade cell
        is_grade = utils.is_grade(cell)

        # check that it is marked as a grade cell if we remove a test
        # region -- if it's not, then this is a problem, because the cell needs
        # to be given an id
        if not is_grade and removed_test:
            if self.enforce_metadata:
                raise RuntimeError(
                    "Hidden test region detected in a non-grade cell; "
                    "please make sure all solution regions are within "
                    "'Autograder tests' cells."
                )

        return cell, resources
