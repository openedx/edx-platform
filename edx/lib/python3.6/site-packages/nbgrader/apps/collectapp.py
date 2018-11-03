from traitlets import default

from .baseapp import NbGrader, nbgrader_aliases, nbgrader_flags
from ..exchange import Exchange, ExchangeCollect, ExchangeError


aliases = {}
aliases.update(nbgrader_aliases)
aliases.update({
    "timezone": "Exchange.timezone",
    "course": "Exchange.course_id",
})

flags = {}
flags.update(nbgrader_flags)
flags.update({
    'update': (
        {'ExchangeCollect' : {'update': True}},
        "Update existing submissions with ones that have newer timestamps."
    ),
})

class CollectApp(NbGrader):

    name = u'nbgrader-collect'
    description = u'Collect an assignment from the nbgrader exchange'

    aliases = aliases
    flags = flags

    examples = """
        Collect assignments students have submitted. For the usage of instructors.

        This command is run from the top-level nbgrader folder. Before running
        this command, you may want toset the unique `course_id` for the course.
        It must be unique for each instructor/course combination. To set it in
        the config file add a line to the `nbgrader_config.py` file:

            c.Exchange.course_id = 'phys101'

        To pass the `course_id` at the command line, add `--course=phys101` to any
        of the below commands.

        To collect `assignment1` for all students:

            nbgrader collect assignment1

        To collect `assignment1` for only `student1`:

            nbgrader collect --student=student1 assignment1

        Collected assignments will go into the `submitted` folder with the proper
        directory structure to start grading. All submissions are timestamped and
        students can turn an assignment in multiple times. The `collect` command
        will always get the most recent submission from each student, but it will
        never overwrite an existing submission unless you provide the `--update`
        flag:

            nbgrader collect --update assignment1
        """

    @default("classes")
    def _classes_default(self):
        classes = super(CollectApp, self)._classes_default()
        classes.extend([Exchange, ExchangeCollect])
        return classes

    def _load_config(self, cfg, **kwargs):
        if 'CollectApp' in cfg:
            self.log.warning(
                "Use ExchangeCollect in config, not CollectApp. Outdated config:\n%s",
                '\n'.join(
                    'CollectApp.{key} = {value!r}'.format(key=key, value=value)
                    for key, value in cfg.CollectApp.items()
                )
            )
            cfg.ExchangeCollect.merge(cfg.CollectApp)
            del cfg.CollectApp

        super(CollectApp, self)._load_config(cfg, **kwargs)

    def start(self):
        super(CollectApp, self).start()

        # set assignemnt and course
        if len(self.extra_args) == 1:
            self.coursedir.assignment_id = self.extra_args[0]
        elif len(self.extra_args) > 2:
            self.fail("Too many arguments")
        elif self.coursedir.assignment_id == "":
            self.fail("Must provide assignment name:\nnbgrader <command> ASSIGNMENT [ --course COURSE ]")

        collect = ExchangeCollect(coursedir=self.coursedir, parent=self)
        try:
            collect.start()
        except ExchangeError:
            self.fail("nbgrader collect failed")
