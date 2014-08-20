"""
Helper methods for credit card processing modules.
These methods should be shared among all processor implementations,
but should NOT be imported by modules outside this package.
"""
from django.conf import settings
from microsite_configuration import microsite


def get_processor_config():
    """
    Return a dictionary of configuration settings for the active credit card processor.
    If we're in a microsite and overrides are available, return those instead.

    Returns:
        dict

    """
    # Retrieve the configuration settings for the active credit card processor
    config = settings.CC_PROCESSOR.get(
        settings.CC_PROCESSOR_NAME, {}
    )

    # Check whether we're in a microsite that overrides our configuration
    # If so, find the microsite-specific configuration in the 'microsites'
    # sub-key of the normal processor configuration.
    config_key = microsite.get_value('cybersource_config_key')
    if config_key:
        config = config['microsites'][config_key]

    return config
