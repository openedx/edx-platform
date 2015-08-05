"""
This file contains receivers of course publication signals.
"""

import logging

from django.dispatch import receiver
from django.utils import timezone
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.credit.utils import get_course_xblocks
from openedx.core.djangoapps.signals.signals import GRADES_UPDATED
from xmodule.modulestore.django import modulestore
from xmodule.partitions.partitions import Group, UserPartition, NoSuchUserPartitionError


log = logging.getLogger(__name__)
# User partition scheme
VERIFICATION_SCHEME = "verification"
# Course modules categories on which an ICRV has access control
GATED_COURSE_CATEGORIES = ['vertical', 'sequential']
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
    # synchronously tag course content with ICRV access control
    tag_course_content_with_partition_scheme(course_key, partition_scheme='verification')

    # Import here, because signal is registered at startup, but items in tasks
    # are not yet able to be loaded
    from openedx.core.djangoapps.credit import api, tasks

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
    # TODO: Dynamically update user_id (actual course publisher)
    user_id = 1

    # get user partition with provided partition scheme
    user_partition = UserPartition.get_scheme(partition_scheme)
    if user_partition is None:
        # log and raise exception 'NoSuchUserPartitionError' if no matching
        # user partition exists
        log.error(
            u'No user partition found with scheme "%s". Exiting tagging course content with user partition.',
            partition_scheme
        )
        raise NoSuchUserPartitionError

    access_control_credit_xblocks = _get_credit_xblocks_for_access_control(course_key)
    all_user_partitions = []
    for block in access_control_credit_xblocks:
        # for now we are only entertaining verification partition scheme
        if partition_scheme == VERIFICATION_SCHEME:
            # TODO: Break code in small reusable code
            # create group configuration for VerificationPartitionScheme
            group_configuration = _verification_partition_group_configuration(user_partition, block)
            all_user_partitions.append(group_configuration)

            # update 'group_access' field of gating xblock with groups
            # 'verified_allow' and 'verified_deny' of newly created group
            # configuration
            access_dict = {
                group_configuration.id: [
                    group_configuration.get_group('verified_allow').id,
                    group_configuration.get_group('verified_deny').id,
                ]
            }
            block.group_access = access_dict
            modulestore().update_item(block, user_id)

            # now for course content access control, add groups
            # 'non_verified' and 'verified_allow' in 'group_access' field of
            # current ICRV's grand parent (if category of parent and grand
            # parent are 'vertical' and 'sequential' respectively);
            # otherwise add groups to current ICRV's parent only
            access_dict = {
                group_configuration.id: [
                    group_configuration.get_group('non_verified').id,
                    group_configuration.get_group('verified_allow').id,
                ]
            }
            parent_block = block.get_parent()
            grandparent_block = parent_block.get_parent()
            ancestor_categories = [parent_block.location.category, grandparent_block.location.category]

            # update 'group_access' field of parent only (immediate siblings
            # will have access control)
            ancestor_for_update = parent_block
            if len(set(ancestor_categories).difference(set(GATED_COURSE_CATEGORIES))) == 0:
                # category of parent and grand parent are 'vertical' and
                # 'sequential' respectively so update 'group_access' field of
                # grandparent
                ancestor_for_update = grandparent_block

            ancestor_for_update.group_access = access_dict
            modulestore().update_item(ancestor_for_update, user_id)

    # Now add all newly created partition in 'user_partitions' field of course
    course = modulestore().get_course(course_key, depth=0)
    # TODO: Consider deleting old user partition with same scheme for proper cleanup, preserve non matching partitions
    course.user_partitions = all_user_partitions
    modulestore().update_item(course, user_id)
    # TODO: Check that course and modules are properly updated in database


def _verification_partition_group_configuration(user_partition, block):
    """ Create verification user partition for given block.

    Args:
        user_partition (UserPartition): UserPartition object
        block (xblock): XBlock mixin

    """
    group_configuration_id = user_partition.key_for_partition(block.location)
    group_configuration_name = u"Verification Checkpoint for {checkpoint_name}".format(
        checkpoint_name=block.display_name
    )
    group_configuration_description = group_configuration_name
    # TODO: Group requires id to be an int value. Properly handle using strings as id's
    group_configuration_groups = [
        Group('non_verified', 'Not enrolled in a verified track'),
        Group('verified_allow', 'Enrolled in a verified track and has access'),
        Group('verified_deny', 'Enrolled in a verified track and does not have access'),
    ]
    group_configuration_parameters = {'location': unicode(block.location)}

    group_configuration = UserPartition(
        id=group_configuration_id,
        name=group_configuration_name,
        description=group_configuration_description,
        groups=group_configuration_groups,
        scheme=VERIFICATION_SCHEME,
        parameters=group_configuration_parameters,
    )
    return group_configuration


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
        credit_blocks.extend(xblocks)

    return credit_blocks
