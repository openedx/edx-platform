"""
This module contains handlers for signals emitted in other parts of LMS
"""
import logging

from django.dispatch import receiver

from lms.djangoapps.grades.signals.signals import SCORE_CHANGED
from .enterprise_entitlements import ShareResultsEntitlement


def _check_data_sharing_consent(user, entitlement_group):
    """
    Helper method - checks if user have data sharing consent Entitlement in specified EntitlementGroup
    :param django.contrib.auth.models.User user: target user
    :param EntitlementGroup entitlement_group: self-explanatory
    :return: boolean
    """
    # TODO: O(m*n) performance where m - number of groups of target user, n - number of entitlements in the group
    sharing_entitlement_models = entitlement_group.get_entitlement_models_of_type(
        ShareResultsEntitlement.ENTITLEMENT_TYPE
    )
    return any(
        entitlement_model for entitlement_model in sharing_entitlement_models
        if entitlement_model.get_entitlement().is_applicable_to(user)
    )


@receiver(SCORE_CHANGED)
def share_grade(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Handles SCORE_CHANGED signal emitted when learner's grade for some problem is changed
    """
    log = logging.getLogger(__name__)
    user = kwargs['user']
    # get all groups that have data sharing consent entitlement scoped to user
    groups_with_data_sharing_consent = [
        entitlement_group for entitlement_group in user.entitlement_groups.all()
        if _check_data_sharing_consent(user, entitlement_group)
    ]
    # ... each group should be linked to an enterprise customer, so we're sending learner's progress data to it.
    for entitlement_group in groups_with_data_sharing_consent:
        enterprise_customer = entitlement_group.enterprise_customer
        if enterprise_customer:
            # emulating sending data by logging an "INFO" record in the log
            log.info("Sharing {user} progress data with {name}".format(user=user, name=enterprise_customer.name))
