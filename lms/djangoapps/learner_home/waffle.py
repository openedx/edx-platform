"""
Configuration for features of Learner Home
"""
from django.conf import settings

from edx_toggles.toggles import WaffleFlag

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

# Namespace for Learner Home MFE waffle flags.
WAFFLE_FLAG_NAMESPACE = "learner_home_mfe"

# .. toggle_name: learner_home_mfe.enabled
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to enable to redirect user to learner home mfe
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2022-10-11
# .. toggle_tickets: AU-879
ENABLE_LEARNER_HOME_MFE = WaffleFlag(
    f"{WAFFLE_FLAG_NAMESPACE}.enabled",
    __name__,
)


def should_redirect_to_learner_home_mfe(user):
    """
    Redirect a percentage of learners to Learner Home for experimentation.

    Percentage is based on the LEARNER_HOME_MFE_REDIRECT_PERCENTAGE setting.
    """

    is_learning_mfe_enabled = configuration_helpers.get_value(
        "ENABLE_LEARNER_HOME_MFE", ENABLE_LEARNER_HOME_MFE.is_enabled()
    )

    learning_mfe_redirect_percent = configuration_helpers.get_value(
        "LEARNER_HOME_MFE_REDIRECT_PERCENTAGE",
        settings.LEARNER_HOME_MFE_REDIRECT_PERCENTAGE,
    )

    # Redirect when 1) Learner Home MFE is enabled and 2) a user falls into the
    # target range for experimental rollout.
    if is_learning_mfe_enabled and user.id % 100 < learning_mfe_redirect_percent:
        return True

    return False
