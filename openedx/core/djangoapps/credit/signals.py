"""
This file contains receivers of course publication signals.
"""

import logging

from django.dispatch import receiver
from django.utils import timezone
from opaque_keys.edx.keys import CourseKey

from util.db import generate_int_id, MYSQL_MAX_INT

from openedx.core.djangoapps.credit.partition_schemes import VerificationPartitionScheme
from openedx.core.djangoapps.credit.utils import (
    get_course_xblocks,
    exclude_by_scheme,
    get_group_access_blocks,
    get_course_partitions_used_ids,
)
from openedx.core.djangoapps.signals.signals import GRADES_UPDATED
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.partitions.partitions import Group, UserPartition, NoSuchUserPartitionError


log = logging.getLogger(__name__)
# Used in
MINIMUM_GROUP_ID = 100
# User partition scheme
VERIFICATION_SCHEME = "verification"
# Course modules categories on which an ICRV has access control
GATED_COURSE_CATEGORIES = ['vertical', 'sequential']
# XBlocks that are used as course credit requirements and are required for
# access control of specific gated course contents
GATED_CREDIT_XBLOCK_CATEGORIES = ['edx-reverification-block']


def on_course_publish(course_key):  # pylint: disable=unused-argument
    """Update the credit course requirements on receiving a delegated signal
    `course_published` from `cms/djangoapps/contentstore/signals.py` by
    kicking off a celery task.

    Add user partitions e.g., 'VerificationPartitionScheme' for the provided
    course and tag course content with these newly created user partitions.

    IMPORTANT: It is assumed that the edx-proctoring subsystem has been
    refreshed appropriately with any `on_publish` event workflow *BEFORE* this
    method is called.
    """
    # Import here, because signal is registered at startup, but items in tasks
    # are not yet able to be loaded
    from openedx.core.djangoapps.credit import api, tasks

    if api.is_credit_course(course_key):
        tasks.update_credit_course_requirements.delay(unicode(course_key))
        log.info(u'Added task to update credit requirements for course "%s" to the task queue', course_key)

    # now synchronously tag course content with ICRV access control
    with modulestore().bulk_operations(course_key, emit_signals=False):
        log.info(u'Start tagging course "%s" content with ICRV Access Control', course_key)
        tag_course_content_with_partition_scheme(course_key, partition_scheme='verification')
        log.info(u'Finished tagging course "%s" content with ICRV Access Control', course_key)


