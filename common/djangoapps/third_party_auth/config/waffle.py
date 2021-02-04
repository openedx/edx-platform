"""
Waffle flags and switches for third party auth .
"""


from edx_toggles.toggles import WaffleSwitch

WAFFLE_NAMESPACE = 'third_party_auth'

# .. toggle_name: third_party_auth.enable_multiple_sso_accounts_association_to_saml_user
# .. toggle_implementation: WaffleSwitch
# .. toggle_default: False
# .. toggle_description: If enabled than learner should not be prompted for their edX password arriving via SAML
#   and already linked to the enterprise customer linked to the same IdP."
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2021-01-29
# .. toggle_target_removal_date: 2021-04-31
# .. toggle_tickets: ENT-4034
ENABLE_MULTIPLE_SSO_ACCOUNTS_ASSOCIATION_TO_SAML_USER = WaffleSwitch(
    '{NAMESPACE}.enable_multiple_sso_accounts_association_to_saml_user'.format(NAMESPACE=WAFFLE_NAMESPACE),
    __name__
)
