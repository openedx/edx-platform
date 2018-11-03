import os
import re
from textwrap import dedent

from traitlets import List, Bool, default

from ..api import Gradebook, MissingEntry
from .base import BaseConverter, NbGraderException
from ..preprocessors import (
    IncludeHeaderFooter,
    ClearSolutions,
    LockCells,
    ComputeChecksums,
    SaveCells,
    CheckCellMetadata,
    ClearOutput,
    ClearHiddenTests,
)


class Assign(BaseConverter):

    create_assignment = Bool(
        False,
        help=dedent(
            """
            Whether to create the assignment at runtime if it does not
            already exist.
            """
        )
    ).tag(config=True)

    no_database = Bool(
        False,
        help=dedent(
            """
            Do not save information about the assignment into the database.
            """
        )
    ).tag(config=True)

    @default("permissions")
    def _permissions_default(self):
        return 644

    @property
    def _input_directory(self):
        return self.coursedir.source_directory

    @property
    def _output_directory(self):
        return self.coursedir.release_directory

    preprocessors = List([
        IncludeHeaderFooter,
        LockCells,
        ClearSolutions,
        ClearOutput,
        CheckCellMetadata,
        ComputeChecksums,
        SaveCells,
        ClearHiddenTests,
        ComputeChecksums,
        CheckCellMetadata,
    ])
    # NB: ClearHiddenTests must come after ComputeChecksums and SaveCells.
    # ComputerChecksums must come again after ClearHiddenTests.

    def __init__(self, coursedir=None, **kwargs):
        super(Assign, self).__init__(coursedir=coursedir, **kwargs)

    def _clean_old_notebooks(self, assignment_id, student_id):
        with Gradebook(self.coursedir.db_url) as gb:
            assignment = gb.find_assignment(assignment_id)
            regexp = re.escape(os.path.sep).join([
                self._format_source("(?P<assignment_id>.*)", "(?P<student_id>.*)", escape=True),
                "(?P<notebook_id>.*).ipynb"
            ])

            # find a set of notebook ids for new notebooks
            new_notebook_ids = set([])
            for notebook in self.notebooks:
                m = re.match(regexp, notebook)
                if m is None:
                    raise NbGraderException("Could not match '%s' with regexp '%s'", notebook, regexp)
                gd = m.groupdict()
                if gd['assignment_id'] == assignment_id and gd['student_id'] == student_id:
                    new_notebook_ids.add(gd['notebook_id'])

            # pull out the existing notebook ids
            old_notebook_ids = set(x.name for x in assignment.notebooks)

            # no added or removed notebooks, so nothing to do
            if old_notebook_ids == new_notebook_ids:
                return

            # some notebooks have been removed, but there are submissions associated
            # with the assignment, so we don't want to overwrite stuff
            if len(assignment.submissions) > 0:
                msg = "Cannot modify existing assignment '%s' because there are submissions associated with it" % assignment
                self.log.error(msg)
                raise NbGraderException(msg)

            # remove the old notebooks
            for notebook_id in (old_notebook_ids - new_notebook_ids):
                self.log.warning("Removing notebook '%s' from the gradebook", notebook_id)
                gb.remove_notebook(notebook_id, assignment_id)

    def init_assignment(self, assignment_id, student_id):
        super(Assign, self).init_assignment(assignment_id, student_id)

        # try to get the assignment from the database, and throw an error if it
        # doesn't exist
        if not self.no_database:
            assignment = {}
            for a in self.coursedir.db_assignments:
                if a['name'] == assignment_id:
                    assignment = a.copy()
                    break

            if assignment or self.create_assignment:
                if 'name' in assignment:
                    del assignment['name']
                self.log.info("Updating/creating assignment '%s': %s", assignment_id, assignment)
                with Gradebook(self.coursedir.db_url) as gb:
                    gb.update_or_create_assignment(assignment_id, **assignment)

            else:
                with Gradebook(self.coursedir.db_url) as gb:
                    try:
                        gb.find_assignment(assignment_id)
                    except MissingEntry:
                        msg = "No assignment called '%s' exists in the database" % assignment_id
                        self.log.error(msg)
                        raise NbGraderException(msg)

            # check if there are any extra notebooks in the db that are no longer
            # part of the assignment, and if so, remove them
            if self.coursedir.notebook_id == "*":
                self._clean_old_notebooks(assignment_id, student_id)

    def start(self):
        old_student_id = self.coursedir.student_id
        self.coursedir.student_id = '.'
        try:
            super(Assign, self).start()
        finally:
            self.coursedir.student_id = old_student_id
