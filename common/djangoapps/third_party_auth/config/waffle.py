"""
Waffle flags and switches for third party auth .
"""


from edx_toggles.toggles import WaffleSwitch


WAFFLE_NAMESPACE = 'third_party_auth'

# .. toggle_name: ALWAYS_ASSOCIATE_USER_BY_EMAIL
# .. toggle_implementation: WaffleSwitch
# .. toggle_default: False
# .. toggle_description: Always associates current social auth user with
#   the user with the same email address in the database, which verifies
#   that only a single database user is associated with the email.
# .. toggle_use_cases: opt_in
# .. toggle_creation_date: 2020-12-23
# .. toggle_tickets: https://openedx.atlassian.net/browse/OSPR-5312
ALWAYS_ASSOCIATE_USER_BY_EMAIL = WaffleSwitch(
    WAFFLE_NAMESPACE,
    'always_associate_user_by_email',
    module_name=__name__,
)


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
    f'{WAFFLE_NAMESPACE}.enable_multiple_sso_accounts_association_to_saml_user',
    __name__
)
