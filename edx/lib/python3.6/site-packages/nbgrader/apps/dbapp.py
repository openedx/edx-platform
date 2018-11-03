#!/usr/bin/env python
# encoding: utf-8

import csv
import os
import shutil

from textwrap import dedent
from traitlets import default, Unicode, Bool, List
from datetime import datetime

from . import NbGrader
from ..api import Gradebook, MissingEntry, Student, Assignment
from .. import dbutil

aliases = {
    'log-level': 'Application.log_level',
    'course-dir': 'CourseDirectory.root',
    'db': 'CourseDirectory.db_url'
}
flags = {}

student_add_aliases = {}
student_add_aliases.update(aliases)
student_add_aliases.update({
    'last-name': 'DbStudentAddApp.last_name',
    'first-name': 'DbStudentAddApp.first_name',
    'email': 'DbStudentAddApp.email'
})

class DbStudentAddApp(NbGrader):

    name = 'nbgrader-db-student-add'
    description = 'Add a student to the nbgrader database'

    aliases = student_add_aliases
    flags = flags

    last_name = Unicode(
        None,
        allow_none=True,
        help="The last name of the student"
    ).tag(config=True)

    first_name = Unicode(
        None,
        allow_none=True,
        help="The first name of the student"
    ).tag(config=True)

    email = Unicode(
        None,
        allow_none=True,
        help="The email of the student"
    ).tag(config=True)

    def start(self):
        super(DbStudentAddApp, self).start()

        if len(self.extra_args) != 1:
            self.fail("No student id provided.")

        student_id = self.extra_args[0]
        student = {
            "last_name": self.last_name,
            "first_name": self.first_name,
            "email": self.email
        }

        self.log.info("Creating/updating student with ID '%s': %s", student_id, student)
        with Gradebook(self.coursedir.db_url) as gb:
            gb.update_or_create_student(student_id, **student)

student_remove_flags = {}
student_remove_flags.update(flags)
student_remove_flags.update({
    'force': (
        {'DbStudentRemoveApp': {'force': True}},
        "Complete the operation, even if it means grades will be deleted."
    ),
})

class DbStudentRemoveApp(NbGrader):

    name = 'nbgrader-db-student-remove'
    description = 'Remove a student from the nbgrader database'

    aliases = aliases
    flags = student_remove_flags

    force = Bool(False, help="Confirm operation if it means grades will be deleted.").tag(config=True)

    def start(self):
        super(DbStudentRemoveApp, self).start()

        if len(self.extra_args) != 1:
            self.fail("No student id provided.")

        student_id = self.extra_args[0]

        with Gradebook(self.coursedir.db_url) as gb:
            try:
                student = gb.find_student(student_id)
            except MissingEntry:
                self.fail("No such student: '%s'", student_id)

            if len(student.submissions) > 0:
                if self.force:
                    self.log.warning("Removing associated grades")
                else:
                    self.log.warning("!!! There are grades in the database for student '%s'.", student_id)
                    self.log.warning("!!! Removing this student will also remove these grades.")
                    self.fail("!!! If you are SURE this is what you want to do, rerun with --force.")

            self.log.info("Removing student with ID '%s'", student_id)
            gb.remove_student(student_id)


class DbGenericImportApp(NbGrader):

    aliases = aliases
    flags = flags

    expected_keys = List(help="These are the keys expected by the database")

    def db_update_method_name(self):
        """
        Name of the update method used on the Gradebook for this import app.
        It is expected to have the signature:
            * instance_id : string, identifies which instance you are updating based on self.primary_key
            * instance : dictionary, contents for the update from the parsed csv rows; unpacked as kwargs
        """
        raise NotImplementedError

    name = ""
    description = ""


    @property
    def table_class(self):
        raise NotImplementedError

    @property
    def primary_key_default(self):
        """
        The key for the instance_id passed to the get_db_update_method.
        """
        raise NotImplementedError

    @default("expected_keys")
    def expected_keys_default(self):
        return self.table_class.__table__.c.keys()

    def start(self):
        super(DbGenericImportApp, self).start()

        if len(self.extra_args) != 1:
            self.fail("Path to CSV file not provided.")

        path = self.extra_args[0]
        if not os.path.exists(path):
            self.fail("No such file: '%s'", path)
        self.log.info("Importing from: '%s'", path)


        with Gradebook(self.coursedir.db_url) as gb:
            with open(path, 'r') as fh:
                reader = csv.DictReader(fh)
                reader.fieldnames = self._preprocess_keys(reader.fieldnames)
                for row in reader:
                    if self.primary_key not in row:
                        self.fail("Malformatted CSV file: must contain a column for '%s'" % self.primary_key)

                    # make sure all the keys are actually allowed in the database,
                    # and that any empty strings are parsed as None
                    instance = {}
                    for key, val in row.items():
                        if key not in self.expected_keys:
                            continue
                        if val == '':
                            instance[key] = None
                        else:
                            instance[key] = val
                    instance_primary_key = instance.pop(self.primary_key)


                    self.log.info("Creating/updating %s with %s '%s': %s",
                                  self.table_class.__name__,
                                  self.primary_key,
                                  instance_primary_key,
                                  instance)
                    db_update_method = getattr(gb, self.db_update_method_name)
                    db_update_method(instance_primary_key, **instance)


    def _preprocess_keys(self, keys):
        """
        Helper function for preprocessing keys
        """
        proposed_keys = [key.strip() for key in keys]
        unknown_keys = [k for k in proposed_keys if k not in self.expected_keys]
        if unknown_keys:
            self.log.info("Unknown keys in csv: '%s'",
                          (', '.join(unknown_keys[:-1])
                           + 'and '
                           + unknown_keys[-1]))
        return proposed_keys


