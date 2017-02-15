"""
Common Functions to Validate Configurations
"""


def validate_lms_config(settings):
    """
    Validates configurations for lms and raise ValueError if not valid
    """
    validate_common_config(settings)

    # validate feature based configurations
    validate_marketing_site_config(settings)


def validate_cms_config(settings):
    """
    Validates configurations for lms and raise ValueError if not valid
    """
    validate_common_config(settings)

    # validate feature based configurations
    validate_marketing_site_config(settings)


def validate_common_config(settings):
    """
    Validates configurations common for all apps
    """
    if not getattr(settings, 'LMS_ROOT_URL', None):
        raise ValueError("'LMS_ROOT_URL' is not defined.")


def validate_marketing_site_config(settings):
    """
    Validates 'marketing site' related configurations
    """
    if settings.FEATURES.get('ENABLE_MKTG_SITE'):
        if not hasattr(settings, 'MKTG_URLS'):
            raise ValueError("'ENABLE_MKTG_SITE' is True, but 'MKTG_URLS' is not defined.")
        if not settings.MKTG_URLS.get('ROOT'):
            raise ValueError("There is no 'ROOT' defined in 'MKTG_URLS'.")
