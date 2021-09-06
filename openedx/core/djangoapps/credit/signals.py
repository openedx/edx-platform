"""
This file contains receivers of course publication signals.
"""


import logging

import six
from django.dispatch import receiver
from django.utils import timezone
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.signals.signals import COURSE_GRADE_CHANGED

log = logging.getLogger(__name__)


def on_course_publish(course_key):
    """
    Will receive a delegated 'course_published' signal from cms/djangoapps/contentstore/signals.py
    and kick off a celery task to update the credit course requirements.

    IMPORTANT: It is assumed that the edx-proctoring subsystem has been appropriate refreshed
    with any on_publish event workflow *BEFORE* this method is called.
    """

    # Import here, because signal is registered at startup, but items in tasks
    # are not yet able to be loaded
    from openedx.core.djangoapps.credit import api, tasks

    if api.is_credit_course(course_key):
        tasks.update_credit_course_requirements.delay(six.text_type(course_key))
        log.info(u'Added task to update credit requirements for course "%s" to the task queue', course_key)


@receiver(COURSE_GRADE_CHANGED)
def listen_for_grade_calculation(sender, user, course_grade, course_key, deadline, **kwargs):  # pylint: disable=unused-argument
    """Receive 'MIN_GRADE_REQUIREMENT_STATUS' signal and update minimum grade requirement status.

    Args:
        sender: None
        user(User): User Model object
        course_grade(CourseGrade): CourseGrade object
        course_key(CourseKey): The key for the course
        deadline(datetime): Course end date or None

    Kwargs:
        kwargs : None

    """
    # This needs to be imported here to avoid a circular dependency
    # that can cause migrations to fail.
    from openedx.core.djangoapps.credit import api
    course_id = CourseKey.from_string(six.text_type(course_key))
    is_credit = api.is_credit_course(course_id)
    if is_credit:
        requirements = api.get_credit_requirements(course_id, namespace='grade')
        if requirements:
            criteria = requirements[0].get('criteria')
            if criteria:
                min_grade = criteria.get('min_grade')
                passing_grade = course_grade.percent >= min_grade
                now = timezone.now()
                status = None
                reason = None

                if (deadline and now < deadline) or not deadline:
                    # Student completed coursework on-time

                    if passing_grade:
                        # Student received a passing grade
                        status = 'satisfied'
                        reason = {'final_grade': course_grade.percent}
                else:
                    # Submission after deadline

                    if passing_grade:
                        # Grade was good, but submission arrived too late
                        status = 'failed'
                        reason = {
                            'current_date': now,
                            'deadline': deadline
                        }
                    else:
                        # Student failed to receive minimum grade
                        status = 'failed'
                        reason = {
                            'final_grade': course_grade.percent,
                            'minimum_grade': min_grade
                        }

                # We do not record a status if the user has not yet earned the minimum grade, but still has
                # time to do so.
                if status and reason:
                    api.set_credit_requirement_status(
                        user, course_id, 'grade', 'grade', status=status, reason=reason
                    )
