"""
Discussion API internal interface
"""
from collections import defaultdict

from lazy.lazy import lazy

from django.core.exceptions import ValidationError
from django.http import Http404

from opaque_keys.edx.locator import CourseLocator

from courseware.courses import get_course_with_access
from discussion_api.pagination import get_paginated_data
from django_comment_client.utils import get_accessible_discussion_modules
from django_comment_common.models import (
    FORUM_ROLE_ADMINISTRATOR,
    FORUM_ROLE_COMMUNITY_TA,
    FORUM_ROLE_MODERATOR,
    Role,
)
from lms.lib.comment_client.thread import Thread
from lms.lib.comment_client.user import User
from lms.lib.comment_client.utils import CommentClientRequestError
from openedx.core.djangoapps.course_groups.cohorts import get_cohort_id, get_cohort_names
from xmodule.tabs import DiscussionTab


def _get_course_or_404(course_key, user):
    """
    Get the course descriptor, raising Http404 if the course is not found,
    the user cannot access forums for the course, or the discussion tab is
    disabled for the course.
    """
    course = get_course_with_access(user, 'load_forum', course_key)
    if not any([isinstance(tab, DiscussionTab) for tab in course.tabs]):
        raise Http404
    return course


def get_course_topics(course_key, user):
    """
    Return the course topic listing for the given course and user.

    Parameters:

    course: The course to get topics for
    user: The requesting user, for access control

    Returns:

    A course topic listing dictionary; see discussion_api.views.CourseTopicViews
    for more detail.
    """
    def get_module_sort_key(module):
        """
        Get the sort key for the module (falling back to the discussion_target
        setting if absent)
        """
        return module.sort_key or module.discussion_target

    course = _get_course_or_404(course_key, user)
    discussion_modules = get_accessible_discussion_modules(course, user)
    modules_by_category = defaultdict(list)
    for module in discussion_modules:
        modules_by_category[module.discussion_category].append(module)
    courseware_topics = [
        {
            "id": None,
            "name": category,
            "children": [
                {
                    "id": module.discussion_id,
                    "name": module.discussion_target,
                    "children": [],
                }
                for module in sorted(modules_by_category[category], key=get_module_sort_key)
            ],
        }
        for category in sorted(modules_by_category.keys())
    ]

    non_courseware_topics = [
        {
            "id": entry["id"],
            "name": name,
            "children": [],
        }
        for name, entry in sorted(
            course.discussion_topics.items(),
            key=lambda item: item[1].get("sort_key", item[0])
        )
    ]

    return {
        "courseware_topics": courseware_topics,
        "non_courseware_topics": non_courseware_topics,
    }


