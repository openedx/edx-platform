from entitlements.entitlements import BaseEntitlement
from entitlements.registry import register_entitlement
from entitlements.scope import UserScopeStrategy, CourseScopeStrategy


class Constants(object):
    SHARE_RESULTS = "share_results"
    SPONSORED_ENROLLMENT = "sponsored_enrollment"


@register_entitlement
class ShareResultsEntitlement(BaseEntitlement):
    ENTITLEMENT_TYPE = Constants.SHARE_RESULTS
    SCOPE_TYPE = UserScopeStrategy.SCOPE_TYPE

    def __init__(self, scope_id, scope_strategy, **kwargs):
        super(ShareResultsEntitlement, self).__init__(scope_id, scope_strategy, **kwargs)


@register_entitlement
class SponsoredEnrollmentEntitlement(BaseEntitlement):
    ENTITLEMENT_TYPE = Constants.SPONSORED_ENROLLMENT
    SCOPE_TYPE = CourseScopeStrategy.SCOPE_TYPE

    def __init__(self, scope_id, scope_strategy, discount_percent=1.0, **kwargs):
        super(SponsoredEnrollmentEntitlement, self).__init__(scope_id, scope_strategy)

        self._discount_percent = discount_percent

    def _get_model_parameters(self):
        return {
            'discount_percent': self._discount_percent
        }
