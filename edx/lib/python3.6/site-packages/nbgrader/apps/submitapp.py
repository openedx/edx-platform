from traitlets import default

from .baseapp import NbGrader, nbgrader_aliases, nbgrader_flags
from ..exchange import Exchange, ExchangeSubmit, ExchangeError


aliases = {}
aliases.update(nbgrader_aliases)
aliases.update({
    "timezone": "Exchange.timezone",
    "course": "Exchange.course_id",
})

flags = {}
flags.update(nbgrader_flags)
flags.update({
    'strict': (
        {'ExchangeSubmit': {'strict': True}},
        "Fail if the submission is missing notebooks for the assignment"
    ),
})


class SubmitApp(NbGrader):

    name = u'nbgrader-submit'
    description = u'Submit an assignment to the nbgrader exchange'

    aliases = aliases
    flags = flags

    examples = """
        Submit an assignment for grading. For the usage of students.

        You must run this command from the directory containing the assignments
        sub-directory. For example, if you want to submit an assignment named
        `assignment1`, that must be a sub-directory of your current working directory.
        If you are inside the `assignment1` directory, it won't work.

        To fetch an assignment you must first know the `course_id` for your course.
        If you don't know it, ask your instructor.

        To submit `assignment1` to the course `phys101`:

            nbgrader submit assignment1 --course phys101

        You can submit an assignment multiple times and the instructor will always
        get the most recent version. Your assignment submission are timestamped
        so instructors can tell when you turned it in. No other students will
        be able to see your submissions.
        """

    @default("classes")
    def _classes_default(self):
        classes = super(SubmitApp, self)._classes_default()
        classes.extend([Exchange, ExchangeSubmit])
        return classes

    def _load_config(self, cfg, **kwargs):
        if 'SubmitApp' in cfg:
            self.log.warning(
                "Use ExchangeSubmit in config, not SubmitApp. Outdated config:\n%s",
                '\n'.join(
                    'SubmitApp.{key} = {value!r}'.format(key=key, value=value)
                    for key, value in cfg.SubmitApp.items()
                )
            )
            cfg.ExchangeSubmit.merge(cfg.SubmitApp)
            del cfg.SubmitApp

        super(SubmitApp, self)._load_config(cfg, **kwargs)

    def start(self):
        super(SubmitApp, self).start()

        # set assignemnt and course
        if len(self.extra_args) == 1:
            self.coursedir.assignment_id = self.extra_args[0]
        elif len(self.extra_args) > 2:
            self.fail("Too many arguments")
        elif self.coursedir.assignment_id == "":
            self.fail("Must provide assignment name:\nnbgrader <command> ASSIGNMENT [ --course COURSE ]")

        submit = ExchangeSubmit(coursedir=self.coursedir, parent=self)
        try:
            submit.start()
        except ExchangeError:
            self.fail("nbgrader submit failed")