class DbStudentImportApp(DbGenericImportApp):

    name = 'nbgrader-db-student-import'
    description = 'Import students into the nbgrader database from a CSV file'

    @property
    def table_class(self):
        return Student

    @property
    def primary_key(self):
        return "id"

    @property
    def db_update_method_name(self):
        return "update_or_create_student"


class DbStudentListApp(NbGrader):

    name = 'nbgrader-db-student-list'
    description = 'List students in the nbgrader database'

    aliases = aliases
    flags = flags

    def start(self):
        super(DbStudentListApp, self).start()

        with Gradebook(self.coursedir.db_url) as gb:
            print("There are %d students in the database:" % len(gb.students))
            for student in gb.students:
                print("%s (%s, %s) -- %s" % (student.id, student.last_name, student.first_name, student.email))


assignment_add_aliases = {}
assignment_add_aliases.update(aliases)
assignment_add_aliases.update({
    'duedate': 'DbAssignmentAddApp.duedate',
})

class DbAssignmentAddApp(NbGrader):

    name = 'nbgrader-db-assignment-add'
    description = 'Add an assignment to the nbgrader database'

    aliases = assignment_add_aliases
    flags = flags

    duedate = Unicode(
        None,
        allow_none=True,
        help="The due date of the assignment"
    ).tag(config=True)

    def start(self):
        super(DbAssignmentAddApp, self).start()

        if len(self.extra_args) != 1:
            self.fail("No assignment id provided.")

        assignment_id = self.extra_args[0]
        assignment = {
            "duedate": self.duedate
        }

        self.log.info("Creating/updating assignment with ID '%s': %s", assignment_id, assignment)
        with Gradebook(self.coursedir.db_url) as gb:
            gb.update_or_create_assignment(assignment_id, **assignment)


assignment_remove_flags = {}
assignment_remove_flags.update(flags)
assignment_remove_flags.update({
    'force': (
        {'DbAssignmentRemoveApp': {'force': True}},
        "Complete the operation, even if it means grades will be deleted."
    ),
})

class DbAssignmentRemoveApp(NbGrader):

    name = 'nbgrader-db-assignment-remove'
    description = 'Remove an assignment from the nbgrader database'

    aliases = aliases
    flags = assignment_remove_flags

    force = Bool(False, help="Confirm operation if it means grades will be deleted.").tag(config=True)

    def start(self):
        super(DbAssignmentRemoveApp, self).start()

        if len(self.extra_args) != 1:
            self.fail("No assignment id provided.")

        assignment_id = self.extra_args[0]

        with Gradebook(self.coursedir.db_url) as gb:
            try:
                assignment = gb.find_assignment(assignment_id)
            except MissingEntry:
                self.fail("No such assignment: '%s'", assignment_id)

            if len(assignment.submissions) > 0:
                if self.force:
                    self.log.warning("Removing associated grades")
                else:
                    self.log.warning("!!! There are grades in the database for assignment '%s'.", assignment_id)
                    self.log.warning("!!! Removing this assignment will also remove these grades.")
                    self.fail("!!! If you are SURE this is what you want to do, rerun with --force.")

            self.log.info("Removing assignment with ID '%s'", assignment_id)
            gb.remove_assignment(assignment_id)


class DbAssignmentImportApp(DbGenericImportApp):

    name = 'nbgrader-db-assignment-import'
    description = 'Import assignments into the nbgrader database from a CSV file'

    @property
    def table_class(self):
        return Assignment

    @property
    def primary_key(self):
        return "name"

    @property
    def db_update_method_name(self):
        return "update_or_create_assignment"

