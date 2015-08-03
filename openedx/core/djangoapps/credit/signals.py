"""
This file contains receivers of course publication signals.
"""

import logging

from django.dispatch import receiver
from django.utils import timezone
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.credit.partition_schemes import VerificationPartitionScheme
from openedx.core.djangoapps.credit.utils import get_course_xblocks
from openedx.core.djangoapps.signals.signals import GRADES_UPDATED


log = logging.getLogger(__name__)
# XBlocks that are used as course credit requirements and are required for
# access control of specific gated course contents
GATED_CREDIT_XBLOCK_CATEGORIES = ['edx-reverification-block']


def on_course_publish(course_key):  # pylint: disable=unused-argument
    """
    Will receive a delegated 'course_published' signal from cms/djangoapps/contentstore/signals.py
    and kick off a celery task to update the credit course requirements.

    IMPORTANT: It is assumed that the edx-proctoring subsystem has been appropriate refreshed
    with any on_publish event workflow *BEFORE* this method is called.
    """

    # Import here, because signal is registered at startup, but items in tasks
    # are not yet able to be loaded
    from openedx.core.djangoapps.credit import api, tasks
    tag_course_content_with_partition_scheme(course_key, partition_scheme='verification')

    if api.is_credit_course(course_key):
        tasks.update_credit_course_requirements.delay(unicode(course_key))
        log.info(u'Added task to update credit requirements for course "%s" to the task queue', course_key)


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


def tag_course_content_with_partition_scheme(course_key, partition_scheme):
    """ Create user partitions with provided partition scheme and tag credit
    blocks for the given course with those user partitions.

    Args:
        course_key (CourseKey): Identifier for the course.
        partition_scheme (str): Name of the user partition scheme

    """
    partition = None
    # create partition with provided partition scheme
    if partition_scheme == 'verification':
        partition = VerificationPartitionScheme()

    if partition is None:
        log.error(u'No user partition found with scheme "%s".', partition_scheme)
        # TODO: maybe raise a 'NoSuchUserPartitionError' exception if not user partition is present with provide 'partition_scheme'.
        return

    access_control_credit_xblocks = _get_credit_xblocks_for_access_control(course_key)
    for xblock in access_control_credit_xblocks:
        # TODO: Implement ICRV access control by assigning partitions with different groups (remove old access groups with same partition scheme), to the credit xblocks and save them.
        pass


def _get_credit_xblocks_for_access_control(course_key):
    """ Retrieve all credit requirements XBlocks in the course for categories
     in list 'GATED_CREDIT_XBLOCK_CATEGORIES'.

    Args:
        course_key (CourseKey): Identifier for the course.

    Returns:
        List of XBlocks that are published and haven't been deleted.
    """
    credit_blocks = []
    for category in GATED_CREDIT_XBLOCK_CATEGORIES:
        xblocks = get_course_xblocks(course_key, category)
        credit_blocks.append(xblocks)

    return credit_blocks
