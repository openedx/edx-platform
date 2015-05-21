"""Context processors for Django templates. """
from branding import api as branding_api


# TODO (ECOM-1339): Remove this module once we permanently enable the V3 footer.
def branding_context_processor(request):  # pylint: disable=unused-argument
    """Add the feature flag to Django template context. """
    return {
        "ENABLE_BRANDING_API": branding_api.is_enabled()
    }
