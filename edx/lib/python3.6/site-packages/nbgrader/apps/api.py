import glob
import re
import sys
import os
import six
import logging

from traitlets.config import LoggingConfigurable
from traitlets import Instance, Enum, Unicode, observe

from ..coursedir import CourseDirectory
from ..converters import Assign, Autograde
from ..exchange import ExchangeList, ExchangeRelease, ExchangeCollect, ExchangeError
from ..api import MissingEntry, Gradebook, Student, SubmittedAssignment
from ..utils import parse_utc, temp_attrs, capture_log, as_timezone


class NbGraderAPI(LoggingConfigurable):
    """A high-level API for using nbgrader."""

    coursedir = Instance(CourseDirectory, allow_none=True)

    # The log level for the application
    log_level = Enum(
        (0, 10, 20, 30, 40, 50, 'DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL'),
        default_value=logging.INFO,
        help="Set the log level by value or name."
    ).tag(config=True)

    timezone = Unicode(
        "UTC",
        help="Timezone for displaying timestamps"
    ).tag(config=True)

    timestamp_format = Unicode(
        "%Y-%m-%d %H:%M:%S %Z",
        help="Format string for displaying timestamps"
    ).tag(config=True)

    @observe('log_level')
    def _log_level_changed(self, change):
        """Adjust the log level when log_level is set."""
        new = change.new
        if isinstance(new, six.string_types):
            new = getattr(logging, new)
            self.log_level = new
        self.log.setLevel(new)

    def __init__(self, coursedir=None, **kwargs):
        """Initialize the API.

        Arguments
        ---------
        coursedir: :class:`nbgrader.coursedir.CourseDirectory`
            (Optional) A course directory object.
        kwargs:
            Additional keyword arguments (e.g. ``parent``, ``config``)

        """
        self.log.setLevel(self.log_level)
        super(NbGraderAPI, self).__init__(**kwargs)

        if coursedir is None:
            self.coursedir = CourseDirectory(parent=self)
        else:
            self.coursedir = coursedir

        if sys.platform != 'win32':
            lister = ExchangeList(coursedir=self.coursedir, parent=self)
            self.course_id = lister.course_id
            self.exchange = lister.root

            try:
                lister.start()
            except ExchangeError:
                self.exchange_missing = True
            else:
                self.exchange_missing = False

        else:
            self.course_id = ''
            self.exchange = ''
            self.exchange_missing = True

    @property
    def exchange_is_functional(self):
        return self.course_id and not self.exchange_missing and sys.platform != 'win32'

    @property
    def gradebook(self):
        """An instance of :class:`nbgrader.api.Gradebook`.

        Note that each time this property is accessed, a new gradebook is
        created. The user is responsible for destroying the gradebook through
        :func:`~nbgrader.api.Gradebook.close`.

        """
        return Gradebook(self.coursedir.db_url)

    def get_source_assignments(self):
        """Get the names of all assignments in the `source` directory.

        Returns
        -------
        assignments: set
            A set of assignment names

        """
        filenames = glob.glob(self.coursedir.format_path(
            self.coursedir.source_directory,
            student_id='.',
            assignment_id='*'))

        assignments = set([])
        for filename in filenames:
            # skip files that aren't directories
            if not os.path.isdir(filename):
                continue

            # parse out the assignment name
            regex = self.coursedir.format_path(
                self.coursedir.source_directory,
                student_id='.',
                assignment_id='(?P<assignment_id>.*)',
                escape=True)

            matches = re.match(regex, filename)
            if matches:
                assignments.add(matches.groupdict()['assignment_id'])

        return assignments

    def get_released_assignments(self):
        """Get the names of all assignments that have been released to the
        exchange directory. If the course id is blank, this returns an empty
        set.

        Returns
        -------
        assignments: set
            A set of assignment names

        """
        if self.exchange_is_functional:
            lister = ExchangeList(coursedir=self.coursedir, parent=self)
            released = set([x['assignment_id'] for x in lister.start()])
        else:
            released = set([])

        return released

    def get_submitted_students(self, assignment_id):
        """Get the ids of students that have submitted a given assignment
        (determined by whether or not a submission exists in the `submitted`
        directory).

        Arguments
        ---------
        assignment_id: string
            The name of the assignment. May be * to select for all assignments.

        Returns
        -------
        students: set
            A set of student ids

        """
        # get the names of all student submissions in the `submitted` directory
        filenames = glob.glob(self.coursedir.format_path(
            self.coursedir.submitted_directory,
            student_id='*',
            assignment_id=assignment_id))

        students = set([])
        for filename in filenames:
            # skip files that aren't directories
            if not os.path.isdir(filename):
                continue

            # parse out the student id
            if assignment_id == "*":
                assignment_id = ".*"
            regex = self.coursedir.format_path(
                self.coursedir.submitted_directory,
                student_id='(?P<student_id>.*)',
                assignment_id=assignment_id,
                escape=True)

            matches = re.match(regex, filename)
            if matches:
                students.add(matches.groupdict()['student_id'])

        return students

    def get_submitted_timestamp(self, assignment_id, student_id):
        """Gets the timestamp of a submitted assignment.

        Arguments
        ---------
        assignment_id: string
            The assignment name
        student_id: string
            The student id

        Returns
        -------
        timestamp: datetime.datetime or None
            The timestamp of the submission, or None if the timestamp does
            not exist

        """
        assignment_dir = os.path.abspath(self.coursedir.format_path(
            self.coursedir.submitted_directory,
            student_id,
            assignment_id))

        timestamp_pth = os.path.join(assignment_dir, 'timestamp.txt')
        if os.path.exists(timestamp_pth):
            with open(timestamp_pth, 'r') as fh:
                return parse_utc(fh.read().strip())

    def get_autograded_students(self, assignment_id):
        """Get the ids of students whose submission for a given assignment
        has been autograded. This is determined based on satisfying all of the
        following criteria:

        1. There is a directory present in the `autograded` directory.
        2. The submission is present in the database.
        3. The timestamp of the autograded submission is the same as the
           timestamp of the original submission (in the `submitted` directory).

        Returns
        -------
        students: set
            A set of student ids

        """
        # get all autograded submissions
        with self.gradebook as gb:
            ag_timestamps = dict(gb.db\
                .query(Student.id, SubmittedAssignment.timestamp)\
                .join(SubmittedAssignment)\
                .filter(SubmittedAssignment.name == assignment_id)\
                .all())
            ag_students = set(ag_timestamps.keys())

        students = set([])
        for student_id in ag_students:
            # skip files that aren't directories
            filename = self.coursedir.format_path(
                self.coursedir.autograded_directory,
                student_id=student_id,
                assignment_id=assignment_id)
            if not os.path.isdir(filename):
                continue

            # get the timestamps and check whether the submitted timestamp is
            # newer than the autograded timestamp
            submitted_timestamp = self.get_submitted_timestamp(assignment_id, student_id)
            autograded_timestamp = ag_timestamps[student_id]
            if submitted_timestamp != autograded_timestamp:
                continue

            students.add(student_id)

        return students

    def get_assignment(self, assignment_id, released=None):
        """Get information about an assignment given its name.

        Arguments
        ---------
        assignment_id: string
            The name of the assignment
        released: list
            (Optional) A set of names of released assignments, obtained via
            self.get_released_assignments().

        Returns
        -------
        assignment: dict
            A dictionary containing information about the assignment

        """
        # get the set of released assignments if not given
        if not released:
            released = self.get_released_assignments()

        # check whether there is a source version of the assignment
        sourcedir = os.path.abspath(self.coursedir.format_path(
            self.coursedir.source_directory,
            student_id='.',
            assignment_id=assignment_id))
        if not os.path.isdir(sourcedir):
            return

        # see if there is information about the assignment in the database
        try:
            with self.gradebook as gb:
                db_assignment = gb.find_assignment(assignment_id)
                assignment = db_assignment.to_dict()
                if db_assignment.duedate:
                    ts = as_timezone(db_assignment.duedate, self.timezone)
                    assignment["display_duedate"] = ts.strftime(self.timestamp_format)
                    assignment["duedate_notimezone"] = ts.replace(tzinfo=None).isoformat()
                else:
                    assignment["display_duedate"] = None
                    assignment["duedate_notimezone"] = None
                assignment["duedate_timezone"] = self.timezone
                assignment["average_score"] = gb.average_assignment_score(assignment_id)
                assignment["average_code_score"] = gb.average_assignment_code_score(assignment_id)
                assignment["average_written_score"] = gb.average_assignment_written_score(assignment_id)

        except MissingEntry:
            assignment = {
                "id": None,
                "name": assignment_id,
                "duedate": None,
                "display_duedate": None,
                "duedate_notimezone": None,
                "duedate_timezone": self.timezone,
                "average_score": 0,
                "average_code_score": 0,
                "average_written_score": 0,
                "max_score": 0,
                "max_code_score": 0,
                "max_written_score": 0
            }

        # get released status
        if not self.exchange_is_functional:
            assignment["releaseable"] = False
            assignment["status"] = "draft"
        else:
            assignment["releaseable"] = True
            if assignment_id in released:
                assignment["status"] = "released"
            else:
                assignment["status"] = "draft"

        # get source directory
        assignment["source_path"] = os.path.relpath(sourcedir, self.coursedir.root)

        # get release directory
        releasedir = os.path.abspath(self.coursedir.format_path(
            self.coursedir.release_directory,
            student_id='.',
            assignment_id=assignment_id))
        if os.path.exists(releasedir):
            assignment["release_path"] = os.path.relpath(releasedir, self.coursedir.root)
        else:
            assignment["release_path"] = None

        # number of submissions
        assignment["num_submissions"] = len(self.get_submitted_students(assignment_id))

        return assignment

    def get_assignments(self):
        """Get a list of information about all assignments.

        Returns
        -------
        assignments: list
            A list of dictionaries containing information about each assignment

        """
        released = self.get_released_assignments()

        assignments = []
        for x in self.get_source_assignments():
            assignments.append(self.get_assignment(x, released=released))

        assignments.sort(key=lambda x: (x["duedate"] if x["duedate"] is not None else "None", x["name"]))
        return assignments

    def get_notebooks(self, assignment_id):
        """Get a list of notebooks in an assignment.

        Arguments
        ---------
        assignment_id: string
            The name of the assignment

        Returns
        -------
        notebooks: list
            A list of dictionaries containing information about each notebook

        """
        with self.gradebook as gb:
            try:
                assignment = gb.find_assignment(assignment_id)
            except MissingEntry:
                assignment = None

            # if the assignment exists in the database
            if assignment and assignment.notebooks:
                notebooks = []
                for notebook in assignment.notebooks:
                    x = notebook.to_dict()
                    x["average_score"] = gb.average_notebook_score(notebook.name, assignment.name)
                    x["average_code_score"] = gb.average_notebook_code_score(notebook.name, assignment.name)
                    x["average_written_score"] = gb.average_notebook_written_score(notebook.name, assignment.name)
                    notebooks.append(x)

            # if it doesn't exist in the database
            else:
                sourcedir = self.coursedir.format_path(
                    self.coursedir.source_directory,
                    student_id='.',
                    assignment_id=assignment_id)
                escaped_sourcedir = self.coursedir.format_path(
                    self.coursedir.source_directory,
                    student_id='.',
                    assignment_id=assignment_id,
                    escape=True)

                notebooks = []
                for filename in glob.glob(os.path.join(sourcedir, "*.ipynb")):
                    regex = re.escape(os.path.sep).join([escaped_sourcedir, "(?P<notebook_id>.*).ipynb"])
                    matches = re.match(regex, filename)
                    notebook_id = matches.groupdict()['notebook_id']
                    notebooks.append({
                        "name": notebook_id,
                        "id": None,
                        "average_score": 0,
                        "average_code_score": 0,
                        "average_written_score": 0,
                        "max_score": 0,
                        "max_code_score": 0,
                        "max_written_score": 0,
                        "needs_manual_grade": False,
                        "num_submissions": 0
                    })

        return notebooks

    def get_submission(self, assignment_id, student_id, ungraded=None, students=None):
        """Get information about a student's submission of an assignment.

        Arguments
        ---------
        assignment_id: string
            The name of the assignment
        student_id: string
            The student's id
        ungraded: set
            (Optional) A set of student ids corresponding to students whose
            submissions have not yet been autograded.
        students: dict
            (Optional) A dictionary of dictionaries, keyed by student id,
            containing information about students.

        Returns
        -------
        submission: dict
            A dictionary containing information about the submission

        """
        if ungraded is None:
            autograded = self.get_autograded_students(assignment_id)
            ungraded = self.get_submitted_students(assignment_id) - autograded
        if students is None:
            students = {x['id']: x for x in self.get_students()}

        if student_id in ungraded:
            ts = self.get_submitted_timestamp(assignment_id, student_id)
            if ts:
                timestamp = ts.isoformat()
                display_timestamp = as_timezone(ts, self.timezone).strftime(self.timestamp_format)
            else:
                timestamp = None
                display_timestamp = None

            submission = {
                "id": None,
                "name": assignment_id,
                "timestamp": timestamp,
                "display_timestamp": display_timestamp,
                "score": 0.0,
                "max_score": 0.0,
                "code_score": 0.0,
                "max_code_score": 0.0,
                "written_score": 0.0,
                "max_written_score": 0.0,
                "needs_manual_grade": False,
                "autograded": False,
                "submitted": True,
                "student": student_id,
            }

            if student_id not in students:
                submission["last_name"] = None
                submission["first_name"] = None
            else:
                submission["last_name"] = students[student_id]["last_name"]
                submission["first_name"] = students[student_id]["first_name"]

        elif student_id in autograded:
            with self.gradebook as gb:
                try:
                    db_submission = gb.find_submission(assignment_id, student_id)
                    submission = db_submission.to_dict()
                    if db_submission.timestamp:
                        submission["display_timestamp"] = as_timezone(
                            db_submission.timestamp, self.timezone).strftime(self.timestamp_format)
                    else:
                        submission["display_timestamp"] = None

                except MissingEntry:
                    return None

            submission["autograded"] = True
            submission["submitted"] = True

        else:
            submission = {
                "id": None,
                "name": assignment_id,
                "timestamp": None,
                "display_timestamp": None,
                "score": 0.0,
                "max_score": 0.0,
                "code_score": 0.0,
                "max_code_score": 0.0,
                "written_score": 0.0,
                "max_written_score": 0.0,
                "needs_manual_grade": False,
                "autograded": False,
                "submitted": False,
                "student": student_id,
            }

            if student_id not in students:
                submission["last_name"] = None
                submission["first_name"] = None
            else:
                submission["last_name"] = students[student_id]["last_name"]
                submission["first_name"] = students[student_id]["first_name"]

        return submission

    def get_submissions(self, assignment_id):
        """Get a list of submissions of an assignment. Each submission
        corresponds to a student.

        Arguments
        ---------
        assignment_id: string
            The name of the assignment

        Returns
        -------
        notebooks: list
            A list of dictionaries containing information about each submission

        """
        with self.gradebook as gb:
            db_submissions = gb.submission_dicts(assignment_id)
        ungraded = self.get_submitted_students(assignment_id) - self.get_autograded_students(assignment_id)
        students = {x['id']: x for x in self.get_students()}
        submissions = []
        for submission in db_submissions:
            if submission["student"] in ungraded:
                continue
            ts = submission["timestamp"]
            if ts:
                submission["timestamp"] = ts.isoformat()
                submission["display_timestamp"] = as_timezone(
                    ts, self.timezone).strftime(self.timestamp_format)
            else:
                submission["timestamp"] = None
                submission["display_timestamp"] = None
            submission["autograded"] = True
            submission["submitted"] = True
            submissions.append(submission)

        for student_id in ungraded:
            submission = self.get_submission(
                assignment_id, student_id, ungraded=ungraded, students=students)
            submissions.append(submission)

        submissions.sort(key=lambda x: x["student"])
        return submissions

    def _filter_existing_notebooks(self, assignment_id, notebooks):
        """Filters a list of notebooks so that it only includes those notebooks
        which actually exist on disk.

        This functionality is necessary for cases where student delete or rename
        on or more notebooks in their assignment, but still submit the assignment.

        Arguments
        ---------
        assignment_id: string
            The name of the assignment
        notebooks: list
            List of :class:`~nbgrader.api.SubmittedNotebook` objects

        Returns
        -------
        submissions: list
            List of :class:`~nbgrader.api.SubmittedNotebook` objects

        """
        submissions = list()
        for nb in notebooks:
            filename = os.path.join(
                os.path.abspath(self.coursedir.format_path(
                    self.coursedir.autograded_directory,
                    student_id=nb.student.id,
                    assignment_id=assignment_id)),
                "{}.ipynb".format(nb.name))

            if os.path.exists(filename):
                submissions.append(nb)

        return sorted(submissions, key=lambda x: x.id)

    def get_notebook_submission_indices(self, assignment_id, notebook_id):
        """Get a dictionary mapping unique submission ids to indices of the
        submissions relative to the full list of submissions.

        Arguments
        ---------
        assignment_id: string
            The name of the assignment
        notebook_id: string
            The name of the notebook

        Returns
        -------
        indices: dict
            A dictionary mapping submission ids to the index of each submission

        """
        with self.gradebook as gb:
            notebooks = gb.notebook_submissions(notebook_id, assignment_id)
            submissions = self._filter_existing_notebooks(assignment_id, notebooks)
        return dict([(x.id, i) for i, x in enumerate(submissions)])

    def get_notebook_submissions(self, assignment_id, notebook_id):
        """Get a list of submissions for a particular notebook in an assignment.

        Arguments
        ---------
        assignment_id: string
            The name of the assignment
        notebook_id: string
            The name of the notebook

        Returns
        -------
        submissions: list
            A list of dictionaries containing information about each submission.

        """
        with self.gradebook as gb:
            try:
                gb.find_notebook(notebook_id, assignment_id)
            except MissingEntry:
                return []

            submissions = gb.notebook_submission_dicts(notebook_id, assignment_id)

        indices = self.get_notebook_submission_indices(assignment_id, notebook_id)
        for nb in submissions:
            nb['index'] = indices.get(nb['id'], None)

        submissions = [x for x in submissions if x['index'] is not None]
        submissions.sort(key=lambda x: x["id"])
        return submissions

    def get_student(self, student_id, submitted=None):
        """Get a dictionary containing information about the given student.

        Arguments
        ---------
        student_id: string
            The unique id of the student
        submitted: set
            (Optional) A set of unique ids of students who have submitted an assignment

        Returns
        -------
        student: dictionary
            A dictionary containing information about the student, or None if
            the student does not exist

        """
        if submitted is None:
            submitted = self.get_submitted_students("*")

        try:
            with self.gradebook as gb:
                student = gb.find_student(student_id).to_dict()

        except MissingEntry:
            if student_id in submitted:
                student = {
                    "id": student_id,
                    "last_name": None,
                    "first_name": None,
                    "email": None,
                    "score": 0.0,
                    "max_score": 0.0
                }

            else:
                return None

        return student

    def get_students(self):
        """Get a list containing information about all the students in class.

        Returns
        -------
        students: list
            A list of dictionaries containing information about all the students

        """
        with self.gradebook as gb:
            in_db = set([x.id for x in gb.students])
            students = gb.student_dicts()

        submitted = self.get_submitted_students("*")
        for student_id in (submitted - in_db):
            students.append({
                "id": student_id,
                "last_name": None,
                "first_name": None,
                "email": None,
                "score": 0.0,
                "max_score": 0.0
            })

        students.sort(key=lambda x: (x["last_name"] or "None", x["first_name"] or "None", x["id"]))
        return students

    def get_student_submissions(self, student_id):
        """Get information about all submissions from a particular student.

        Arguments
        ---------
        student_id: string
            The unique id of the student

        Returns
        -------
        submissions: list
            A list of dictionaries containing information about all the student's
            submissions

        """
        # return just an empty list if the student doesn't exist
        submissions = []
        for assignment_id in self.get_source_assignments():
            submission = self.get_submission(assignment_id, student_id)
            submissions.append(submission)

        submissions.sort(key=lambda x: x["name"])
        return submissions

    def get_student_notebook_submissions(self, student_id, assignment_id):
        """Gets information about all notebooks within a submitted assignment.

        Arguments
        ---------
        student_id: string
            The unique id of the student
        assignment_id: string
            The name of the assignment

        Returns
        -------
        submissions: list
            A list of dictionaries containing information about the submissions

        """
        with self.gradebook as gb:
            try:
                assignment = gb.find_submission(assignment_id, student_id)
                student = assignment.student
            except MissingEntry:
                return []

            submissions = []
            for notebook in assignment.notebooks:
                filename = os.path.join(
                    os.path.abspath(self.coursedir.format_path(
                        self.coursedir.autograded_directory,
                        student_id=student_id,
                        assignment_id=assignment_id)),
                    "{}.ipynb".format(notebook.name))

                if os.path.exists(filename):
                    submissions.append(notebook.to_dict())
                else:
                    submissions.append({
                        "id": None,
                        "name": notebook.name,
                        "student": student_id,
                        "last_name": student.last_name,
                        "first_name": student.first_name,
                        "score": 0,
                        "max_score": notebook.max_score,
                        "code_score": 0,
                        "max_code_score": notebook.max_code_score,
                        "written_score": 0,
                        "max_written_score": notebook.max_written_score,
                        "needs_manual_grade": False,
                        "failed_tests": False,
                        "flagged": False
                    })

        submissions.sort(key=lambda x: x["name"])
        return submissions

    def assign(self, assignment_id, force=True, create=True):
        """Run ``nbgrader assign`` for a particular assignment.

        Arguments
        ---------
        assignment_id: string
            The name of the assignment
        force: bool
            Whether to force creating the student version, even if it already
            exists.
        create: bool
            Whether to create the assignment in the database, if it doesn't
            already exist.

        Returns
        -------
        result: dict
            A dictionary with the following keys (error and log may or may not be present):

            - success (bool): whether or not the operation completed successfully
            - error (string): formatted traceback
            - log (string): captured log output

        """
        with temp_attrs(self.coursedir, assignment_id=assignment_id):
            app = Assign(coursedir=self.coursedir, parent=self)
            app.force = force
            app.create_assignment = create
            return capture_log(app)

    def unrelease(self, assignment_id):
        """Run ``nbgrader list --remove`` for a particular assignment.

        Arguments
        ---------
        assignment_id: string
            The name of the assignment

        Returns
        -------
        result: dict
            A dictionary with the following keys (error and log may or may not be present):

            - success (bool): whether or not the operation completed successfully
            - error (string): formatted traceback
            - log (string): captured log output

        """
        if sys.platform != 'win32':
            with temp_attrs(self.coursedir, assignment_id=assignment_id):
                app = ExchangeList(coursedir=self.coursedir, parent=self)
                app.remove = True
                return capture_log(app)

    def release(self, assignment_id):
        """Run ``nbgrader release`` for a particular assignment.

        Arguments
        ---------
        assignment_id: string
            The name of the assignment

        Returns
        -------
        result: dict
            A dictionary with the following keys (error and log may or may not be present):

            - success (bool): whether or not the operation completed successfully
            - error (string): formatted traceback
            - log (string): captured log output

        """
        if sys.platform != 'win32':
            with temp_attrs(self.coursedir, assignment_id=assignment_id):
                app = ExchangeRelease(coursedir=self.coursedir, parent=self)
                return capture_log(app)

    def collect(self, assignment_id, update=True):
        """Run ``nbgrader collect`` for a particular assignment.

        Arguments
        ---------
        assignment_id: string
            The name of the assignment
        update: bool
            Whether to update already-collected assignments with newer
            submissions, if they exist

        Returns
        -------
        result: dict
            A dictionary with the following keys (error and log may or may not be present):

            - success (bool): whether or not the operation completed successfully
            - error (string): formatted traceback
            - log (string): captured log output

        """
        if sys.platform != 'win32':
            with temp_attrs(self.coursedir, assignment_id=assignment_id):
                app = ExchangeCollect(coursedir=self.coursedir, parent=self)
                app.update = update
                return capture_log(app)

    def autograde(self, assignment_id, student_id, force=True, create=True):
        """Run ``nbgrader autograde`` for a particular assignment and student.

        Arguments
        ---------
        assignment_id: string
            The name of the assignment
        student_id: string
            The unique id of the student
        force: bool
            Whether to autograde the submission, even if it's already been
            autograded
        create: bool
            Whether to create students in the database if they don't already
            exist

        Returns
        -------
        result: dict
            A dictionary with the following keys (error and log may or may not be present):

            - success (bool): whether or not the operation completed successfully
            - error (string): formatted traceback
            - log (string): captured log output

        """
        with temp_attrs(self.coursedir, assignment_id=assignment_id, student_id=student_id):
            app = Autograde(coursedir=self.coursedir, parent=self)
            app.force = force
            app.create_student = create
            return capture_log(app)
