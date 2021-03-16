from pylint.interfaces import IAstroidChecker
from pylint.checkers import BaseChecker
from pylint_django.checkers import ForeignKeyStringsChecker
from pylint_plugin_utils import get_checker


class ArgumentCompatibilityError(Exception):
    pass


class SetDjangoSettingsChecker(BaseChecker):
    """
    This isn't a checker, but setting django settings module when pylint command is ran.
    This is to avoid 'django-not-configured' pylint warning

    """
    __implements__ = IAstroidChecker

    name = 'set-django-settings'

    msgs = {'R0991': ('bogus', 'bogus', 'bogus')}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def open(self):
        name_checker = get_checker(self.linter, ForeignKeyStringsChecker)
        # pylint command should not run with modules from both cms and (lms, common) at once
        cms_module = False
        lms_module = False
        common_module = False
        for arg in self.linter.cmdline_parser.largs:
            if arg.startswith('cms'):
                cms_module = True
            elif arg.startswith('lms'):
                lms_module = True
            elif arg.startswith('common'):
                common_module = True

        if cms_module and (lms_module or common_module):
            # when cms module is present in pylint command, it can't be parired with (lms, common)
            # as common and lms gives error with cms test settings
            raise ArgumentCompatibilityError(
                "Modules from both common and lms can't be paired with cms while running pylint"
            )
        elif cms_module:
            # If a module from cms is present in pylint command arguments
            # and ony other module from (openedx, pavelib) is present
            # than test setting of cms is used
            name_checker.config.django_settings_module = 'cms.envs.test'
        else:
            # If any module form (lms, common, openedx, pavelib) is present in
            # pylint command arguments than test setting of lms is used
            name_checker.config.django_settings_module = 'lms.envs.test'


def register(linter):
    linter.register_checker(SetDjangoSettingsChecker(linter))