class DbAssignmentListApp(NbGrader):

    name = 'nbgrader-db-assignment-list'
    description = 'List assignments int the nbgrader database'

    aliases = aliases
    flags = flags

    def start(self):
        super(DbAssignmentListApp, self).start()

        with Gradebook(self.coursedir.db_url) as gb:
            print("There are %d assignments in the database:" % len(gb.assignments))
            for assignment in gb.assignments:
                print("%s (due: %s)" % (assignment.name, assignment.duedate))
                for notebook in assignment.notebooks:
                    print("    - %s" % notebook.name)


class DbStudentApp(NbGrader):

    name = 'nbgrader-db-student'
    description = u'Modify or list students in the nbgrader database'

    subcommands = {
        "add": (DbStudentAddApp, "Add a student to the database"),
        "remove": (DbStudentRemoveApp, "Remove a student from the database"),
        "list": (DbStudentListApp, "List students in the database"),
        "import": (DbStudentImportApp, "Import students into the database from a file")
    }

    @default("classes")
    def _classes_default(self):
        classes = super(DbStudentApp, self)._classes_default()

        # include all the apps that have configurable options
        for _, (app, _) in self.subcommands.items():
            if len(app.class_traits(config=True)) > 0:
                classes.append(app)

        return classes

    def start(self):
        # check: is there a subapp given?
        if self.subapp is None:
            print("No db command given (run with --help for options). List of subcommands:\n")
            self.print_subcommands()

        # This starts subapps
        super(DbStudentApp, self).start()


class DbAssignmentApp(NbGrader):

    name = 'nbgrader-db-assignment'
    description = u'Modify or list assignments in the nbgrader database'

    subcommands = {
        "add": (DbAssignmentAddApp, "Add an assignment to the database"),
        "remove": (DbAssignmentRemoveApp, "Remove an assignment from the database"),
        "list": (DbAssignmentListApp, "List assignments in the database"),
        "import": (DbAssignmentImportApp, "Import assignments into the database from a file")
    }

    @default("classes")
    def _classes_default(self):
        classes = super(DbAssignmentApp, self)._classes_default()

        # include all the apps that have configurable options
        for _, (app, _) in self.subcommands.items():
            if len(app.class_traits(config=True)) > 0:
                classes.append(app)

        return classes

    def start(self):
        # check: is there a subapp given?
        if self.subapp is None:
            print("No assignment command given. List of subcommands:\n")
            for key, (app, desc) in self.subcommands.items():
                print("    {}\n{}\n".format(key, desc))

        # This starts subapps
        super(DbAssignmentApp, self).start()


class DbUpgradeApp(NbGrader):
    """Based on the `jupyterhub upgrade-db` command found in jupyterhub.app.UpgradeDB"""

    name = 'nbgrader-db-upgrade'
    description = u'Upgrade the database schema to the latest version'

    def _backup_db_file(self, db_file):
        """Backup a database file"""
        if not os.path.exists(db_file):
            with Gradebook("sqlite:///{}".format(db_file)):
                pass

        timestamp = datetime.now().strftime('.%Y-%m-%d-%H%M%S.%f')
        backup_db_file = db_file + timestamp
        if os.path.exists(backup_db_file):
            self.fail("backup db file already exists: %s" % backup_db_file)

        self.log.info("Backing up %s => %s", db_file, backup_db_file)
        shutil.copy(db_file, backup_db_file)

    def start(self):
        super(DbUpgradeApp, self).start()
        if (self.coursedir.db_url.startswith('sqlite:///')):
            db_file = self.coursedir.db_url.split(':///', 1)[1]
            self._backup_db_file(db_file)
        self.log.info("Upgrading %s", self.coursedir.db_url)
        dbutil.upgrade(self.coursedir.db_url)


class DbApp(NbGrader):

    name = 'nbgrader-db'
    description = u'Perform operations on the nbgrader database'

    subcommands = dict(
        student=(
            DbStudentApp,
            dedent(
                """
                Add, remove, or list students in the nbgrader database.
                """
            ).strip()
        ),
        assignment=(
            DbAssignmentApp,
            dedent(
                """
                Add, remove, or list assignments in the nbgrader database.
                """
            ).strip()
        ),
        upgrade=(
            DbUpgradeApp,
            dedent(
                """
                Upgrade database schema to latest version.
                """
            ).strip()
        ),
    )

    @default("classes")
    def _classes_default(self):
        classes = super(DbApp, self)._classes_default()

        # include all the apps that have configurable options
        for _, (app, _) in self.subcommands.items():
            if len(app.class_traits(config=True)) > 0:
                classes.append(app)

        return classes

    def start(self):
        # check: is there a subapp given?
        if self.subapp is None:
            print("No db command given (run with --help for options). List of subcommands:\n")
            self.print_subcommands()

        # This starts subapps
        super(DbApp, self).start()
