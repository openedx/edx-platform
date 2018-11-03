from traitlets import default

from .baseapp import NbGrader, nbgrader_aliases, nbgrader_flags
from ..exchange import Exchange, ExchangeList, ExchangeError


aliases = {}
aliases.update(nbgrader_aliases)
aliases.update({
    "timezone": "Exchange.timezone",
    "course": "Exchange.course_id",
})

flags = {}
flags.update(nbgrader_flags)
flags.update({
    'inbound': (
        {'ExchangeList' : {'inbound': True}},
        "List inbound files rather than outbound."
    ),
    'cached': (
        {'ExchangeList' : {'cached': True}},
        "List cached files rather than inbound/outbound."
    ),
    'remove': (
        {'ExchangeList' : {'remove': True}},
        "Remove an assignment from the exchange."
    ),
    'json': (
        {'ExchangeList' : {'as_json': True}},
        "Print out assignments as json."
    ),
})

class ListApp(NbGrader):

    name = u'nbgrader-list'
    description = u'List assignments in the nbgrader exchange'

    aliases = aliases
    flags = flags

    examples = """
        List assignments in the nbgrader exchange. For the usage of instructors
        and students.

        Students
        ========

        To list assignments for a course, you must first know the `course_id` for
        your course. If you don't know it, ask your instructor.

        To list the released assignments for the course `phys101`:

            nbgrader list phys101

        Instructors
        ===========

        To list outbound (released) or inbound (submitted) assignments for a course,
        you must configure the `course_id` in your config file or the command line.

        To see all of the released assignments, run

            nbgrader list  # course_id in the config file

        or

            nbgrader list --course phys101  # course_id provided

        To see the inbound (submitted) assignments:

            nbgrader list --inbound

        You can use the `--student` and `--assignment` options to filter the list
        by student or assignment:

            nbgrader list --inbound --student=student1 --assignment=assignment1

        If a student has submitted an assignment multiple times, the `list` command
        will show all submissions with their timestamps.

        The `list` command can optionally remove listed assignments by providing the
        `--remove` flag:

            nbgrader list --inbound --remove --student=student1
        """

    @default("classes")
    def _classes_default(self):
        classes = super(ListApp, self)._classes_default()
        classes.extend([Exchange, ExchangeList])
        return classes

    def _load_config(self, cfg, **kwargs):
        if 'ListApp' in cfg:
            self.log.warning(
                "Use ExchangeList in config, not ListApp. Outdated config:\n%s",
                '\n'.join(
                    'ListApp.{key} = {value!r}'.format(key=key, value=value)
                    for key, value in cfg.ListApp.items()
                )
            )
            cfg.ExchangeList.merge(cfg.ListApp)
            del cfg.ListApp

        super(ListApp, self)._load_config(cfg, **kwargs)

    def start(self):
        super(ListApp, self).start()

        # set assignemnt and course
        if len(self.extra_args) == 1:
            self.coursedir.assignment_id = self.extra_args[0]
        elif len(self.extra_args) > 2:
            self.fail("Too many arguments")

        lister = ExchangeList(coursedir=self.coursedir, parent=self)
        try:
            lister.start()
        except ExchangeError:
            self.fail("nbgrader list failed")
