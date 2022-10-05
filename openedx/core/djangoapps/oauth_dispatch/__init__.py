from edx_toggles.toggles import WaffleSwitch

OAUTH_DISPATCH_WAFFLE_SWITCH_NAMESPACE = 'oauth_dispatch'

JWT_DISABLED_FOR_MOBILE = WaffleSwitch(
    f'{OAUTH_DISPATCH_WAFFLE_SWITCH_NAMESPACE}.jwt_disabled_for_mobile',
    __name__
)
