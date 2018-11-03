#!/usr/bin/env python
# encoding: utf-8

import sys
import os

from textwrap import dedent

from traitlets import default
from traitlets.config.application import catch_config_error
from jupyter_core.application import NoStart

import nbgrader
from .. import preprocessors
from .. import plugins
from ..coursedir import CourseDirectory
from .. import exchange
from .. import converters
from .baseapp import nbgrader_aliases, nbgrader_flags
from . import (
    NbGrader,
    AssignApp,
    AutogradeApp,
    FormgradeApp,
    FeedbackApp,
    ValidateApp,
    ReleaseApp,
    CollectApp,
    FetchApp,
    SubmitApp,
    ListApp,
    ExtensionApp,
    QuickStartApp,
    ExportApp,
    DbApp,
    UpdateApp,
    ZipCollectApp,
)

aliases = {}
aliases.update(nbgrader_aliases)
aliases.update({
})

flags = {}
flags.update(nbgrader_flags)
flags.update({
    'generate-config': (
        {'NbGraderApp' : {'generate_config': True}},
        "Generate a config file."
    )
})


class NbGraderApp(NbGrader):

    name = 'nbgrader'
    description = u'A system for assigning and grading notebooks'
    version = nbgrader.__version__

    aliases = aliases
    flags = flags

    examples = """
        The nbgrader application is a system for assigning and grading notebooks.
        Each subcommand of this program corresponds to a different step in the
        grading process. In order to facilitate the grading pipeline, nbgrader
        places some constraints on how the assignments must be structured. By
        default, the directory structure for the assignments must look like this:

            {nbgrader_step}/{student_id}/{assignment_id}/{notebook_id}.ipynb

        where 'nbgrader_step' is the step in the nbgrader pipeline, 'student_id'
        is the ID of the student, 'assignment_id' is the name of the assignment,
        and 'notebook_id' is the name of the notebook (excluding the extension).
        For example, when running `nbgrader autograde "Problem Set 1"`, the
        autograder will first look for all notebooks for all students in the
        following directories:

            submitted/*/Problem Set 1/*.ipynb

        and it will write the autograded notebooks to the corresponding directory
        and filename for each notebook and each student:

            autograded/{student_id}/Problem Set 1/{notebook_id}.ipynb

        These variables, as well as the overall directory structure, can be
        configured through the `NbGrader` class (run `nbgrader --help-all`
        to see these options).

        For more details on how each of the subcommands work, please see the help
        for that command (e.g. `nbgrader assign --help-all`).
        """

    subcommands = dict(
        assign=(
            AssignApp,
            dedent(
                """
                Create the student version of an assignment. Intended for use by
                instructors only.
                """
            ).strip()
        ),
        autograde=(
            AutogradeApp,
            dedent(
                """
                Autograde submitted assignments. Intended for use by instructors
                only.
                """
            ).strip()
        ),
        formgrade=(
            FormgradeApp,
            dedent(
                """
                Manually grade assignments (after autograding). Intended for use
                by instructors only.
                """
            ).strip()
        ),
        feedback=(
            FeedbackApp,
            dedent(
                """
                Generate feedback (after autograding and manual grading).
                Intended for use by instructors only.
                """
            ).strip()
        ),
        validate=(
            ValidateApp,
            dedent(
                """
                Validate a notebook in an assignment. Intended for use by
                instructors and students.
                """
            ).strip()
        ),
        release=(
            ReleaseApp,
            dedent(
                """
                Release an assignment to students through the nbgrader exchange.
                Intended for use by instructors only.
                """
            ).strip()
        ),
        collect=(
            CollectApp,
            dedent(
                """
                Collect an assignment from students through the nbgrader exchange.
                Intended for use by instructors only.
                """
            ).strip()
        ),
        zip_collect=(
            ZipCollectApp,
            dedent(
                """
                Collect assignment submissions from files and/or archives (zip
                files) manually downloaded from a LMS.
                Intended for use by instructors only.
                """
            ).strip()
        ),
        fetch=(
            FetchApp,
            dedent(
                """
                Fetch an assignment from an instructor through the nbgrader exchange.
                Intended for use by students only.
                """
            ).strip()
        ),
        submit=(
            SubmitApp,
            dedent(
                """
                Submit an assignment to an instructor through the nbgrader exchange.
                Intended for use by students only.
                """
            ).strip()
        ),
        list=(
            ListApp,
            dedent(
                """
                List inbound or outbound assignments in the nbgrader exchange.
                Intended for use by instructors and students.
                """
            ).strip()
        ),
        extension=(
            ExtensionApp,
            dedent(
                """
                Install and activate the "Create Assignment" notebook extension.
                """
            ).strip()
        ),
        quickstart=(
            QuickStartApp,
            dedent(
                """
                Create an example class files directory with an example
                config file and assignment.
                """
            ).strip()
        ),
        export=(
            ExportApp,
            dedent(
                """
                Export grades from the database to another format.
                """
            ).strip()
        ),
        db=(
            DbApp,
            dedent(
                """
                Perform operations on the nbgrader database, such as adding,
                removing, importing, and listing assignments or students.
                """
            ).strip()
        ),
        update=(
            UpdateApp,
            dedent(
                """
                Update nbgrader cell metadata to the most recent version.
                """
            ).strip()
        )
    )

    @default("classes")
    def _classes_default(self):
        classes = super(NbGraderApp, self)._classes_default()

        # include the coursedirectory
        classes.append(CourseDirectory)

        # include all the apps that have configurable options
        for _, (app, _) in self.subcommands.items():
            if len(app.class_traits(config=True)) > 0:
                classes.append(app)

        # include plugins that have configurable options
        for pg_name in plugins.__all__:
            pg = getattr(plugins, pg_name)
            if pg.class_traits(config=True):
                classes.append(pg)

        # include all preprocessors that have configurable options
        for pp_name in preprocessors.__all__:
            pp = getattr(preprocessors, pp_name)
            if len(pp.class_traits(config=True)) > 0:
                classes.append(pp)

        # include all the exchange actions
        for ex_name in exchange.__all__:
            ex = getattr(exchange, ex_name)
            if hasattr(ex, "class_traits") and ex.class_traits(config=True):
                classes.append(ex)

        # include all the converters
        for ex_name in converters.__all__:
            ex = getattr(converters, ex_name)
            if hasattr(ex, "class_traits") and ex.class_traits(config=True):
                classes.append(ex)

        return classes

    @catch_config_error
    def initialize(self, argv=None):
        super(NbGraderApp, self).initialize(argv)

    def start(self):
        # if we're generating a config file, then do only that
        if self.generate_config:
            s = self.generate_config_file()
            filename = "nbgrader_config.py"

            if os.path.exists(filename):
                self.fail("Config file '{}' already exists".format(filename))

            with open(filename, 'w') as fh:
                fh.write(s)
            self.log.info("New config file saved to '{}'".format(filename))
            raise NoStart()

        # check: is there a subapp given?
        if self.subapp is None:
            print("No command given (run with --help for options). List of subcommands:\n")
            self.print_subcommands()

        # This starts subapps
        super(NbGraderApp, self).start()

    def print_version(self):
        print("Python version {}".format(sys.version))
        print("nbgrader version {}".format(nbgrader.__version__))

def main():
    NbGraderApp.launch_instance()
