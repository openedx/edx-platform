"""
Common functionality for Django Template Context Processor for
Online Contextual Help.
"""

import ConfigParser
from django.conf import settings
import logging


log = logging.getLogger(__name__)


def common_doc_url(request, config_file_object):  # pylint: disable=unused-argument
    """
    This function is added in the list of TEMPLATES 'context_processors' OPTION, which is a django setting for
    a tuple of callables that take a request object as their argument and return a dictionary of items
    to be merged into the RequestContext.

    This function returns a dict with get_online_help_info, making it directly available to all mako templates.

    Args:
        request: Currently not used, but is passed by django to context processors.
            May be used in the future for determining the language of choice.
        config_file_object: Configuration file object.
    """

    def get_online_help_info(page_token=None, base_url=None):
        """
        Args:
            page_token: A string that identifies the page for which the help information is requested.
                It should correspond to an option in the docs/config_file_object.ini file.  If it doesn't, the "default"
                option is used instead.

            base_url: A string that identifies the base URL for the documentation link.  If not
                provided, defaults to the value in settings.DOC_LINK_BASE_URL or otherwise to the
                value of "url_base" in the config_file_object.

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
            if option:
                try:
                    return config_file_object.get(section_name, option)
                except (ConfigParser.NoOptionError, AttributeError):
                    log.debug("Didn't find a configuration option for '%s' section and '%s' option",
                              section_name, option)
            return config_file_object.get(section_name, default_option)

        def get_doc_url():
            """
            Returns:
                The URL for the documentation
            """

            # Read an optional configuration property that sets the base
            # URL of documentation links. By default, DOC_LINK_BASE_URL
            # is null, this test determines whether it is set to a non-null
            # value. If it is set, this function will use its string value
            # as the base of documentation link URLs. If it is not set, the
            # function reads the base of the documentation link URLs from
            # the .ini configuration file, lms_config.ini or cms_config.ini.
            if base_url:
                doc_base_url = base_url
            elif settings.DOC_LINK_BASE_URL:
                doc_base_url = settings.DOC_LINK_BASE_URL
            else:
                doc_base_url = config_file_object.get("help_settings", "url_base")

            # Construct and return the URL for the documentation link.
            return "{url_base}/{language}/{version}/{page_path}".format(
                url_base=doc_base_url,
                language=get_config_value_with_default("locales", settings.LANGUAGE_CODE),
                version=config_file_object.get("help_settings", "version"),
                page_path=get_config_value_with_default("pages", page_token),
            )

        def get_pdf_url():
            """
            Returns:
                The URL for the PDF document using the pdf_settings and the
                help_settings (version) in the configuration
            """

            # Read an optional configuration property that sets the base
            # URL of pdf links. By default, DOC_LINK_BASE_URL
            # is null, this test determines whether it is set to a non-null
            # value. If it is set, this function will use its string value
            # as the base of documentation link URLs. If it is not set, the
            # function reads the base of the documentation link URLs from
            # the .ini configuration file, lms_config.ini or cms_config.ini.
            if base_url:
                pdf_base_url = base_url
            elif settings.DOC_LINK_BASE_URL:
                pdf_base_url = settings.DOC_LINK_BASE_URL
            else:
                pdf_base_url = config_file_object.get("pdf_settings", "pdf_base")

            # Construct and return the URL for the PDF link.
            return "{pdf_base}/{version}/{pdf_file}".format(
                pdf_base=pdf_base_url,
                version=config_file_object.get("help_settings", "version"),
                pdf_file=config_file_object.get("pdf_settings", "pdf_file"),
            )

        return {
            "doc_url": get_doc_url(),
            "pdf_url": get_pdf_url(),
        }

    return {'get_online_help_info': get_online_help_info}
