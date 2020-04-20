"""
Content library signal handlers.
"""

import logging

from django.dispatch import receiver

from lms.djangoapps.grades.api import signals as grades_signals

from .models import LtiGradedResource


log = logging.getLogger(__name__)


@receiver(grades_signals.PROBLEM_WEIGHTED_SCORE_CHANGED)
def score_changed_handler(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Match the score event to an LTI resource and update.
    """

    modified = kwargs.get('modified')
    usage_id = kwargs.get('usage_id')
    user_id = kwargs.get('user_id')
    weighted_earned = kwargs.get('weighted_earned')
    weighted_possible = kwargs.get('weighted_possible')

    if None in (modified, usage_id, user_id, weighted_earned, weighted_possible):
        log.error("LTI 1.3: Score Signal: Missing a required parameters, "
                  "ignoring: kwargs=%s", kwargs)
        return
    try:
        resource = LtiGradedResource.objects.get_from_user_id(
            user_id, usage_key=usage_id
        )
    except LtiGradedResource.DoesNotExist:
        log.error("LTI 1.3: Score Signal: Unknown resource, ignoring: kwargs=%s",
                  kwargs)
    else:
        resource.update_score(weighted_earned, weighted_possible, modified)
        log.info("LTI 1.3: Score Signal: Grade upgraded: resource; %s",
                 resource)
