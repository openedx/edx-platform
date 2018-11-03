import os
import shutil

from textwrap import dedent
from traitlets import Bool, List

from .base import BaseConverter, NbGraderException
from ..preprocessors import (
    AssignLatePenalties, ClearOutput, DeduplicateIds, OverwriteCells, SaveAutoGrades,
    Execute, LimitOutput, OverwriteKernelspec, CheckCellMetadata)
from ..api import Gradebook, MissingEntry
from .. import utils


class Autograde(BaseConverter):

    create_student = Bool(
        False,
        help=dedent(
            """
            Whether to create the student at runtime if it does not
            already exist.
            """
        )
    ).tag(config=True)

    _sanitizing = True

    @property
    def _input_directory(self):
        if self._sanitizing:
            return self.coursedir.submitted_directory
        else:
            return self.coursedir.autograded_directory

    @property
    def _output_directory(self):
        return self.coursedir.autograded_directory

    sanitize_preprocessors = List([
        ClearOutput,
        DeduplicateIds,
        OverwriteKernelspec,
        OverwriteCells,
        CheckCellMetadata
    ])
    autograde_preprocessors = List([
        Execute,
        LimitOutput,
        SaveAutoGrades,
        AssignLatePenalties,
        CheckCellMetadata
    ])

    preprocessors = List([])

    def init_assignment(self, assignment_id, student_id):
        super(Autograde, self).init_assignment(assignment_id, student_id)

        # try to get the student from the database, and throw an error if it
        # doesn't exist
        student = {}
        for s in self.coursedir.db_students:
            if s['id'] == student_id:
                student = s.copy()
                break

        if student or self.create_student:
            if 'id' in student:
                del student['id']
            self.log.info("Creating/updating student with ID '%s': %s", student_id, student)
            with Gradebook(self.coursedir.db_url) as gb:
                gb.update_or_create_student(student_id, **student)

        else:
            with Gradebook(self.coursedir.db_url) as gb:
                try:
                    gb.find_student(student_id)
                except MissingEntry:
                    msg = "No student with ID '%s' exists in the database" % student_id
                    self.log.error(msg)
                    raise NbGraderException(msg)

        # make sure the assignment exists
        with Gradebook(self.coursedir.db_url) as gb:
            try:
                gb.find_assignment(assignment_id)
            except MissingEntry:
                msg = "No assignment with ID '%s' exists in the database" % assignment_id
                self.log.error(msg)
                raise NbGraderException(msg)

        # try to read in a timestamp from file
        src_path = self._format_source(assignment_id, student_id)
        timestamp = self.coursedir.get_existing_timestamp(src_path)
        with Gradebook(self.coursedir.db_url) as gb:
            if timestamp:
                submission = gb.update_or_create_submission(
                    assignment_id, student_id, timestamp=timestamp)
                self.log.info("%s submitted at %s", submission, timestamp)

                # if the submission is late, print out how many seconds late it is
                if timestamp and submission.total_seconds_late > 0:
                    self.log.warning("%s is %s seconds late", submission, submission.total_seconds_late)
            else:
                submission = gb.update_or_create_submission(assignment_id, student_id)

        # copy files over from the source directory
        self.log.info("Overwriting files with master versions from the source directory")
        dest_path = self._format_dest(assignment_id, student_id)
        source_path = self.coursedir.format_path(self.coursedir.source_directory, '.', assignment_id)
        source_files = utils.find_all_files(source_path, self.coursedir.ignore + ["*.ipynb"])

        # copy them to the build directory
        for filename in source_files:
            dest = os.path.join(dest_path, os.path.relpath(filename, source_path))
            if not os.path.exists(os.path.dirname(dest)):
                os.makedirs(os.path.dirname(dest))
            if os.path.exists(dest):
                os.remove(dest)
            self.log.info("Copying %s -> %s", filename, dest)
            shutil.copy(filename, dest)

        # ignore notebooks that aren't in the database
        notebooks = []
        with Gradebook(self.coursedir.db_url) as gb:
            for notebook in self.notebooks:
                notebook_id = os.path.splitext(os.path.basename(notebook))[0]
                try:
                    gb.find_notebook(notebook_id, assignment_id)
                except MissingEntry:
                    self.log.warning("Skipping unknown notebook: %s", notebook)
                    continue
                else:
                    notebooks.append(notebook)
        self.notebooks = notebooks
        if len(self.notebooks) == 0:
            msg = "No notebooks found, did you forget to run 'nbgrader assign'?"
            self.log.error(msg)
            raise NbGraderException(msg)

        # check for missing notebooks and give them a score of zero if they
        # do not exist
        with Gradebook(self.coursedir.db_url) as gb:
            assignment = gb.find_assignment(assignment_id)
            for notebook in assignment.notebooks:
                path = os.path.join(self.coursedir.format_path(
                    self.coursedir.submitted_directory,
                    student_id,
                    assignment_id), "{}.ipynb".format(notebook.name))
                if not os.path.exists(path):
                    self.log.warning("No submitted file: {}".format(path))
                    submission = gb.find_submission_notebook(
                        notebook.name, assignment_id, student_id)
                    for grade in submission.grades:
                        grade.auto_score = 0
                        grade.needs_manual_grade = False
                    gb.db.commit()

    def _init_preprocessors(self):
        self.exporter._preprocessors = []
        if self._sanitizing:
            preprocessors = self.sanitize_preprocessors
        else:
            preprocessors = self.autograde_preprocessors

        for pp in preprocessors:
            self.exporter.register_preprocessor(pp)

    def convert_single_notebook(self, notebook_filename):
        self.log.info("Sanitizing %s", notebook_filename)
        self._sanitizing = True
        self._init_preprocessors()
        super(Autograde, self).convert_single_notebook(notebook_filename)

        notebook_filename = os.path.join(self.writer.build_directory, os.path.basename(notebook_filename))
        self.log.info("Autograding %s", notebook_filename)
        self._sanitizing = False
        self._init_preprocessors()
        try:
            super(Autograde, self).convert_single_notebook(notebook_filename)
        finally:
            self._sanitizing = True
