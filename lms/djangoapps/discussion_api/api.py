"""
Discussion API internal interface
"""
from collections import defaultdict
from urllib import urlencode
from urlparse import urlunparse

from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.http import Http404

from rest_framework.exceptions import PermissionDenied

from opaque_keys import InvalidKeyError
from opaque_keys.edx.locator import CourseKey

from courseware.courses import get_course_with_access
from discussion_api.forms import ThreadCreateExtrasForm
from discussion_api.pagination import get_paginated_data
from discussion_api.serializers import CommentSerializer, ThreadSerializer, get_context
from django_comment_client.base.views import (
    THREAD_CREATED_EVENT_NAME,
    get_comment_created_event_data,
    get_comment_created_event_name,
    get_thread_created_event_data,
    track_forum_event,
)
from django_comment_client.utils import get_accessible_discussion_modules
from lms.lib.comment_client.thread import Thread
from lms.lib.comment_client.utils import CommentClientRequestError
from openedx.core.djangoapps.course_groups.cohorts import get_cohort_id, is_commentable_cohorted


def _get_course_or_404(course_key, user):
    """
    Get the course descriptor, raising Http404 if the course is not found,
    the user cannot access forums for the course, or the discussion tab is
    disabled for the course.
    """
    course = get_course_with_access(user, 'load_forum', course_key)
    if not any([tab.type == 'discussion' for tab in course.tabs]):
        raise Http404
    return course


def _get_thread_and_context(request, thread_id, parent_id=None, retrieve_kwargs=None):
    """
    Retrieve the given thread and build a serializer context for it, returning
    both. This function also enforces access control for the thread (checking
    both the user's access to the course and to the thread's cohort if
    applicable). Raises Http404 if the thread does not exist or the user cannot
    access it.
    """
    retrieve_kwargs = retrieve_kwargs or {}
    try:
        if "mark_as_read" not in retrieve_kwargs:
            retrieve_kwargs["mark_as_read"] = False
        cc_thread = Thread(id=thread_id).retrieve(**retrieve_kwargs)
        course_key = CourseKey.from_string(cc_thread["course_id"])
        course = _get_course_or_404(course_key, request.user)
        context = get_context(course, request, cc_thread, parent_id)
        if (
                not context["is_requester_privileged"] and
                cc_thread["group_id"] and
                is_commentable_cohorted(course.id, cc_thread["commentable_id"])
        ):
            requester_cohort = get_cohort_id(request.user, course.id)
            if requester_cohort is not None and cc_thread["group_id"] != requester_cohort:
                raise Http404
        return cc_thread, context
    except CommentClientRequestError:
        # params are validated at a higher level, so the only possible request
        # error is if the thread doesn't exist
        raise Http404


def get_thread_list_url(request, course_key, topic_id_list):
    """
    Returns the URL for the thread_list_url field, given a list of topic_ids
    """
    path = reverse("thread-list")
    query_list = [("course_id", unicode(course_key))] + [("topic_id", topic_id) for topic_id in topic_id_list]
    return request.build_absolute_uri(urlunparse(("", "", path, "", urlencode(query_list), "")))


