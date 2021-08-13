"""
Contentstore signals
"""


import logging
from django.dispatch.dispatcher import receiver
from openedx.core.djangoapps.content.course_overviews.signals import COURSE_PACING_CHANGED

log = logging.getLogger(__name__)
from django.dispatch import Signal

# Signal that indicates that a course grading policy has been updated.
# This signal is generated when a grading policy change occurs within
# modulestore for either course or subsection changes.
GRADING_POLICY_CHANGED = Signal(
    providing_args=[
        'user_id',  # Integer User ID
        'course_key',  # Unicode string representing the course
    ]
)



@receiver(COURSE_PACING_CHANGED, dispatch_uid="update_cert_settings_on_pacing_change")
def _update_cert_settings_on_pacing_change(sender, updated_course_overview, **kwargs):  # pylint: disable=unused-argument
    """
    Catches the signal that course pacing has changed and enable/disable
    the self-generated certificates according to course-pacing.
    """
    log.info('This receiver will now work')
