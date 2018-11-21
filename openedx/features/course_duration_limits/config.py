"""
Content type gating waffle flag
"""
from openedx.core.djangoapps.waffle_utils import WaffleFlagNamespace, WaffleFlag


WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace(name=u'content_type_gating')

CONTENT_TYPE_GATING_FLAG = WaffleFlag(
    waffle_namespace=WAFFLE_FLAG_NAMESPACE,
    flag_name=u'debug',
    flag_undefined_default=False
)
