"""
Toggles for Oauth Dispatch.
"""


from edx_toggles.toggles import WaffleSwitch

OAUTH_DISPATCH_WAFFLE_SWITCH_NAMESPACE = 'oauth_dispatch'

# .. toggle_name: DISABLE_JWT_FOR_MOBILE
# .. toggle_implementation: WaffleSwitch
# .. toggle_default: False
# .. toggle_description: Toggle to control creation of JWT token for mobile
#   field during development.
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2022-10-14
# .. toggle_target_removal_date: 2022-12-30
DISABLE_JWT_FOR_MOBILE = WaffleSwitch(
    f'{OAUTH_DISPATCH_WAFFLE_SWITCH_NAMESPACE}.disable_jwt_for_mobile',
    __name__
)
