from collections import OrderedDict

from django.template.loader import render_to_string
from django.urls import reverse
from edx_notifications.data import NotificationMessage
from edx_notifications.lib.publisher import get_notification_type, publish_notification_to_user

from lms.djangoapps.courseware.courses import get_course_by_id
from lms.djangoapps.teams import is_feature_enabled as is_teams_feature_enabled
from lms.djangoapps.teams.models import CourseTeam
from nodebb.constants import CONVERSATIONALIST_ENTRY_INDEX, TEAM_PLAYER_ENTRY_INDEX

from .constants import (
    BADGES_KEY,
    CONVERSATIONALIST,
    EARNED_BADGE_NOTIFICATION_TYPE,
    FILTER_BADGES_ERROR,
    TEAM_ID_KEY,
    TEAM_PLAYER,
    TEAM_ROOM_ID_KEY
)
from .models import Badge


def populate_trophycase(user, courses, earned_badges):
    """
    This method populate trophycase data into dictionary and returns it. This method has a hierarchy of
    enrolled courses, badge type, earned and yet to be earned badges with complete detail
    :param courses: Courses enrolled by user
    :param earned_badges: Badges earned by user
    :param user: Current logged-in user
    :return: dictionary containing trophycase json
    """
    trophycase_dict = OrderedDict()
    badge_queryset = Badge.objects.all().order_by('threshold')

    for course_key, display_name in courses:
        course_badges = get_course_badges(user, course_key, earned_badges, badge_queryset)

        course_id = unicode(course_key)
        trophycase_dict[course_id] = {
            'display_name': display_name,
        }
        trophycase_dict[course_id].update(course_badges)

    return trophycase_dict


def get_course_badges(user, course_id, earned_badges, badge_queryset=None):
    """
    Get all badges of a course in a hierarchy, categorised by badge type
    :param user: Current logged-in user
    :param badge_queryset: Badge queryset
    :param course_id: Course identifier
    :param earned_badges: All badges earned in a course
    :return: List of badges in a course
    """
    badges = {
        BADGES_KEY: dict()
    }

    if not badge_queryset:
        badge_queryset = Badge.objects.all().order_by('threshold')

    for badge_type, _ in Badge.BADGE_TYPES:

        if badge_type == TEAM_PLAYER[TEAM_PLAYER_ENTRY_INDEX]:
            course = get_course_by_id(course_id)

            if not is_teams_feature_enabled(course):
                # do not show team badges, for course, if teams are either not enabled or not configured
                continue

            course_team, earned_badges = filter_earned_badge_by_joined_team(user, course, earned_badges)

            if course_team:
                # only if user has joined any team
                badges[TEAM_ID_KEY] = course_team[TEAM_ID_KEY]

        badge_list = list(
            badge_queryset.filter(type=badge_type).values()
        )

        add_badge_earned_date(course_id, badge_list, earned_badges)

        badges[BADGES_KEY].update({
            badge_type: badge_list
        })

    return badges


def add_badge_earned_date(course_id, course_badges, earned_badges):
    """
    Add badge earned date in to badge, if badge is earned by user in specified course
    :param course_id: Course identifier
    :param course_badges: All badges of a course
    :param earned_badges: All badges earned in a course
    """
    for badge in course_badges:
        for earned_badge in earned_badges:
            if badge['id'] == earned_badge.badge_id and course_id == earned_badge.course_id:
                # earned date indicate badge is earned
                badge['date_earned'] = earned_badge.date_earned


def filter_earned_badge_by_joined_team(user, course, earned_badges):
    """
    This method filter badges earned, in a course, by team joined by user
    :param user: Current logged-in user
    :param course: Course, user enrolled in
    :param earned_badges: All badges earned in a course
    :return: A tuple containing:
        flag: Has user joined any team
        earned_badges: All badges earned in a course, specific to joined team
    """
    course_team = CourseTeam.objects.filter(course_id=course.id, users=user).values(TEAM_ID_KEY,
                                                                                    TEAM_ROOM_ID_KEY).first()

    if not course_team:
        # if user has not joined any team, return empty list for earned badges
        return course_team, list()

    if not course_team[TEAM_ROOM_ID_KEY]:
        error = FILTER_BADGES_ERROR.format(team_id=course_team[TEAM_ID_KEY])
        raise Exception(error)

    # filter earned badges for joined team only
    return course_team, [
        earned_badge for earned_badge in earned_badges if
        earned_badge.community_id == course_team[TEAM_ROOM_ID_KEY]
    ]


def get_badge_url(course_id, badge_type, team_id):
    """
    This method return badge url depends on badge_type
    :param course_id: Course Id
    :param badge_type: Badge type can be communicator or team
    :param team_id: Team Id
    :return: URL of badge in String format. Return "browse team" if user hasn't join any team.
    """
    badge_url = reverse('teams_dashboard', kwargs={'course_id': course_id})
    if badge_type == CONVERSATIONALIST[CONVERSATIONALIST_ENTRY_INDEX]:
        badge_url = reverse('nodebb_forum_discussion', kwargs={'course_id': course_id})
    elif badge_type == TEAM_PLAYER[TEAM_PLAYER_ENTRY_INDEX] and team_id:
        badge_url = reverse('view_team', kwargs={'course_id': course_id, 'team_id': team_id})
    return badge_url


def get_badge_progress(index, badges, team_joined=True):
    """
    This method calls from "my_badges.html" and "course_trophy_case.html".
    It return status for badges that will be applied as class on badges
    :param index: Index of badge which status is required.
    :param badges: Complete badges list
    :param team_joined: Boolean
    :return: A tuple containing classname and status. classname will be added to the div of badge and status
        text will be displayed on badge.
    """
    current_badge = badges[index]
    previous_badge = index and badges[index - 1]

    badge_progress = ('', 'Not Started')
    if not team_joined:
        return badge_progress
    elif 'date_earned' in current_badge:
        badge_progress = ('completed', 'Completed!')
    elif not previous_badge or 'date_earned' in previous_badge:
        badge_progress = ('in-progress', 'In Progress')
    return badge_progress


def send_user_badge_notification(user, my_badge_url, badge_name):
    """
    Send user new badge notification
    :param user: User receiving the Notification
    :param my_badge_url: Redirect url to my_badge view on notification click
    :param badge_name: Newly earned badge
    """
    context = {
        'badge_name': badge_name
    }

    body_short = render_to_string('philu_notifications/templates/user_badge_earned.html', context)

    message = NotificationMessage(
        msg_type=get_notification_type(EARNED_BADGE_NOTIFICATION_TYPE),
        payload={
            'from_user': user.username,
            'path': my_badge_url,
            'bodyShort': body_short,
        }
    )

    publish_notification_to_user(user.id, message)
