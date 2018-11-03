from traitlets.config.application import catch_config_error

from .baseapp import NbGrader, format_excepthook

_compat_message = """
The installation of the nbgrader extensions are now managed through the
`jupyter nbextension` and `jupyter serverextension` commands.

To install and enable the nbextensions (assignment_list and create_assignment) run:

    $ jupyter nbextension install --sys-prefix --py nbgrader
    $ jupyter nbextension enable --sys-prefix --py nbgrader
    
To install the server extension (assignment_list) run:

    $ jupyter serverextension enable --sys-prefix --py nbgrader

To install for all users, replace `--sys-prefix` by `--system`.
To install only for the current user replace `--sys-prefix` by `--user`.
"""

class ExtensionApp(NbGrader):

    name = u'nbgrader extension'
    description = u'Utilities for managing the nbgrader extension'
    examples = ""

    @catch_config_error
    def initialize(self, argv=None):
        super(ExtensionApp, self).initialize(argv)

    def start(self):
        for line in _compat_message.split('\n'):
            self.log.info(line)
        super(ExtensionApp, self).start()
