"""
Toggles for the Agreements app
"""

from edx_toggles.toggles import WaffleFlag

# .. toggle_name: agreements.enable_integrity_signature
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: Supports rollout of the integrity signature feature
# .. toggle_use_cases: temporary, open_edx
# .. toggle_creation_date: 2021-05-07
# .. toggle_target_removal_date: None
# .. toggle_warnings: None
# .. toggle_tickets: MST-786

ENABLE_INTEGRITY_SIGNATURE = WaffleFlag('agreements.enable_integrity_signature', __name__)


def is_integrity_signature_enabled():
    return ENABLE_INTEGRITY_SIGNATURE.is_enabled()
