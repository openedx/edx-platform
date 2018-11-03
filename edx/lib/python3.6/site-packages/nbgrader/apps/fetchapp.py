from traitlets import default

from .baseapp import NbGrader, nbgrader_aliases, nbgrader_flags
from ..exchange import Exchange, ExchangeFetch, ExchangeError


aliases = {}
aliases.update(nbgrader_aliases)
aliases.update({
    "timezone": "Exchange.timezone",
    "course": "Exchange.course_id",
})

flags = {}
flags.update(nbgrader_flags)
flags.update({
    'replace': (
        {'ExchangeFetch' : {'replace_missing_files' : True}},
        "replace missing files, even if the assignment has already been fetched"
    ),
})


class FetchApp(NbGrader):

    name = u'nbgrader-fetch'
    description = u'Fetch an assignment from the nbgrader exchange'

    aliases = aliases
    flags = flags

    examples = """
        Fetch an assignment that an instructor has released. For the usage of students.

        You can run this command from any directory, but usually, you will have a
        directory where you are keeping your course assignments.

        To fetch an assignment by name into the current directory:

            nbgrader fetch assignment1

        To fetch an assignment for a specific course, you must first know the
        `course_id` for your course.  If you don't know it, ask your instructor.
        Then, simply include the argument with the '--course' flag.

            nbgrader fetch assignment1 --course=phys101

        This will create an new directory named `assignment1` where you can work
        on the assignment. When you are done, use the `nbgrader submit` command
        to turn in the assignment.
        """

    @default("classes")
    def _classes_default(self):
        classes = super(FetchApp, self)._classes_default()
        classes.extend([Exchange, ExchangeFetch])
        return classes

    def _load_config(self, cfg, **kwargs):
        if 'FetchApp' in cfg:
            self.log.warning(
                "Use ExchangeFetch in config, not FetchApp. Outdated config:\n%s",
                '\n'.join(
                    'FetchApp.{key} = {value!r}'.format(key=key, value=value)
                    for key, value in cfg.FetchApp.items()
                )
            )
            cfg.ExchangeFetch.merge(cfg.FetchApp)
            del cfg.FetchApp

        super(FetchApp, self)._load_config(cfg, **kwargs)

    def start(self):
        super(FetchApp, self).start()

        # set assignemnt and course
        if len(self.extra_args) == 1:
            self.coursedir.assignment_id = self.extra_args[0]
        elif len(self.extra_args) > 2:
            self.fail("Too many arguments")
        elif self.coursedir.assignment_id == "":
            self.fail("Must provide assignment name:\nnbgrader <command> ASSIGNMENT [ --course COURSE ]")

        fetch = ExchangeFetch(coursedir=self.coursedir, parent=self)
        try:
            fetch.start()
        except ExchangeError:
            self.fail("nbgrader fetch failed")
