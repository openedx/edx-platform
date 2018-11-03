from traitlets import default

from .baseapp import NbGrader, nbgrader_aliases, nbgrader_flags
from ..exchange import Exchange, ExchangeRelease, ExchangeError


aliases = {}
aliases.update(nbgrader_aliases)
aliases.update({
    "timezone": "Exchange.timezone",
    "course": "Exchange.course_id",
})

flags = {}
flags.update(nbgrader_flags)
flags.update({
    'force': (
        {'ExchangeRelease' : {'force' : True}},
        "Force overwrite of existing files in the exchange."
    ),
})

class ReleaseApp(NbGrader):

    name = u'nbgrader-release'
    description = u'Release an assignment to the nbgrader exchange'

    aliases = aliases
    flags = flags

    examples = """
        Release an assignment to students. For the usage of instructors.

        This command is run from the top-level nbgrader folder. Before running
        this command, there are two things you must do.

        First, you have to set the unique `course_id` for the course. It must be
        unique for each instructor/course combination. To set it in the config
        file add a line to the `nbgrader_config.py` file:

            c.Exchange.course_id = 'phys101'

        To pass the `course_id` at the command line, add `--course=phys101` to any
        of the below commands.

        Second, the assignment to be released must already be in the `release` folder.
        The usual way of getting an assignment into this folder is by running
        `nbgrader assign`.

        To release an assignment named `assignment1` run:

            nbgrader release assignment1

        If the assignment has already been released, you will have to add the
        `--force` flag to overwrite the released assignment:

            nbgrader release --force assignment1

        To query the exchange to see a list of your released assignments:

            nbgrader list
        """

    @default("classes")
    def _classes_default(self):
        classes = super(ReleaseApp, self)._classes_default()
        classes.extend([Exchange, ExchangeRelease])
        return classes

    def _load_config(self, cfg, **kwargs):
        if 'ReleaseApp' in cfg:
            self.log.warning(
                "Use ExchangeRelease in config, not ReleaseApp. Outdated config:\n%s",
                '\n'.join(
                    'ReleaseApp.{key} = {value!r}'.format(key=key, value=value)
                    for key, value in cfg.ReleaseApp.items()
                )
            )
            cfg.ExchangeRelease.merge(cfg.ReleaseApp)
            del cfg.ReleaseApp

        super(ReleaseApp, self)._load_config(cfg, **kwargs)

    def start(self):
        super(ReleaseApp, self).start()

        # set assignemnt and course
        if len(self.extra_args) == 1:
            self.coursedir.assignment_id = self.extra_args[0]
        elif len(self.extra_args) > 2:
            self.fail("Too many arguments")
        elif self.coursedir.assignment_id == "":
            self.fail("Must provide assignment name:\nnbgrader <command> ASSIGNMENT [ --course COURSE ]")

        release = ExchangeRelease(coursedir=self.coursedir, parent=self)
        try:
            release.start()
        except ExchangeError:
            self.fail("nbgrader release failed")
