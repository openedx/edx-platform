"""Third party authentication. """

from microsite_configuration import microsite


def is_enabled():
    """Check whether third party authentication has been enabled. """

    # We do this import internally to avoid initializing settings prematurely
    from django.conf import settings

    return microsite.get_value(
        "ENABLE_THIRD_PARTY_AUTH",
        settings.FEATURES.get("ENABLE_THIRD_PARTY_AUTH")
    )
