import os
import re

from textwrap import dedent

from traitlets.config import LoggingConfigurable
from traitlets import Unicode, List, default

from .utils import full_split, parse_utc


class CourseDirectory(LoggingConfigurable):

    student_id = Unicode(
        "*",
        help=dedent(
            """
            File glob to match student IDs. This can be changed to filter by
            student. Note: this is always changed to '.' when running `nbgrader
            assign`, as the assign step doesn't have any student ID associated
            with it.

            If the ID is purely numeric and you are passing it as a flag on the
            command line, you will need to escape the quotes in order to have
            it detected as a string, for example `--student="\"12345\""`. See:

                https://github.com/jupyter/nbgrader/issues/743

            for more details.
            """
        )
    ).tag(config=True)

    assignment_id = Unicode(
        "",
        help=dedent(
            """
            The assignment name. This MUST be specified, either by setting the
            config option, passing an argument on the command line, or using the
            --assignment option on the command line.
            """
        )
    ).tag(config=True)

    notebook_id = Unicode(
        "*",
        help=dedent(
            """
            File glob to match notebook names, excluding the '.ipynb' extension.
            This can be changed to filter by notebook.
            """
        )
    ).tag(config=True)

    directory_structure = Unicode(
        os.path.join("{nbgrader_step}", "{student_id}", "{assignment_id}"),
        help=dedent(
            """
            Format string for the directory structure that nbgrader works
            over during the grading process. This MUST contain named keys for
            'nbgrader_step', 'student_id', and 'assignment_id'. It SHOULD NOT
            contain a key for 'notebook_id', as this will be automatically joined
            with the rest of the path.
            """
        )
    ).tag(config=True)

    source_directory = Unicode(
        'source',
        help=dedent(
            """
            The name of the directory that contains the master/instructor
            version of assignments. This corresponds to the `nbgrader_step`
            variable in the `directory_structure` config option.
            """
        )
    ).tag(config=True)

    release_directory = Unicode(
        'release',
        help=dedent(
            """
            The name of the directory that contains the version of the
            assignment that will be released to students. This corresponds to
            the `nbgrader_step` variable in the `directory_structure` config
            option.
            """
        )
    ).tag(config=True)

    submitted_directory = Unicode(
        'submitted',
        help=dedent(
            """
            The name of the directory that contains assignments that have been
            submitted by students for grading. This corresponds to the
            `nbgrader_step` variable in the `directory_structure` config option.
            """
        )
    ).tag(config=True)

    autograded_directory = Unicode(
        'autograded',
        help=dedent(
            """
            The name of the directory that contains assignment submissions after
            they have been autograded. This corresponds to the `nbgrader_step`
            variable in the `directory_structure` config option.
            """
        )
    ).tag(config=True)

    feedback_directory = Unicode(
        'feedback',
        help=dedent(
            """
            The name of the directory that contains assignment feedback after
            grading has been completed. This corresponds to the `nbgrader_step`
            variable in the `directory_structure` config option.
            """
        )
    ).tag(config=True)

    db_url = Unicode(
        "",
        help=dedent(
            """
            URL to the database. Defaults to sqlite:///<root>/gradebook.db,
            where <root> is another configurable variable.
            """
        )
    ).tag(config=True)

    @default("db_url")
    def _db_url_default(self):
        return "sqlite:///{}".format(
            os.path.abspath(os.path.join(self.root, "gradebook.db")))

    db_assignments = List(
        help=dedent(
            """
            A list of assignments that will be created in the database. Each
            item in the list should be a dictionary with the following keys:

                - name
                - duedate (optional)

            The values will be stored in the database. Please see the API
            documentation on the `Assignment` database model for details on
            these fields.
            """
        )
    ).tag(config=True)

    db_students = List(
        help=dedent(
            """
            A list of student that will be created in the database. Each
            item in the list should be a dictionary with the following keys:

                - id
                - first_name (optional)
                - last_name (optional)
                - email (optional)

            The values will be stored in the database. Please see the API
            documentation on the `Student` database model for details on
            these fields.
            """
        )
    ).tag(config=True)

    root = Unicode(
        '',
        help=dedent(
            """
            The root directory for the course files (that includes the `source`,
            `release`, `submitted`, `autograded`, etc. directories). Defaults to
            the current working directory.
            """
        )
    ).tag(config=True)

    @default("root")
    def _root_default(self):
        return os.getcwd()

    ignore = List(
        [
            ".ipynb_checkpoints",
            "*.pyc",
            "__pycache__"
        ],
        help=dedent(
            """
            List of file names or file globs to be ignored when copying directories.
            """
        )
    ).tag(config=True)

    def format_path(self, nbgrader_step, student_id, assignment_id, escape=False):
        kwargs = dict(
            nbgrader_step=nbgrader_step,
            student_id=student_id,
            assignment_id=assignment_id
        )

        if escape:
            base = re.escape(self.root)
            structure = [x.format(**kwargs) for x in full_split(self.directory_structure)]
            path = re.escape(os.path.sep).join([base] + structure)
        else:
            path = os.path.join(self.root, self.directory_structure).format(**kwargs)

        return path

    def get_existing_timestamp(self, dest_path):
        """Get the timestamp, as a datetime object, of an existing submission."""
        timestamp_path = os.path.join(dest_path, 'timestamp.txt')
        if os.path.exists(timestamp_path):
            with open(timestamp_path, 'r') as fh:
                timestamp = fh.read().strip()
            if not timestamp:
                self.log.warning(
                    "Empty timestamp file: {}".format(timestamp_path))
                return None
            try:
                return parse_utc(timestamp)
            except ValueError:
                self.fail(
                    "Invalid timestamp string: {}".format(timestamp_path))
        else:
            return None
