
import ConfigParser
from django.conf import settings
import logging


log = logging.getLogger(__name__)


# Open and parse the configuration file when the module is initialized
config_file = open(settings.REPO_ROOT / "docs" / "config.ini")
config = ConfigParser.ConfigParser()
config.readfp(config_file)


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

    def get_online_help_info(page_token=None):
        """
        Args:
            page_token: A string that identifies the page for which the help information is requested.
                It should correspond to an option in the docs/config.ini file.  If it doesn't, the "default"
                option is used instead.

        Returns:
            A dict mapping the following items
                * "doc_url" - a string with the url corresponding to the online help location for the given page_token.
                * "pdf_url" - a string with the url corresponding to the location of the PDF help file.
        """

        def get_config_value_with_default(section_name, option, default_option="default"):
            """
            Args:
                section_name: name of the section in the configuration from which the option should be found
                option: name of the configuration option
                default_option: name of the default configuration option whose value should be returned if the
                    requested option is not found
            """
            try:
                return config.get(section_name, option)
            except (ConfigParser.NoOptionError, AttributeError):
                log.debug("Didn't find a configuration option for '%s' section and '%s' option", section_name, option)
                return config.get(section_name, default_option)

        def get_doc_url():
            """
            Returns:
                The URL for the documentation
            """
            return "{url_base}/{language}/{version}/{page_path}".format(
                url_base=config.get("help_settings", "url_base"),
                language=get_config_value_with_default("locales", settings.LANGUAGE_CODE),
                version=config.get("help_settings", "version"),
                page_path=get_config_value_with_default("pages", page_token),
            )

        def get_pdf_url():
            """
            Returns:
                The URL for the PDF document using the pdf_settings and the help_settings (version) in the configuration
            """
            return "{pdf_base}/{version}/{pdf_file}".format(
                pdf_base=config.get("pdf_settings", "pdf_base"),
                version=config.get("help_settings", "version"),
                pdf_file=config.get("pdf_settings", "pdf_file"),
            )

        return {
            "doc_url": get_doc_url(),
            "pdf_url": get_pdf_url(),
        }

    return {'get_online_help_info': get_online_help_info}