def get_course_topics(request, course_key):
    """
    Return the course topic listing for the given course and user.

    Parameters:

    course_key: The key of the course to get topics for
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

    course = _get_course_or_404(course_key, request.user)
    discussion_modules = get_accessible_discussion_modules(course, request.user)
    modules_by_category = defaultdict(list)
    for module in discussion_modules:
        modules_by_category[module.discussion_category].append(module)

    def get_sorted_modules(category):
        """Returns key sorted modules by category"""
        return sorted(modules_by_category[category], key=get_module_sort_key)

    courseware_topics = [
        {
            "id": None,
            "name": category,
            "thread_list_url": get_thread_list_url(
                request,
                course_key,
                [item.discussion_id for item in get_sorted_modules(category)]
            ),
            "children": [
                {
                    "id": module.discussion_id,
                    "name": module.discussion_target,
                    "thread_list_url": get_thread_list_url(request, course_key, [module.discussion_id]),
                    "children": [],
                }
                for module in get_sorted_modules(category)
            ],
        }
        for category in sorted(modules_by_category.keys())
    ]

    non_courseware_topics = [
        {
            "id": entry["id"],
            "name": name,
            "thread_list_url": get_thread_list_url(request, course_key, [entry["id"]]),
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


def get_thread_list(request, course_key, page, page_size, topic_id_list=None):
    """
    Return the list of all discussion threads pertaining to the given course

    Parameters:

    request: The django request objects used for build_absolute_uri
    course_key: The key of the course to get discussion threads for
    page: The page number (1-indexed) to retrieve
    page_size: The number of threads to retrieve per page
    topic_id_list: The list of topic_ids to get the discussion threads for

    Returns:

    A paginated result containing a list of threads; see
    discussion_api.views.ThreadViewSet for more detail.
    """
    course = _get_course_or_404(course_key, request.user)
    context = get_context(course, request)
    topic_ids_csv = ",".join(topic_id_list) if topic_id_list else None
    threads, result_page, num_pages, _ = Thread.search({
        "course_id": unicode(course.id),
        "group_id": (
            None if context["is_requester_privileged"] else
            get_cohort_id(request.user, course.id)
        ),
        "sort_key": "date",
        "sort_order": "desc",
        "page": page,
        "per_page": page_size,
        "commentable_ids": topic_ids_csv,
    })
    # The comments service returns the last page of results if the requested
    # page is beyond the last page, but we want be consistent with DRF's general
    # behavior and return a 404 in that case
    if result_page != page:
        raise Http404

    results = [ThreadSerializer(thread, context=context).data for thread in threads]
    return get_paginated_data(request, results, page, num_pages)


def get_comment_list(request, thread_id, endorsed, page, page_size):
    """
    Return the list of comments in the given thread.

    Parameters:

        request: The django request object used for build_absolute_uri and
          determining the requesting user.

        thread_id: The id of the thread to get comments for.

        endorsed: Boolean indicating whether to get endorsed or non-endorsed
          comments (or None for all comments). Must be None for a discussion
          thread and non-None for a question thread.

        page: The page number (1-indexed) to retrieve

        page_size: The number of comments to retrieve per page

    Returns:

        A paginated result containing a list of comments; see
        discussion_api.views.CommentViewSet for more detail.
    """
    response_skip = page_size * (page - 1)
    cc_thread, context = _get_thread_and_context(
        request,
        thread_id,
        retrieve_kwargs={
            "recursive": True,
            "user_id": request.user.id,
            "mark_as_read": True,
            "response_skip": response_skip,
            "response_limit": page_size,
        }
    )

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

    results = [CommentSerializer(response, context=context).data for response in responses]
    return get_paginated_data(request, results, page, num_pages)


def create_thread(request, thread_data):
    """
    Create a thread.

    Parameters:

        request: The django request object used for build_absolute_uri and
          determining the requesting user.

        thread_data: The data for the created thread.

    Returns:

        The created thread; see discussion_api.views.ThreadViewSet for more
        detail.
    """
    course_id = thread_data.get("course_id")
    if not course_id:
        raise ValidationError({"course_id": ["This field is required."]})
    try:
        course_key = CourseKey.from_string(course_id)
        course = _get_course_or_404(course_key, request.user)
    except (Http404, InvalidKeyError):
        raise ValidationError({"course_id": ["Invalid value."]})

    context = get_context(course, request)
    serializer = ThreadSerializer(data=thread_data, context=context)
    extras_form = ThreadCreateExtrasForm(thread_data)
    if not (serializer.is_valid() and extras_form.is_valid()):
        raise ValidationError(dict(serializer.errors.items() + extras_form.errors.items()))
    serializer.save()

    thread = serializer.object
    ret = serializer.data
    following = extras_form.cleaned_data["following"]
    if following:
        context["cc_requester"].follow(thread)
        ret["following"] = True

    track_forum_event(
        request,
        THREAD_CREATED_EVENT_NAME,
        course,
        thread,
        get_thread_created_event_data(thread, followed=following)
    )

    return ret


def create_comment(request, comment_data):
    """
    Create a comment.

    Parameters:

        request: The django request object used for build_absolute_uri and
          determining the requesting user.

        comment_data: The data for the created comment.

    Returns:

        The created comment; see discussion_api.views.CommentViewSet for more
        detail.
    """
    thread_id = comment_data.get("thread_id")
    parent_id = comment_data.get("parent_id")
    if not thread_id:
        raise ValidationError({"thread_id": ["This field is required."]})
    try:
        cc_thread, context = _get_thread_and_context(request, thread_id, parent_id)
    except Http404:
        raise ValidationError({"thread_id": ["Invalid value."]})

    serializer = CommentSerializer(data=comment_data, context=context)
    if not serializer.is_valid():
        raise ValidationError(serializer.errors)
    serializer.save()

    cc_comment = serializer.object
    track_forum_event(
        request,
        get_comment_created_event_name(cc_comment),
        context["course"],
        cc_comment,
        get_comment_created_event_data(cc_comment, cc_thread["commentable_id"], followed=False)
    )

    return serializer.data


def update_thread(request, thread_id, update_data):
    """
    Update a thread.

    Parameters:

        request: The django request object used for build_absolute_uri and
          determining the requesting user.

        thread_id: The id for the thread to update.

        update_data: The data to update in the thread.

    Returns:

        The updated thread; see discussion_api.views.ThreadViewSet for more
        detail.
    """
    cc_thread, context = _get_thread_and_context(request, thread_id)
    is_author = str(request.user.id) == cc_thread["user_id"]
    if not (context["is_requester_privileged"] or is_author):
        raise PermissionDenied()
    serializer = ThreadSerializer(cc_thread, data=update_data, partial=True, context=context)
    if not serializer.is_valid():
        raise ValidationError(serializer.errors)
    serializer.save()
    return serializer.data
