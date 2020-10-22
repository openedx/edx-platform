"""
Feature toggles for user_authn.
"""
from openedx.core.djangoapps.waffle_utils import WaffleFlagNamespace, WaffleFlag

# Namespace
_WAFFLE_NAMESPACE = u'user_authn'
_WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace(_WAFFLE_NAMESPACE)

# Flags

# TODO (ARCH-247)
# Intended as a temporary toggle for roll-out of jwt cookies feature.
# Satisfies Use Case #3 "Ops - Monitored Rollout" from
# https://open-edx-proposals.readthedocs.io/en/latest/oep-0017-bp-feature-toggles.html
JWT_COOKIES_FLAG = WaffleFlag(_WAFFLE_FLAG_NAMESPACE, u'jwt_cookies')
