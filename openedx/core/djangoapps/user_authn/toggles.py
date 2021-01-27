"""
Toggles for user_authn
"""


from django.conf import settings

# .. toggle_name: ENABLE_REQUIRE_THIRD_PARTY_AUTH
# .. toggle_implementation: DjangoSetting
# .. toggle_default: False
# .. toggle_description: Set to True to prevent using username/password login and registration and only allow authentication with third party auth
# .. toggle_category: admin
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2020-09-16
# .. toggle_expiration_date: None
# .. toggle_tickets: None
# .. toggle_status: supported
# .. toggle_warnings: Requires configuration of third party auth


def is_require_third_party_auth_enabled():
    # TODO: Replace function with SettingToggle when it is available.
    return getattr(settings, "ENABLE_REQUIRE_THIRD_PARTY_AUTH", False)
