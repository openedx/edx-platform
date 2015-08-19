"""
This file contains receivers of course publication signals.
"""

import logging

from django.dispatch import receiver
from django.utils import timezone
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.signals.signals import GRADES_UPDATED
from openedx.core.djangoapps.credit.verification_access import update_verification_partitions
from xmodule.modulestore.django import SignalHandler


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
        tasks.update_credit_course_requirements.delay(unicode(course_key))
        log.info(u'Added task to update credit requirements for course "%s" to the task queue', course_key)


@receiver(SignalHandler.pre_publish)
def on_pre_publish(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """
    Create user partitions for verification checkpoints.

    This is a pre-publish step since we need to write to the course descriptor.
    """
    from openedx.core.djangoapps.credit import api
    if api.is_credit_course(course_key):
        # For now, we are tagging content with in-course-reverification access groups
        # only in credit courses on publish.  In the long run, this is not where we want to put this.
        # This really should be a transformation on the course structure performed as a pre-processing
        # step by the LMS, and the transformation should be owned by the verify_student app.
        # Since none of that infrastructure currently exists, we're doing it this way instead.
        log.info(u"Starting to update in-course reverification access rules")
        update_verification_partitions(course_key)
        log.info(u"Finished updating in-course reverification access rules")


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
    # This needs to be imported here to avoid a circular dependency
    # that can cause syncdb to fail.
    from openedx.core.djangoapps.credit import api

    course_id = CourseKey.from_string(unicode(course_key))
    is_credit = api.is_credit_course(course_id)
    if is_credit:
        requirements = api.get_credit_requirements(course_id, namespace='grade')
        if requirements:
            criteria = requirements[0].get('criteria')
            if criteria:
                min_grade = criteria.get('min_grade')
                if grade_summary['percent'] >= min_grade:
                    reason_dict = {'final_grade': grade_summary['percent']}
                    api.set_credit_requirement_status(
                        username, course_id, 'grade', 'grade', status="satisfied", reason=reason_dict
                    )
                elif deadline and deadline < timezone.now():
                    api.set_credit_requirement_status(
                        username, course_id, 'grade', 'grade', status="failed", reason={}
                    )