@receiver(GRADES_UPDATED)
def listen_for_grade_calculation(sender, username, grade_summary, course_key, deadline, **kwargs):  # pylint: disable=unused-argument
    """ Receive 'MIN_GRADE_REQUIREMENT_STATUS' signal and update minimum grade
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


def tag_course_content_with_partition_scheme(course_key, partition_scheme):  # pylint: disable=invalid-name
    """ Create user partitions with provided partition scheme and tag credit
    blocks for the given course with those user partitions.

    Course and its all block will be updated with their respective last
    editor's `edited_by`.

    Args:
        course_key (CourseKey): Identifier for the course
        partition_scheme (str): Name of the user partition scheme

    """
    # TODO: Refactor code (move code to proper files e.g., 'common/lib/xmodule/xmodule/partitions/partitions.py')
    # TODO: Increase logging (add logging for errors and success)

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
    new_user_partitions = []
    for block in access_control_credit_xblocks:
        # for now we are entertaining only verification partition scheme
        if partition_scheme == VERIFICATION_SCHEME:
            # create group configuration for VerificationPartitionScheme
            group_configuration = _verification_partition_group_configuration(course_key, user_partition, block)
            new_user_partitions.append(group_configuration)

            # update the 'group_access' of provided xblock 'block' and its ancestor.
            _update_content_group_access(block, group_configuration)

    # Now update course 'user_partitions' field and add all newly created user
    # partitions
    _update_course_user_partitions(course_key, partition_scheme, new_user_partitions)


def _access_dict(group_configuration, access_groups_id_list):
    """ Returns dict 'group_access' of provided user partition and its groups.

    Args:
        group_configuration  (UserPartition): UserPartition object
        access_groups_id_list  (List): List of id's of partition groups

    Returns:
        Dict object.

    """
    access_dict = {
        group_configuration.id: access_groups_id_list
    }
    return access_dict


def _update_content_group_access(block, group_configuration):
    """ Update the 'group_access' of provided xblock 'block' and its ancestor.

    Args:
        block (XBlock): XBlock mixin
        group_configuration  (UserPartition): UserPartition object

    """
    # update 'group_access' field of gating xblock with groups
    # 'verified_allow' and 'verified_deny' of provided user partition
    # 'group_configuration'
    access_groups_id_list = [VerificationPartitionScheme.VERIFIED_ALLOW, VerificationPartitionScheme.VERIFIED_DENY]
    # Assuming that there will be only one user partition for a block
    block.group_access = _access_dict(group_configuration, access_groups_id_list)

    # TODO: Use or delete 'block.group_access.update' after consultation with developers
    # Uncomment bottom line when we support multiple partitions for
    # 'group_access' field for a block, since for now when course author will
    # try to access 'Group Configurations' page then the method
    # '_get_content_groups_usage_info' in the file
    # 'cms/djangoapps/contentstore/course_group_config.py' will raise
    # exception 'ValueError: too many values to unpack'
    # block.group_access.update(_access_dict(group_configuration, access_groups_id_list))

    # Update only published version of the block in database
    _update_published_block(block)

    # now for course content access control, add groups
    # 'non_verified' and 'verified_allow' in 'group_access' field of
    # current ICRV's grand parent (if category of parent and grand
    # parent are 'vertical' and 'sequential' respectively);
    # otherwise add groups to current ICRV's parent only
    access_groups_id_list = [VerificationPartitionScheme.NON_VERIFIED, VerificationPartitionScheme.VERIFIED_ALLOW]
    access_dict = _access_dict(group_configuration, access_groups_id_list)

    parent_block = block.get_parent()
    grandparent_block = parent_block.get_parent()

    ancestor_categories = [parent_block.location.category, grandparent_block.location.category]

    # update 'group_access' field of parent only (immediate siblings
    # will have access control)
    ancestor_for_update = parent_block
    if not set(ancestor_categories).difference(set(GATED_COURSE_CATEGORIES)):
        # category of parent and grand parent are 'vertical' and 'sequential'
        # respectively so update 'group_access' field of immediate siblings
        # (unit components) and siblings of parent (verticals) of current block
        ancestor_for_update = grandparent_block
        for child in ancestor_for_update.get_children():
            if child.location != parent_block.location:
                # siblings of parent (verticals) of current block
                child.group_access = access_dict
                _update_published_block(child)
            else:
                # immediate siblings (unit components) of current block
                for grand_child in child.get_children():
                    if grand_child.location.category not in GATED_CREDIT_XBLOCK_CATEGORIES:
                        # update `group_access` for non gated course content e.g.,
                        # exclude ICRV blocks from updating
                        grand_child.group_access = access_dict
                        _update_published_block(grand_child)
    else:
        # category of parent and grand parent are not 'vertical' and
        # 'sequential' respectively so update 'group_access' field of children
        # (only immediate siblings of current block) of the parent
        for child in ancestor_for_update.get_children():
            if child.location.category not in GATED_CREDIT_XBLOCK_CATEGORIES:
                # update `group_access` for non gated course content e.g.,
                # exclude ICRV blocks from updating
                child.group_access = access_dict
                _update_published_block(child)


def _update_course_user_partitions(course_key, partition_scheme, new_user_partitions):
    """ Add provided user partitions in 'new_user_partitions' in
    'user_partitions' field of provided course.

    Remove all user partitions of course with same partition schemes as in
    provided 'partition_scheme'.

    Args:
        course_key (CourseKey): Identifier for the course
        partition_scheme (str): Name of the user partition scheme
        new_user_partitions (List): List of user partitions

    """
    course = modulestore().get_course(course_key, depth=0)
    # get list of user partitions for the course before updating them
    course_user_partitions_old = [user_partition.id for user_partition in course.user_partitions]
    course_user_partitions = exclude_by_scheme(course.user_partitions, partition_scheme)
    # set filtered 'course_user_partitions' and new 'new_user_partitions' user
    # partitions as course user partitions
    course.user_partitions = course_user_partitions + new_user_partitions
    # Update only published version of the block in database
    _update_published_block(course)

    # get list of user partitions for the course after updating them
    course_user_partitions_new = [user_partition.id for user_partition in course.user_partitions]
    # now get list of deleted user partitions for the course and update for
    # all course group access blocks
    deleted_partitions = list(set(course_user_partitions_old) - set(course_user_partitions_new))
    if deleted_partitions:
        # sync blocks with access roles according to new user partitions for the
        # course so that user is not denied access for blocks with non-existing
        # user partitions/groups
        _sync_course_content_deleted_partitions(course_key, deleted_partitions)


def _sync_course_content_deleted_partitions(course_key, deleted_partitions):  # pylint: disable=invalid-name
    """ Sync blocks with access roles according to new user partitions for
    the provided course.

    Args:
        course_key (CourseKey): Identifier for the course
        deleted_partitions (List): List of id's of deleted user partitions

    """
    # no action needed if there is no deleted user partitions
    if not deleted_partitions:
        return

    # get all course blocks with `group_access` field set, this might include
    # orphan blocks
    group_access_blocks = get_group_access_blocks(course_key)
    # loop over all block with access groups and update them conditionally (
    # remove access groups pointing to deleted user partitions), since we have
    # updated user partitions for course so some partitions may have been
    # deleted.
    for block in group_access_blocks:
        deleted_group_access = set(block.group_access).intersection(set(deleted_partitions))
        if deleted_group_access:
            for group_id in deleted_group_access:
                del block.group_access[group_id]

                # Update only published version of the block in database
                _update_published_block(block)


def _verification_partition_group_configuration(course_key, user_partition, block):  # pylint: disable=invalid-name
    """ Create verification user partition for given block.

    Group and UserPartition id's will be int.

    Args:`
        course_key (CourseKey): Identifier for the course
        user_partition (UserPartition): UserPartition object
        block (XBlock): XBlock mixin

    Returns:
        UserPartition object.

    """
    course = modulestore().get_course(course_key, depth=0)

    # make int id for user partition scheme `VerificationPartitionScheme` which
    # is unique in user partitions of the provided course
    group_configuration_id = generate_int_id(MINIMUM_GROUP_ID, MYSQL_MAX_INT, get_course_partitions_used_ids(course))
    group_configuration_name = u"Verification Checkpoint for {checkpoint_name}".format(
        checkpoint_name=block.display_name
    )
    group_configuration_description = group_configuration_name
    # Since Group requires id to be an int so map verification partition group names to int
    # 0: VerificationPartitionScheme.NON_VERIFIED
    # 1: VerificationPartitionScheme.VERIFIED_ALLOW
    # 2: VerificationPartitionScheme.VERIFIED_DENY
    group_configuration_groups = [
        Group(VerificationPartitionScheme.NON_VERIFIED, 'Not enrolled in a verified track'),
        Group(VerificationPartitionScheme.VERIFIED_ALLOW, 'Enrolled in a verified track and has access'),
        Group(VerificationPartitionScheme.VERIFIED_DENY, 'Enrolled in a verified track and does not have access'),
    ]
    group_configuration_parameters = {'location': unicode(block.location)}

    group_configuration = UserPartition(
        id=group_configuration_id,
        name=group_configuration_name,
        description=group_configuration_description,
        groups=group_configuration_groups,
        scheme=user_partition,
        parameters=group_configuration_parameters,
    )
    return group_configuration


def _get_credit_xblocks_for_access_control(course_key):  # pylint: disable=invalid-name
    """ Retrieve all credit requirements XBlocks in the course for categories
     in list 'GATED_CREDIT_XBLOCK_CATEGORIES'.

    Args:
        course_key (CourseKey): Identifier for the course

    Returns:
        List of XBlocks that are published and haven't been deleted.

    """
    credit_blocks = []
    for category in GATED_CREDIT_XBLOCK_CATEGORIES:
        xblocks = get_course_xblocks(course_key, category)
        credit_blocks.extend(xblocks)

    return credit_blocks


def _update_published_block(block):
    """ Update the provided XBlock in modulestore for published branch only.

    Use the xblock's last editor as modifier.

    Args:
        block (XBlock): XBlock mixin

    Returns:
        List of XBlocks that are published and haven't been deleted.

    """
    # Update the published branch only
    with modulestore().branch_setting(ModuleStoreEnum.Branch.published_only):
        # save updated block with the last editor
        modulestore().update_item(block, block.edited_by)
