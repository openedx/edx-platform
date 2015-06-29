"""
This file contains receivers of course publication signals.
"""

from django.dispatch import receiver
from django.utils import timezone
from opaque_keys.edx.keys import CourseKey

from xmodule.modulestore.django import SignalHandler
from openedx.core.djangoapps.signals.signals import GRADES_UPDATED


@receiver(SignalHandler.course_published)
def listen_for_course_publish(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """Receive 'course_published' signal and kick off a celery task to update
    the credit course requirements.
    """

    # Import here, because signal is registered at startup, but items in tasks
    # are not yet able to be loaded
    from .tasks import update_credit_course_requirements

    update_credit_course_requirements.delay(unicode(course_key))


@receiver(GRADES_UPDATED)
def listen_for_grade_calculation(sender, username, grade_summary, course_key, deadline, **kwargs):  # pylint: disable=unused-argument
    """Receive 'MIN_GRADE_REQUIREMENT_STATUS' signal and update minimum grade
    requirement status.

    Args:
        sender: None
        username(string): user name
        grade_summary(dict): Dict containing output from the course grader
        course_key(CourseKey): The key for the course
        deadline(datetime): Course end date or None

    Kwargs:
        kwargs : None

    """
    from openedx.core.djangoapps.credit.api import (
        is_credit_course, get_credit_requirement, set_credit_requirement_status
    )

    course_id = CourseKey.from_string(unicode(course_key))
    is_credit = is_credit_course(course_id)
    if is_credit:
        requirement = get_credit_requirement(course_id, 'grade', 'grade')
        if requirement:
            criteria = requirement.get('criteria')
            if criteria:
                min_grade = criteria.get('min_grade')
                if grade_summary['percent'] >= min_grade:
                    reason_dict = {'final_grade': grade_summary['percent']}
                    set_credit_requirement_status(
                        username, course_id, 'grade', 'grade', status="satisfied", reason=reason_dict
                    )
                elif deadline and deadline < timezone.now():
                    set_credit_requirement_status(
                        username, course_id, 'grade', 'grade', status="failed", reason={}
                    )
