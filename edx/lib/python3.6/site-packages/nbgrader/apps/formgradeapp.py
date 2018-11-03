from traitlets.config.application import catch_config_error

from .baseapp import NbGrader, format_excepthook

_compat_message = """
The formgrader is no longer a standalone command, but is
rather an extension that is part of the Jupyter notebook. To run the
formgrader, make sure you have enabled the nbgrader server extensions:

http://nbgrader.readthedocs.io/en/stable/user_guide/installation.html#nbgrader-extensions

Then, run the notebook from the command line as normal:

    $ jupyter notebook

And click on the "Formgrader" tab in the window that opens.
"""


class FormgradeApp(NbGrader):

    name = u'nbgrader formgrade'
    description = u'Grade notebooks using a webapp'
    examples = ""

    @catch_config_error
    def initialize(self, argv=None):
        super(FormgradeApp, self).initialize(argv)

    def start(self):
        super(FormgradeApp, self).start()
        self.fail(_compat_message.strip())
