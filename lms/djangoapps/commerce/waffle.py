"""
Configuration for features of Commerce App
"""
from edx_toggles.toggles import WaffleFlag

# Namespace for Commerce waffle flags.
WAFFLE_FLAG_NAMESPACE = "commerce"

# .. toggle_name: commerce.transition_to_coordinator.checkout
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: Allows to redirect checkout to Commerce Coordinator API
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2023-11-22
# .. toggle_target_removal_date: TBA
# .. toggle_tickets: SONIC-99
# .. toggle_status: supported
ENABLE_TRANSITION_TO_COORDINATOR_CHECKOUT = WaffleFlag(
    f"{WAFFLE_FLAG_NAMESPACE}.transition_to_coordinator.checkout",
    __name__,
)


def should_redirect_to_commerce_coordinator_checkout():
    """
    Redirect learners to Commerce coordinator checkout.

    """
    return ENABLE_TRANSITION_TO_COORDINATOR_CHECKOUT.is_enabled()
