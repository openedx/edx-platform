"""
Togglable settings for Third Party Auth
"""

from edx_toggles.toggles import WaffleFlag, SettingToggle

THIRD_PARTY_AUTH_NAMESPACE = 'thirdpartyauth'

# .. toggle_name: third_party_auth.apple_user_migration
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: Enable User ID matching while apple migration is in process
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2023-02-27
# .. toggle_target_removal_date: 2023-05-01
# .. toggle_tickets: LEARNER-8790
# .. toggle_warning: None.
APPLE_USER_MIGRATION_FLAG = WaffleFlag(f'{THIRD_PARTY_AUTH_NAMESPACE}.apple_user_migration', __name__)


# .. toggle_name: ENABLE_SAML_CONFIG_SIGNAL_HANDLERS
# .. toggle_implementation: SettingToggle
# .. toggle_default: False
# .. toggle_description: Controls whether SAML configuration signal handlers are active.
#    When enabled (True), signal handlers will automatically update SAMLProviderConfig
#    references when the associated SAMLConfiguration is updated.
#    When disabled (False), SAMLProviderConfigs
#    point to outdated SAMLConfiguration.
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2025-07-03
# .. toggle_target_removal_date: 2026-01-01
# .. toggle_warning: Disabling this toggle may result in SAMLProviderConfig instances
#    pointing to outdated SAMLConfiguration records. Use the management command
#    'saml --fix-references' to fix outdated references.
ENABLE_SAML_CONFIG_SIGNAL_HANDLERS = SettingToggle(
    "ENABLE_SAML_CONFIG_SIGNAL_HANDLERS",
    default=True,
    module_name=__name__
)


def is_apple_user_migration_enabled():
    """
    Returns a boolean if Apple users migration is in process.
    """
    return APPLE_USER_MIGRATION_FLAG.is_enabled()
