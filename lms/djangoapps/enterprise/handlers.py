import logging

from django.dispatch import receiver

from lms.djangoapps.grades.signals.signals import SCORE_CHANGED
from .enterprise_entitlements import ShareResultsEntitlement


def _check_data_sharing_consent(user, entitlement_group):
    sharing_entitlement_models = entitlement_group.get_entitlement_models_of_type(
        ShareResultsEntitlement.ENTITLEMENT_TYPE
    )
    return any(
        entitlement_model for entitlement_model in sharing_entitlement_models
        if entitlement_model.get_entitlement().applicable_to(user)
    )


@receiver(SCORE_CHANGED)
def share_grade(sender, **kwargs):  # pylint: disable=unused-argument
    log = logging.getLogger(__name__)
    user = kwargs['user']
    groups_with_data_sharing_consent = [
        entitlement_group for entitlement_group in user.entitlement_groups.all()
        if _check_data_sharing_consent(user, entitlement_group)
    ]
    for entitlement_group in groups_with_data_sharing_consent:
        enterprise_customer = entitlement_group.enterprise_customer
        log.info("Sharing {user} progress data with {name}".format(user=user, name=enterprise_customer.name))
