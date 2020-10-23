"""
This module contains various configuration settings via
waffle switches for the contentstore app.
"""


from edx_toggles.toggles import WaffleFlag, WaffleFlagNamespace, WaffleSwitchNamespace
from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag

# Namespace
WAFFLE_NAMESPACE = u'studio'

# Switches
ENABLE_ACCESSIBILITY_POLICY_PAGE = u'enable_policy_page'


def waffle():
    """
    Returns the namespaced, cached, audited Waffle Switch class for Studio pages.
    """
    return WaffleSwitchNamespace(name=WAFFLE_NAMESPACE, log_prefix=u'Studio: ')


def waffle_flags():
    """
    Returns the namespaced, cached, audited Waffle Flag class for Studio pages.
    """
    return WaffleFlagNamespace(name=WAFFLE_NAMESPACE, log_prefix=u'Studio: ')


# TODO: After removing this flag, add a migration to remove waffle flag in a follow-up deployment.
ENABLE_CHECKLISTS_QUALITY = CourseWaffleFlag(
    waffle_namespace=waffle_flags(),
    flag_name=u'enable_checklists_quality',
    module_name=__name__,
)

SHOW_REVIEW_RULES_FLAG = CourseWaffleFlag(
    waffle_namespace=waffle_flags(),
    flag_name=u'show_review_rules',
    module_name=__name__,
)

# Waffle flag to redirect to the library authoring MFE.
# .. toggle_name: contentstore.library_authoring_mfe
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: Toggles the new micro-frontend-based implementation of the library authoring experience.
# .. toggle_use_cases: temporary, open_edx
# .. toggle_creation_date: 2020-08-03
# .. toggle_target_removal_date: 2020-12-31
# .. toggle_warnings: Also set settings.LIBRARY_AUTHORING_MICROFRONTEND_URL and ENABLE_LIBRARY_AUTHORING_MICROFRONTEND.
# .. toggle_tickets: https://openedx.atlassian.net/wiki/spaces/COMM/pages/1545011241/BD-14+Blockstore+Powered+Content+Libraries+Taxonomies
REDIRECT_TO_LIBRARY_AUTHORING_MICROFRONTEND = WaffleFlag(
    waffle_namespace=waffle_flags(),
    flag_name='library_authoring_mfe',
    module_name=__name__,
)
