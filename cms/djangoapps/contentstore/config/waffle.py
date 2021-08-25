"""
This module contains various configuration settings via
waffle switches for the contentstore app.
"""


from edx_toggles.toggles import LegacyWaffleFlag, LegacyWaffleFlagNamespace, LegacyWaffleSwitchNamespace

from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag

# Namespace
WAFFLE_NAMESPACE = 'studio'

# Switches
# TODO: Replace with WaffleSwitch(). See waffle() docstring.
ENABLE_ACCESSIBILITY_POLICY_PAGE = 'enable_policy_page'


def waffle():
    """
    Deprecated: Returns the namespaced, cached, audited Waffle Switch class for Studio pages.

    IMPORTANT: Do NOT copy this pattern and do NOT use this to reference new switches.
      Instead, replace the string constant above with the actual switch instance.
      For example::

        ENABLE_ACCESSIBILITY_POLICY_PAGE = WaffleSwitch(f'{WAFFLE_NAMESPACE}.enable_policy_page')
    """
    return LegacyWaffleSwitchNamespace(name=WAFFLE_NAMESPACE, log_prefix='Studio: ')


def waffle_flags():
    """
    Deprecated: Returns the namespaced, cached, audited Waffle Flag class for Studio pages.

    IMPORTANT: Do NOT copy this pattern and do NOT use this to reference new flags.
      See waffle() docstring for more details.
    """
    return LegacyWaffleFlagNamespace(name=WAFFLE_NAMESPACE, log_prefix='Studio: ')


# TODO: After removing this flag, add a migration to remove waffle flag in a follow-up deployment.
ENABLE_CHECKLISTS_QUALITY = CourseWaffleFlag(  # lint-amnesty, pylint: disable=toggle-missing-annotation
    waffle_namespace=waffle_flags(),
    flag_name='enable_checklists_quality',
    module_name=__name__,
)

SHOW_REVIEW_RULES_FLAG = CourseWaffleFlag(  # lint-amnesty, pylint: disable=toggle-missing-annotation
    waffle_namespace=waffle_flags(),
    flag_name='show_review_rules',
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
REDIRECT_TO_LIBRARY_AUTHORING_MICROFRONTEND = LegacyWaffleFlag(
    waffle_namespace=waffle_flags(),
    flag_name='library_authoring_mfe',
    module_name=__name__,
)


# .. toggle_name: studio.custom_relative_dates
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to enable custom pacing input for Personalized Learner Schedule (PLS).
# ..    This flag guards an input in Studio for a self paced course, where the user can enter date offsets
# ..    for a subsection.
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2021-07-12
# .. toggle_target_removal_date: 2021-12-31
# .. toggle_warnings: Flag course_experience.relative_dates should also be active for relative dates functionalities to work.
# .. toggle_tickets: https://openedx.atlassian.net/browse/AA-844
CUSTOM_RELATIVE_DATES = CourseWaffleFlag(WAFFLE_NAMESPACE, 'custom_relative_dates', module_name=__name__,)
