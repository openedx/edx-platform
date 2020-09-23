"""
Helper methods
"""
import json
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
    BADGES_DATE_EARNED_KEY,
    BADGES_PROGRESS_KEY,
    COURSES_KEY,
    CONVERSATIONALIST,
    DISCUSSION_ID_KEY,
    DISCUSSION_COUNT_KEY,
    EARNED_BADGE_NOTIFICATION_TYPE,
    FILTER_BADGES_ERROR,
    POST_COUNT_KEY,
    TEAM_COUNT_KEY,
    TEAM_ID_KEY,
    TEAM_PLAYER,
    TEAM_ROOM_ID_KEY,
    THRESHOLD_LABEL_KEY,
    USERNAME_KEY
)
from .models import Badge

BADGE_TYPE_TEAM = TEAM_PLAYER[TEAM_PLAYER_ENTRY_INDEX]
BADGE_TYPE_CONVERSATIONALIST = CONVERSATIONALIST[CONVERSATIONALIST_ENTRY_INDEX]


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
    badge_queryset = Badge.objects.all().order_by(THRESHOLD_LABEL_KEY)

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
        badge_queryset = Badge.objects.all().order_by(THRESHOLD_LABEL_KEY)

    for badge_type, _ in Badge.BADGE_TYPES:

        if badge_type == BADGE_TYPE_TEAM:
            course = get_course_by_id(course_id)

            if not is_teams_feature_enabled(course):
                # do not show team badges, for course, if teams are either not enabled or not configured
                continue

            course_team, earned_badges = filter_earned_badge_by_joined_team(user, course, earned_badges)

            if course_team:
                # only if user has joined any team
                badges[TEAM_ID_KEY] = course_team[TEAM_ID_KEY]
                badges[TEAM_ROOM_ID_KEY] = course_team[TEAM_ROOM_ID_KEY]

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
                badge[BADGES_DATE_EARNED_KEY] = earned_badge.date_earned


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
    if badge_type == BADGE_TYPE_CONVERSATIONALIST:
        badge_url = reverse('nodebb_forum_discussion', kwargs={'course_id': course_id})
    elif badge_type == BADGE_TYPE_TEAM and team_id:
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
    elif BADGES_DATE_EARNED_KEY in current_badge:
        badge_progress = ('completed', 'Completed!')
    elif not previous_badge or BADGES_DATE_EARNED_KEY in previous_badge:
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


def get_discussion_team_ids(course_id, discussion_room_id, badges):
    """
    Return generic dictionary that contain another dictionary with course_id as key and contain
    discussion_room_id and team_room_id.
    :param course_id: Course Id in String format
    :param discussion_room_id: Discussion room Id in Int format
    :param badges: Dictionary contain badges
    """
    course_discussion_team = {
        course_id: {
            DISCUSSION_ID_KEY: discussion_room_id
        }
    }
    if TEAM_ROOM_ID_KEY in badges:
        course_discussion_team[course_id][TEAM_ID_KEY] = badges[TEAM_ROOM_ID_KEY]
    return course_discussion_team


def get_badge_progress_request_data(username, courses):
    """
    Return dictionary that contain username and course data regarding discussion room Id and team room Id.
    :param username: Username in String format
    :param courses: course data regarding discussion room Id and team room Id
    """
    return {
        USERNAME_KEY: username,
        COURSES_KEY: json.dumps(courses)
    }


def add_posts_count_in_badges_list(course, badges_list):
    """
    Add post count data in conversationalist badges and team badges
    :param course: Dictionary that contain information related to posts count in Discussion room and Team room.
    :param badges_list: Dictionary contain badges both conversationalist badges and team badges
    """
    course_key = course.keys()[0]
    discussion_posts_count = course[course_key][DISCUSSION_COUNT_KEY]
    conversationalist_badges = add_badge_progress(
        badges_list[BADGE_TYPE_CONVERSATIONALIST], discussion_posts_count)
    badges_list[BADGE_TYPE_CONVERSATIONALIST] = conversationalist_badges

    if BADGE_TYPE_TEAM in badges_list:
        team_posts_count = course[course_key].get(TEAM_COUNT_KEY, 0)
        team_badges = add_badge_progress(badges_list[BADGE_TYPE_TEAM], team_posts_count)
        badges_list[BADGE_TYPE_TEAM] = team_badges


def add_badge_progress(course_badges, posts_count):
    """
    Add post count and badge progress in badges that will than rendered in 'my badges' or 'my trophy case'
    :param course_badges: Badges data either conversationalist badges or team badges
    :param posts_count: Count of post in Int format
    """
    previous_threshold = 0
    for badge in course_badges:
        badge[THRESHOLD_LABEL_KEY] = badge[THRESHOLD_LABEL_KEY] - previous_threshold
        previous_threshold = badge[THRESHOLD_LABEL_KEY] + previous_threshold
        if BADGES_DATE_EARNED_KEY in badge:
            badge[BADGES_PROGRESS_KEY] = 100
            posts_count = posts_count - badge[THRESHOLD_LABEL_KEY]
        else:
            badge[POST_COUNT_KEY] = posts_count if posts_count > 0 else 0
            badge[BADGES_PROGRESS_KEY] = ((posts_count * 100) / badge[THRESHOLD_LABEL_KEY]) if posts_count > 0 else 0
            posts_count = posts_count - badge[THRESHOLD_LABEL_KEY]
    return course_badges
