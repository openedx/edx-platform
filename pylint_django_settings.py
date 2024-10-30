from pylint_django.checkers import ForeignKeyStringsChecker
from pylint_plugin_utils import get_checker


class ArgumentCompatibilityError(Exception):
    pass


def _get_django_settings_module(arguments):
    """
    Determines the appropriate Django settings module based on the pylint command-line arguments.
    It prevents the use of cms modules alongside lms or common modules.

    :param arguments: List of command-line arguments passed to pylint
    :return: A string representing the correct Django settings module ('cms.envs.test' or 'lms.envs.test')
    :raises ArgumentCompatibilityError: If both cms and lms/common modules are present
    """
    cms_module, lms_module, common_module = False, False, False

    for arg in arguments:
        if arg.startswith("cms"):
            cms_module = True
        elif arg.startswith("lms"):
            lms_module = True
        elif arg.startswith("common"):
            common_module = True

    if cms_module and (lms_module or common_module):
        # when cms module is present in pylint command, it can't be parired with (lms, common)
        # as common and lms gives error with cms test settings
        raise ArgumentCompatibilityError(
            "Modules from both common and lms cannot be paired with cms when running pylint"
        )

    # Return the appropriate Django settings module based on the arguments
    return "cms.envs.test" if cms_module else "lms.envs.test"


def register(linter):
    """
    Placeholder function to register the plugin with pylint.
    """
    pass


def load_configuration(linter):
    """
    Configures the Django settings module based on the command-line arguments passed to pylint.
    """
    name_checker = get_checker(linter, ForeignKeyStringsChecker)
    arguments = linter.cmdline_parser.parse_args()[1]
    name_checker.config.django_settings_module = _get_django_settings_module(arguments)
