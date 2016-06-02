"""
Django Template Context Processor for CMS Online Contextual Help
"""
import ConfigParser
from django.conf import settings

from util.help_context_processor import common_doc_url


# Open and parse the configuration file when the module is initialized
CONFIG_FILE = open(settings.REPO_ROOT / "docs" / "cms_config.ini")
CONFIG = ConfigParser.ConfigParser()
CONFIG.readfp(CONFIG_FILE)


def doc_url(request=None):  # pylint: disable=unused-argument
    """
    This function is added in the list of TEMPLATES 'context_processors' OPTION, which is a django setting for
    a tuple of callables that take a request object as their argument and return a dictionary of items
    to be merged into the RequestContext.

    This function returns a dict with get_online_help_info, making it directly available to all mako templates.

    Args:
        request: Currently not used, but is passed by django to context processors.
            May be used in the future for determining the language of choice.
    """
    return common_doc_url(request, CONFIG)
