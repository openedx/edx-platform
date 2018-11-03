import sys

from traitlets import default

from .baseapp import NbGrader, nbgrader_aliases, nbgrader_flags
from ..converters import BaseConverter, Autograde, NbGraderException

aliases = {}
aliases.update(nbgrader_aliases)
aliases.update({
})

flags = {}
flags.update(nbgrader_flags)
flags.update({
    'create': (
        {'Autograde': {'create_student': True}},
        "Create an entry for the student in the database, if one does not already exist."
    ),
    'no-execute': (
        {
            'Execute': {'enabled': False},
            'ClearOutput': {'enabled': False}
        },
        "Don't execute notebooks and clear output when autograding."
    ),
    'force': (
        {'BaseConverter': {'force': True}},
        "Overwrite an assignment/submission if it already exists."
    ),
})


class AutogradeApp(NbGrader):

    name = u'nbgrader-autograde'
    description = u'Autograde a notebook by running it'

    aliases = aliases
    flags = flags

    examples = """
        Autograde submitted assignments. This takes one argument for the
        assignment id, and then (by default) autogrades assignments from the
        following directory structure:

            submitted/*/{assignment_id}/*.ipynb

        and saves the autograded files to the corresponding directory in:

            autograded/{student_id}/{assignment_id}/{notebook_id}.ipynb

        The student IDs must already exist in the database. If they do not, you
        can tell `nbgrader autograde` to add them on the fly by passing the
        --create flag.

        Note that the assignment must also be present in the database. If it is
        not, you should first create it using `nbgrader assign`. Then, during
        autograding, the cells that contain tests for the students' answers will
        be overwritten with the master version of the tests that is saved in the
        database (this prevents students from modifying the tests in order to
        improve their score).

        To grade all submissions for "Problem Set 1":

            nbgrader autograde "Problem Set 1"

        To grade only the submission by student with ID 'Hacker':

            nbgrader autograde "Problem Set 1" --student Hacker

        To grade only the notebooks that start with '1':

            nbgrader autograde "Problem Set 1" --notebook "1*"

        By default, student submissions are re-executed and their output cleared.
        For long running notebooks, it can be useful to disable this with the
        '--no-execute' flag:

            nbgrader autograde "Problem Set 1" --no-execute

        Note, however, that doing so will not guarantee that students' solutions
        are correct. If you use this flag, you should make sure you manually
        check all solutions. For example, if a student saved their notebook with
        all outputs cleared, then using --no-execute would result in them
        receiving full credit on all autograded problems.
        """

    @default("classes")
    def _classes_default(self):
        classes = super(AutogradeApp, self)._classes_default()
        classes.extend([BaseConverter, Autograde])
        return classes

    def _load_config(self, cfg, **kwargs):
        if 'AutogradeApp' in cfg:
            self.log.warning(
                "Use Autograde in config, not AutogradeApp. Outdated config:\n%s",
                '\n'.join(
                    'AutogradeApp.{key} = {value!r}'.format(key=key, value=value)
                    for key, value in cfg.AutogradeApp.items()
                )
            )
            cfg.Autograde.merge(cfg.AutogradeApp)
            del cfg.AutogradeApp

        super(AutogradeApp, self)._load_config(cfg, **kwargs)

    def start(self):
        super(AutogradeApp, self).start()

        if len(self.extra_args) > 1:
            self.fail("Only one argument (the assignment id) may be specified")
        elif len(self.extra_args) == 1 and self.coursedir.assignment_id != "":
            self.fail("The assignment cannot both be specified in config and as an argument")
        elif len(self.extra_args) == 0 and self.coursedir.assignment_id == "":
            self.fail("An assignment id must be specified, either as an argument or with --assignment")
        elif len(self.extra_args) == 1:
            self.coursedir.assignment_id = self.extra_args[0]

        converter = Autograde(coursedir=self.coursedir, parent=self)
        try:
            converter.start()
        except NbGraderException:
            sys.exit(1)

