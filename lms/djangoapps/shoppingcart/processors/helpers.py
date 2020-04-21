"""
Helper methods for credit card processing modules.
These methods should be shared among all processor implementations,
but should NOT be imported by modules outside this package.
"""


from django.conf import settings

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers


def get_processor_config():
    """
    Return a dictionary of configuration settings for the active credit card processor.
    If configuration overrides are available, return those instead.

    Returns:
        dict

    """
    # Retrieve the configuration settings for the active credit card processor
    config = settings.CC_PROCESSOR.get(
        settings.CC_PROCESSOR_NAME, {}
    )
    return config
