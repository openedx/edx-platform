"""
Badging app views
"""
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.views.decorators.http import require_GET
from opaque_keys.edx.keys import CourseKey

from common.lib.nodebb_client.client import NodeBBClient
from courseware.courses import get_course_with_access
from edxmako.shortcuts import render_to_response
from nodebb.models import DiscussionCommunity
from student.models import CourseEnrollment

from .constants import BADGES_KEY, COMMUNITY_URL_KEY, COURSE_ID_KEY, COURSE_NAME_KEY, COURSES_KEY
from .helpers.badges import (
    add_posts_count_in_badges_list,
    get_badge_progress_request_data,
    get_course_badges,
    get_discussion_team_ids,
    populate_trophycase
)
from .models import UserBadge


@require_GET
@login_required
def trophycase(request):
    """
    This view displays list of all badges in enrolled courses

    Args:
        request (HttpRequest): Django request object

    Returns:
        HttpResponse: Template with context
    """
    user = request.user

    enrolled_courses_data = CourseEnrollment.enrollments_for_user(user).order_by(
        COURSE_NAME_KEY).values_list(COURSE_ID_KEY, COURSE_NAME_KEY)

    earned_user_badges = list(
        UserBadge.objects.filter(user=user)
    )

    trophycase_dict = populate_trophycase(user, enrolled_courses_data, earned_user_badges)

    # Get list of dictionary keys in CourseKey Format
    course_key_list = [CourseKey.from_string(unicode(course_id)) for course_id in trophycase_dict.keys()]

    discussion_courses = DiscussionCommunity.objects.filter(
        course_id__in=course_key_list).values(COURSE_ID_KEY, COMMUNITY_URL_KEY)

    courses = []
    if discussion_courses:
        for discussion_course in discussion_courses:
            course_id = str(discussion_course[COURSE_ID_KEY])
            courses.append(get_discussion_team_ids(
                course_id, int(discussion_course[COMMUNITY_URL_KEY].split('/')[0]), trophycase_dict[course_id]))
    else:
        # WE are passing 0 as discussion id in case DiscussionCommunity didn't provide
        # us with any data so that our API won't break.
        for course_id in trophycase_dict.keys():
            courses.append(get_discussion_team_ids(course_id, 0, trophycase_dict[course_id]))

    status_code, response = NodeBBClient().badges.get_progress(
        request_data=get_badge_progress_request_data(user.username, courses))

    if status_code == 200 and response:
        for course in response[COURSES_KEY]:
            add_posts_count_in_badges_list(course, trophycase_dict[course.keys()[0]][BADGES_KEY])

    return render_to_response(
        'features/badging/trophy_case.html',
        {
            'trophycase_data': trophycase_dict
        }
    )


@require_GET
@login_required
def my_badges(request, course_id):
    """
    This view displays list of all badges related to one course

    Args:
        request (HttpRequest): Django request object

    Returns:
        HttpResponse: Template with context
    """
    user = request.user

    course_key = CourseKey.from_string(unicode(course_id))
    course = get_course_with_access(user, 'load', course_key)
    if not CourseEnrollment.is_enrolled(user, course_key):
        raise Http404

    # list of badges earned by user
    earned_user_badges = list(
        UserBadge.objects.filter(user=user, course_id=course_key)
    )

    badges = get_course_badges(user, course_key, earned_user_badges)

    # This will always get result because every course must have discussion board and this will return its ID.
    try:
        discussion_id = DiscussionCommunity.objects.get(course_id=course_key).community_url.split('/')[0]
    except DiscussionCommunity.DoesNotExist:
        discussion_id = 0

    # Here we are dealing with just one course so we can wrap this course details in '[]'
    # because our API on NodeBB side only accepts params in this format.
    courses = [get_discussion_team_ids(course_id, int(discussion_id), badges)]

    status_code, response = NodeBBClient().badges.get_progress(
        request_data=get_badge_progress_request_data(user.username, courses))

    if status_code == 200 and response:
        # Here we are dealing with just one course so we are getting Zero(0th) index from list.
        add_posts_count_in_badges_list(response[COURSES_KEY][0], badges[BADGES_KEY])

    return render_to_response(
        'features/badging/my_badges.html',
        {
            'course': course,
            BADGES_KEY: badges
        }
    )
