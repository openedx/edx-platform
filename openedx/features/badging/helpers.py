import logging

from collections import OrderedDict

from lms.djangoapps.courseware.courses import get_course_by_id
from lms.djangoapps.teams import is_feature_enabled as is_teams_feature_enabled
from lms.djangoapps.teams.models import CourseTeam
from nodebb.constants import TEAM_PLAYER_ENTRY_INDEX
from nodebb.models import TeamGroupChat
from openedx.features.badging.constants import TEAM_PLAYER

from .constants import BADGES_KEY, FILTER_BADGES_ERROR
from .models import Badge

log = logging.getLogger('edx.badging')


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

    for course_id, display_name in courses:
        course_badges = get_course_badges(user, course_id, earned_badges, badge_queryset)

        trophycase_dict[unicode(course_id)] = {
            'display_name': display_name,
        }

        trophycase_dict[unicode(course_id)].update(course_badges)

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
            if course and not is_teams_feature_enabled(course):
                # do not show team badges, for course, if teams are either not enabled or not configured
                continue
            else:
                course_team, earned_badges = filter_earned_badge_by_joined_team(user, course, earned_badges)
                if not course_team:
                    # user has not joined any team
                    badges['team_joined'] = False

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
    :return: All badges earned in a course, specific to joined team
    """
    course_team = CourseTeam.objects.filter(course_id=course.id, users=user).values('id').first()
    if course_team:
        team_group_chat = TeamGroupChat.objects.filter(team_id=course_team['id']).values('room_id').first()

        if not team_group_chat:
            error = FILTER_BADGES_ERROR.format(team_id=course_team['id'])
            log.exception(error)
            raise Exception(error)

        # filter earned badges for joined team only
        earned_badges = [
            earned_badge for earned_badge in earned_badges if
            earned_badge.community_id == team_group_chat['room_id']
        ]
    return course_team, earned_badges
