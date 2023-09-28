"""
Content library signal handlers.
"""

import logging

from django.conf import settings
from django.dispatch import receiver

from lms.djangoapps.grades.api import signals as grades_signals
from opaque_keys import InvalidKeyError  # lint-amnesty, pylint: disable=wrong-import-order
from opaque_keys.edx.locator import LibraryUsageLocatorV2  # lint-amnesty, pylint: disable=wrong-import-order

from .models import LtiGradedResource


log = logging.getLogger(__name__)


@receiver(grades_signals.PROBLEM_WEIGHTED_SCORE_CHANGED)
def score_changed_handler(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Match the score event to an LTI resource and update.
    """

    lti_enabled = (settings.FEATURES.get('ENABLE_CONTENT_LIBRARIES')
                   and settings.FEATURES.get('ENABLE_CONTENT_LIBRARIES_LTI_TOOL'))
    if not lti_enabled:
        return

    modified = kwargs.get('modified')
    usage_id = kwargs.get('usage_id')
    user_id = kwargs.get('user_id')
    weighted_earned = kwargs.get('weighted_earned')
    weighted_possible = kwargs.get('weighted_possible')

    if None in (modified, usage_id, user_id, weighted_earned, weighted_possible):
        log.debug("LTI 1.3: Score Signal: Missing a required parameters, "
                  "ignoring: kwargs=%s", kwargs)
        return
    try:
        usage_key = LibraryUsageLocatorV2.from_string(usage_id)
    except InvalidKeyError:
        log.debug("LTI 1.3: Score Signal: Not a content libraries v2 usage key, "
                  "ignoring: usage_id=%s", usage_id)
        return
    try:
        resource = LtiGradedResource.objects.get_from_user_id(
            user_id, usage_key=usage_key
        )
    except LtiGradedResource.DoesNotExist:
        log.debug("LTI 1.3: Score Signal: Unknown resource, ignoring: kwargs=%s",
                  kwargs)
    else:
        resource.update_score(weighted_earned, weighted_possible, modified)
        log.info("LTI 1.3: Score Signal: Grade upgraded: resource; %s",
                 resource)
