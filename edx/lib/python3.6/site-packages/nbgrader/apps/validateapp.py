import traceback
import glob

from traitlets import default

from .baseapp import NbGrader
from ..validator import Validator

aliases = {}
flags = {
    'invert': (
        {'Validator': {'invert': True}},
        "Complain when cells pass, rather than vice versa."
    )
}

class ValidateApp(NbGrader):

    name = u'nbgrader-validate'
    description = u'Validate a notebook by running it'

    aliases = aliases
    flags = flags

    examples = """
        You can run `nbgrader validate` on just a single file, e.g.:
            nbgrader validate "Problem 1.ipynb"

        Or, you can run it on multiple files using shell globs:
            nbgrader validate "Problem Set 1/*.ipynb"

        If you want to test instead that none of the tests pass (rather than that
        all of the tests pass, which is the default), you can use --invert:
            nbgrader validate --invert "Problem 1.ipynb"
        """

    @default("classes")
    def _classes_default(self):
        classes = super(ValidateApp, self)._classes_default()
        classes.append(Validator)
        return classes

    def _load_config(self, cfg, **kwargs):
        if 'DisplayAutoGrades' in cfg:
            self.log.warn(
                "Use Validator in config, not DisplayAutoGrades. Outdated config:\n%s",
                '\n'.join(
                    'DisplayAutoGrades.{key} = {value!r}'.format(key=key, value=value)
                    for key, value in cfg.DisplayAutoGrades.items()
                )
            )
            cfg.Validator.merge(cfg.DisplayAutoGrades)
            del cfg.DisplayAutoGrades

        super(ValidateApp, self)._load_config(cfg, **kwargs)

    def start(self):
        if not len(self.extra_args):
            self.fail("Must provide path to notebook:\nnbgrader validate NOTEBOOK")
        else:
            notebook_filenames = []
            for x in self.extra_args:
                notebook_filenames.extend(glob.glob(x))

        validator = Validator(parent=self)
        for filename in notebook_filenames:
            try:
                validator.validate_and_print(filename)
            except Exception:
                self.log.error(traceback.format_exc())
                self.fail("nbgrader encountered a fatal error while trying to validate '{}'".format(filename))
