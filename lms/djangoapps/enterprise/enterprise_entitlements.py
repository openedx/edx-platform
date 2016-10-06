"""
This module contains enterprise-specific entitlements.
"""
from entitlements.entitlements import BaseEntitlement
from entitlements.registry import register_entitlement
from entitlements.scope import UserScope, CourseScope


class Constants(object):
    SHARE_RESULTS = "share_results"
    SPONSORED_ENROLLMENT = "sponsored_enrollment"


@register_entitlement
class ShareResultsEntitlement(BaseEntitlement):
    """
    Entitlement to share learner's results with an Enterprise Customer
    """
    ENTITLEMENT_TYPE = Constants.SHARE_RESULTS
    SCOPE_TYPE = UserScope.SCOPE_TYPE

    def __init__(self, scope_id, scope_strategy, **kwargs):
        super(ShareResultsEntitlement, self).__init__(scope_id, scope_strategy, **kwargs)


@register_entitlement
class SponsoredEnrollmentEntitlement(BaseEntitlement):
    """
    Entitlement to sponsored (discounted) enrollment to a course
    """
    ENTITLEMENT_TYPE = Constants.SPONSORED_ENROLLMENT
    SCOPE_TYPE = CourseScope.SCOPE_TYPE

    def __init__(self, scope_id, scope_strategy, discount_percent=1.0, **kwargs):
        super(SponsoredEnrollmentEntitlement, self).__init__(scope_id, scope_strategy)

        self._discount_percent = discount_percent

    def _get_model_parameters(self):
        return {
            'discount_percent': self._discount_percent
        }
