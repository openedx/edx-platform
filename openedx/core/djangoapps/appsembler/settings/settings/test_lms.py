"""
Settings for Appsembler on test/LMS.
"""


def plugin_settings(settings):
    """
    Appsembler LMS overrides for testing environment.
    """
    settings.USE_S3_FOR_CUSTOMER_THEMES = False