class _DiscussionContext(object):
    """
    A class that represents the context in which content can be translated
    between the comments service format and the API format. This encapsulates
    various operations involving relating data from the content (such as user
    ids) with data from django models (such as roles), as well as operations
    relating the content to the comments service's representation of the user.
    """
    def __init__(self, course_key, requester):
        """
        Initializes the _DiscussionContext, raising Http404 if the requesting
        user cannot access the course.
        """
        self._course_key = course_key
        course = _get_course_or_404(course_key, requester)
        self._requester = requester
        self._cc_requester = User.from_django_user(requester).retrieve()
        # TODO: cache staff_user_ids and ta_user_ids if we need to improve perf
        self._staff_user_ids = {
            user.id
            for role in Role.objects.filter(
                name__in=[FORUM_ROLE_ADMINISTRATOR, FORUM_ROLE_MODERATOR],
                course_id=course.id
            )
            for user in role.users.all()
        }
        self._ta_user_ids = {
            user.id
            for role in Role.objects.filter(name=FORUM_ROLE_COMMUNITY_TA, course_id=course.id)
            for user in role.users.all()
        }
        # For now, the only groups are cohorts
        self._group_ids_to_names = get_cohort_names(course)

    def is_user_privileged(self, user_id):
        """
        Returns a boolean indicating whether the user with the given user_id has
        a privileged role in the course.
        """
        return user_id in self._staff_user_ids or user_id in self._ta_user_ids

    def is_requester_privileged(self):
        """
        Returns a boolean indicating whether the requesting user has a
        privileged role in the course.
        """
        return self.is_user_privileged(self._requester.id)

    def is_content_anonymous(self, cc_content):
        """
        Returns a boolean indicating whether the given content should be made
        anonymous to the requesting user.
        """
        return (
            cc_content["anonymous"] or
            (cc_content["anonymous_to_peers"] and not self.is_requester_privileged())
        )

    def get_user_label(self, cc_user_id):
        """
        Returns a string indicating what label should be applied to the user
        with the given user id (the comments service stores user ids as
        strings); possible values are "staff" and "community_ta".
        """
        user_id = int(cc_user_id)
        return (
            "staff" if user_id in self._staff_user_ids else
            "community_ta" if user_id in self._ta_user_ids else
            None
        )

    def get_group_name(self, group_id):
        """Returns the name of the group with the given id in the course."""
        return self._group_ids_to_names.get(group_id)

    @lazy
    def _requester_cohort(self):
        """Returns the id of the requester's cohort in the course."""
        return get_cohort_id(self._requester, self._course_key)

    def requester_can_access(self, cc_thread):
        """
        Returns a boolean indicating whether the requesting user has permission
        to access the given thread.
        """
        return (
            self.is_requester_privileged() or
            not cc_thread["group_id"] or
            self._requester_cohort is None or
            cc_thread["group_id"] == self._requester_cohort
        )

    def requester_has_followed(self, cc_thread):
        """
        Returns a boolean indicating whether the requesting user has followed
        the given thread.
        """
        return cc_thread["id"] in self._cc_requester["subscribed_thread_ids"]

    def requester_has_flagged(self, cc_content):
        """
        Returns a boolean indicating whether the requesting user has flagged the
        given thread.
        """
        return self._cc_requester["id"] in cc_content["abuse_flaggers"]

    def requester_has_voted(self, cc_content):
        """
        Returns a boolean indicating whether the requesting user has voted for
        the given thread.
        """
        return cc_content["id"] in self._cc_requester["upvoted_ids"]


def _get_common_fields(cc_content, context):  # TODO: find a better pair of names
    """
    Convert fields that are common between threads and comments from the
    comments service format to the discussion API format.
    """
    is_anonymous = context.is_content_anonymous(cc_content)
    ret = {
        key: cc_content[key]
        for key in ["id", "created_at", "updated_at"]
    }
    ret.update({
        "author": None if is_anonymous else cc_content["username"],
        "author_label": (None if is_anonymous else context.get_user_label(cc_content["user_id"])),
        "raw_body": cc_content["body"],
        "abuse_flagged": context.requester_has_flagged(cc_content),
        "voted": context.requester_has_voted(cc_content),
        "vote_count": cc_content["votes"]["up_count"],
    })
    return ret


def _cc_thread_to_api_thread(thread, context):
    """
    Convert a thread data dict from the comment_client format (which is a direct
    representation of the format returned by the comments service) to the format
    used in this API

    Arguments:
      thread (comment_client.thread.Thread): The thread to convert
      context (_DiscussionContext): The context in which to translate the thread

    Returns:
      dict: The discussion_api format representation of the thread.
    """
    ret = _get_common_fields(thread, context)
    ret.update({
        key: thread[key]
        for key in [
            "course_id",
            "group_id",
            "title",
            "pinned",
            "closed",
        ]
    })
    ret.update({
        "topic_id": thread["commentable_id"],
        "group_name": context.get_group_name(thread["group_id"]),
        "type": thread["thread_type"],
        "following": context.requester_has_followed(thread),
        "comment_count": thread["comments_count"],
        "unread_comment_count": thread["unread_comments_count"],
    })
    return ret


