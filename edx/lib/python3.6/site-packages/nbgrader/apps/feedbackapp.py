import sys

from traitlets import default

from .baseapp import NbGrader, nbgrader_aliases, nbgrader_flags
from ..converters import BaseConverter, Feedback, NbGraderException

aliases = {}
aliases.update(nbgrader_aliases)
aliases.update({
})

flags = {}
flags.update(nbgrader_flags)
flags.update({
    'force': (
        {'BaseConverter': {'force': True}},
        "Overwrite an assignment/submission if it already exists."
    ),
})

class FeedbackApp(NbGrader):

    name = u'nbgrader-feedback'
    description = u'Generate feedback from a graded notebook'

    aliases = aliases
    flags = flags

    examples = """
        Create HTML feedback for students after all the grading is finished.
        This takes a single parameter, which is the assignment ID, and then (by
        default) looks at the following directory structure:

            autograded/*/{assignment_id}/*.ipynb

        from which it generates feedback the the corresponding directories
        according to:

            feedback/{student_id}/{assignment_id}/{notebook_id}.html

        Running `nbgrader feedback` requires that `nbgrader autograde` (and most
        likely `nbgrader formgrade`) have been run and that all grading is
        complete.

        To generate feedback for all submissions for "Problem Set 1":
            nbgrader feedback "Problem Set 1"

        To generate feedback only for the student with ID 'Hacker':
            nbgrader feedback "Problem Set 1" --student Hacker

        To feedback for only the notebooks that start with '1':
            nbgrader feedback "Problem Set 1" --notebook "1*"
        """

    @default("classes")
    def _classes_default(self):
        classes = super(FeedbackApp, self)._classes_default()
        classes.extend([BaseConverter, Feedback])
        return classes

    def _load_config(self, cfg, **kwargs):
        if 'FeedbackApp' in cfg:
            self.log.warning(
                "Use Feedback in config, not FeedbackApp. Outdated config:\n%s",
                '\n'.join(
                    'FeedbackApp.{key} = {value!r}'.format(key=key, value=value)
                    for key, value in cfg.FeedbackApp.items()
                )
            )
            cfg.Feedback.merge(cfg.FeedbackApp)
            del cfg.FeedbackApp

        super(FeedbackApp, self)._load_config(cfg, **kwargs)

    def start(self):
        super(FeedbackApp, self).start()

        if len(self.extra_args) > 1:
            self.fail("Only one argument (the assignment id) may be specified")
        elif len(self.extra_args) == 1 and self.coursedir.assignment_id != "":
            self.fail("The assignment cannot both be specified in config and as an argument")
        elif len(self.extra_args) == 0 and self.coursedir.assignment_id == "":
            self.fail("An assignment id must be specified, either as an argument or with --assignment")
        elif len(self.extra_args) == 1:
            self.coursedir.assignment_id = self.extra_args[0]

        converter = Feedback(coursedir=self.coursedir, parent=self)
        try:
            converter.start()
        except NbGraderException:
            sys.exit(1)
