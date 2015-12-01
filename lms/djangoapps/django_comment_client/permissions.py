"""
Module for checking permissions with the comment_client backend
"""

import logging
from types import NoneType

from request_cache.middleware import RequestCache
from lms.lib.comment_client import Thread
from opaque_keys.edx.keys import CourseKey

from django_comment_common.models import all_permissions_for_user_in_course
from teams.models import CourseTeam


def has_permission(user, permission, course_id=None):
    assert isinstance(course_id, (NoneType, CourseKey))
    request_cache_dict = RequestCache.get_request_cache().data
    cache_key = "django_comment_client.permissions.has_permission.all_permissions.{}.{}".format(
        user.id, course_id
    )
    if cache_key in request_cache_dict:
        all_permissions = request_cache_dict[cache_key]
    else:
        all_permissions = all_permissions_for_user_in_course(user, course_id)
        request_cache_dict[cache_key] = all_permissions

    return permission in all_permissions


CONDITIONS = ['is_open', 'is_author', 'is_question_author', 'is_team_member_if_applicable']


def get_team(commentable_id):
    """ Returns the team that the commentable_id belongs to if it exists. Returns None otherwise. """
    request_cache_dict = RequestCache.get_request_cache().data
    cache_key = "django_comment_client.team_commentable.{}".format(commentable_id)
    if cache_key in request_cache_dict:
        return request_cache_dict[cache_key]

    try:
        team = CourseTeam.objects.get(discussion_topic_id=commentable_id)
    except CourseTeam.DoesNotExist:
        team = None

    request_cache_dict[cache_key] = team
    return team


def _check_condition(user, condition, content):
    """ Check whether or not the given condition applies for the given user and content. """
    def check_open(_user, content):
        """ Check whether the content is open. """
        try:
            return content and not content['closed']
        except KeyError:
            return False

    def check_author(user, content):
        """ Check if the given user is the author of the content. """
        try:
            return content and content['user_id'] == str(user.id)
        except KeyError:
            return False

    def check_question_author(user, content):
        """ Check if the given user is the author of the original question for both threads and comments. """
        if not content:
            return False
        try:
            if content["type"] == "thread":
                return content["thread_type"] == "question" and content["user_id"] == str(user.id)
            else:
                # N.B. This will trigger a comments service query
                return check_question_author(user, Thread(id=content["thread_id"]).to_dict())
        except KeyError:
            return False

    def check_team_member(user, content):
        """
        If the content has a commentable_id, verifies that either it is not associated with a team,
        or if it is, that the user is a member of that team.
        """
        if not content:
            return False
        try:
            commentable_id = content['commentable_id']
            request_cache_dict = RequestCache.get_request_cache().data
            cache_key = "django_comment_client.check_team_member.{}.{}".format(user.id, commentable_id)
            if cache_key in request_cache_dict:
                return request_cache_dict[cache_key]
            team = get_team(commentable_id)
            if team is None:
                passes_condition = True
            else:
                passes_condition = team.users.filter(id=user.id).exists()
            request_cache_dict[cache_key] = passes_condition
        except KeyError:
            # We do not expect KeyError in production-- it usually indicates an improper test mock.
            logging.warning("Did not find key commentable_id in content.")
            passes_condition = False
        return passes_condition

    handlers = {
        'is_open': check_open,
        'is_author': check_author,
        'is_question_author': check_question_author,
        'is_team_member_if_applicable': check_team_member
    }

    return handlers[condition](user, content)


def _check_conditions_permissions(user, permissions, course_id, content):
    """
    Accepts a list of permissions and proceed if any of the permission is valid.
    Note that ["can_view", "can_edit"] will proceed if the user has either
    "can_view" or "can_edit" permission. To use AND operator in between, wrap them in
    a list.
    """

    def test(user, per, operator="or"):
        if isinstance(per, basestring):
            if per in CONDITIONS:
                return _check_condition(user, per, content)
            return has_permission(user, per, course_id=course_id)
        elif isinstance(per, list) and operator in ["and", "or"]:
            results = [test(user, x, operator="and") for x in per]
            if operator == "or":
                return True in results
            elif operator == "and":
                return False not in results
    return test(user, permissions, operator="or")


# Note: 'edit_content' is being used as a generic way of telling if someone is a privileged user
# (forum Moderator/Admin/TA), because there is a desire that team membership does not impact privileged users.
VIEW_PERMISSIONS = {
    'update_thread': ['edit_content', ['update_thread', 'is_open', 'is_author']],
    'create_comment': ['edit_content', ["create_comment", "is_open", "is_team_member_if_applicable"]],
    'delete_thread': ['delete_thread', ['update_thread', 'is_author']],
    'update_comment': ['edit_content', ['update_comment', 'is_open', 'is_author']],
    'endorse_comment': ['endorse_comment', 'is_question_author'],
    'openclose_thread': ['openclose_thread'],
    'create_sub_comment': ['edit_content', ['create_sub_comment', 'is_open', 'is_team_member_if_applicable']],
    'delete_comment': ['delete_comment', ['update_comment', 'is_open', 'is_author']],
    'vote_for_comment': ['edit_content', ['vote', 'is_open', 'is_team_member_if_applicable']],
    'undo_vote_for_comment': ['edit_content', ['unvote', 'is_open', 'is_team_member_if_applicable']],
    'vote_for_thread': ['edit_content', ['vote', 'is_open', 'is_team_member_if_applicable']],
    'flag_abuse_for_thread': ['edit_content', ['vote', 'is_team_member_if_applicable']],
    'un_flag_abuse_for_thread': ['edit_content', ['vote', 'is_team_member_if_applicable']],
    'flag_abuse_for_comment': ['edit_content', ['vote', 'is_team_member_if_applicable']],
    'un_flag_abuse_for_comment': ['edit_content', ['vote', 'is_team_member_if_applicable']],
    'undo_vote_for_thread': ['edit_content', ['unvote', 'is_open', 'is_team_member_if_applicable']],
    'pin_thread': ['openclose_thread'],
    'un_pin_thread': ['openclose_thread'],
    'follow_thread': ['edit_content', ['follow_thread', 'is_team_member_if_applicable']],
    'follow_commentable': ['edit_content', ['follow_commentable', 'is_team_member_if_applicable']],
    'unfollow_thread': ['edit_content', ['unfollow_thread', 'is_team_member_if_applicable']],
    'unfollow_commentable': ['edit_content', ['unfollow_commentable', 'is_team_member_if_applicable']],
    'create_thread': ['edit_content', ['create_thread', 'is_team_member_if_applicable']],
}


def check_permissions_by_view(user, course_id, content, name):
    assert isinstance(course_id, CourseKey)
    try:
        p = VIEW_PERMISSIONS[name]
    except KeyError:
        logging.warning("Permission for view named %s does not exist in permissions.py", name)
    return _check_conditions_permissions(user, p, course_id, content)