def get_thread_list(request, course_key, page, page_size):
    """
    Return the list of all discussion threads pertaining to the given course

    Parameters:

    request: The django request objects used for build_absolute_uri
    course: The course to get discussion threads for
    page: The page number (1-indexed) to retrieve
    page_size: The number of threads to retrieve per page

    Returns:

    A paginated result containing a list of threads; see
    discussion_api.views.ThreadViewSet for more detail.
    """
    context = _DiscussionContext(course_key, request.user)
    threads, result_page, num_pages, _ = Thread.search({
        "course_id": unicode(course_key),
        "group_id": (
            None if context.is_requester_privileged() else
            get_cohort_id(request.user, course_key)
        ),
        "sort_key": "date",
        "sort_order": "desc",
        "page": page,
        "per_page": page_size,
    })
    # The comments service returns the last page of results if the requested
    # page is beyond the last page, but we want be consistent with DRF's general
    # behavior and return a 404 in that case
    if result_page != page:
        raise Http404

    results = [_cc_thread_to_api_thread(thread, context) for thread in threads]
    return get_paginated_data(request, results, page, num_pages)


def _cc_comment_to_api_comment(cc_comment, parent_id, context):
    """
    Convert a comment data dict from the comment_client format (which is a
    direct representation of the format returned by the comments service) to the
    format used in this API

    Arguments:
      cc_comment (comment_client.comment.Comment): The comment to convert
      context (_DiscussionContext): The context in which to translate the
        comment

    Returns:
      dict: The discussion_api format representation of the comment.
    """
    ret = _get_common_fields(cc_comment, context)
    ret.update({
        key: cc_comment[key]
        for key in ["thread_id"]
    })
    ret.update({
        "parent_id": parent_id,
        "children": [
            _cc_comment_to_api_comment(child, cc_comment["id"], context)
            for child in cc_comment["children"]
        ],
    })
    return ret


def get_comment_list(request, thread_id, endorsed, page, page_size):
    """
    Return the list of comments in the given thread.

    Parameters:

    request: The django request object used for build_absolute_uri and
      determining the requesting user.
    thread_id: The id of the thread to get comments for.
    endorsed: Boolean indicating whether to get endorsed or non-endorsed
      comments (or None for all comments). Must be None for a discussion thread
      and non-None for a question thread.
    page: The page number (1-indexed) to retrieve
    page_size: The number of threads to retrieve per page

    Returns:

    A paginated result containing a list of comments; see
    discussion_api.views.CommentViewSet for more detail.
    """
    response_skip = page_size * (page - 1)
    try:
        cc_thread = Thread(id=thread_id).retrieve(
            recursive=True,
            user_id=request.user.id,
            mark_as_read=True,
            response_skip=response_skip,
            response_limit=page_size
        )
    except CommentClientRequestError:
        raise Http404

    course_key = CourseLocator.from_string(cc_thread["course_id"])

    # Ensure user has access to thread
    context = _DiscussionContext(course_key, request.user)
    if not context.requester_can_access(cc_thread):
        raise Http404

    # Responses to discussion threads cannot be separated by endorsed, but
    # responses to question threads must be separated by endorsed due to the
    # existing comments service interface
    if cc_thread["thread_type"] == "question":
        if endorsed is None:
            raise ValidationError({"endorsed": ["This field is required for question threads."]})
        elif endorsed:
            # CS does not apply resp_skip and resp_limit to endorsed responses
            # of a question post
            responses = cc_thread["endorsed_responses"][response_skip:(response_skip + page_size)]
            resp_total = len(cc_thread["endorsed_responses"])
        else:
            responses = cc_thread["non_endorsed_responses"]
            resp_total = cc_thread["non_endorsed_resp_total"]
    else:
        if endorsed is not None:
            raise ValidationError(
                {"endorsed": ["This field may not be specified for discussion threads."]}
            )
        responses = cc_thread["children"]
        resp_total = cc_thread["resp_total"]

    # The comments service returns the last page of results if the requested
    # page is beyond the last page, but we want be consistent with DRF's general
    # behavior and return a 404 in that case
    if not responses and page != 1:
        raise Http404
    num_pages = (resp_total + page_size - 1) / page_size if resp_total else 1

    results = [_cc_comment_to_api_comment(response, None, context) for response in responses]
    return get_paginated_data(request, results, page, num_pages)
