"""
Appsembler-specific Waffle setup for Open edX Django apps.

Waffle namespaces, flags, that are for specific Appsembler Django apps
should go in those apps.  This module should be used for Flags and Switches
used to override, rollout, or modify changes to non-Appsembler apps.
"""

from openedx.core.djangoapps.waffle_utils import WaffleFlag, WaffleFlagNamespace

# Namespace
WAFFLE_NAMESPACE = u'appsembler'

# Flags
DISABLE_TPA_PIPELINE_SOCIALCORE_CREATE_USER_STEP = 'disable_tpa_pipeline_socialcore_create_user'


def waffle():
    """
    Returns the namespaced, cached, audited Waffle class for Appsembler.
    """
    return WaffleFlagNamespace(name=WAFFLE_NAMESPACE, log_prefix=u'Appsembler: ')


def waffle_flags():
    """
    Returns the namespaced, cached, audited Waffle flags dictionary for Appsembler.
    """
    namespace = waffle()
    return {
        DISABLE_TPA_PIPELINE_SOCIALCORE_CREATE_USER_STEP: WaffleFlag(
            namespace,
            DISABLE_TPA_PIPELINE_SOCIALCORE_CREATE_USER_STEP,
            flag_undefined_default=False,
        ),
    }


def disable_tpa_create_user_step(request):
    """
    Returns whether use of the create_user step in the third_party_auth pipeline is disabled or not.
    It does not appear to be necessary because the hidden registration form POSTs to /user_authn/
    endpoint to create a user prior this step.  The step adds complexity and may not be needed or
    even cause issues.  Using a Waffle Flag to be able to activate selectively for production
    testing.
    """
    return waffle().flag_is_active(
        request, waffle_flags()[DISABLE_TPA_PIPELINE_SOCIALCORE_CREATE_USER_STEP]
    )
