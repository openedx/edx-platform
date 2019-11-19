from collections import OrderedDict

from .models import Badge


def populate_trophycase(courses, earned_badges):
    """
    This method populate trophycase data into dictionary and returns it. This method has a hierarchy of
    enrolled courses, badge type, earned and yet to be earned badges with complete detail
    :param courses: Courses enrolled by user
    :param earned_badges: Badges earned by user
    :return: dictionary containing trophycase json
    """
    trophycase_dict = OrderedDict()

    for course_id, display_name in courses:

        course_badges = get_all_badges(course_id, earned_badges)

        trophycase_dict[unicode(course_id)] = {
            'display_name': display_name,
            'badges': course_badges
        }

    return trophycase_dict


def get_all_badges(course_id, earned_badges):
    """
    Get all badges of a course in a hierarchy, categorised by badge type
    :param course_id: Course identifier
    :param earned_badges: All badges earned in a course
    :return: List of badges in a course
    """
    badges = list()

    for badge_type, _ in Badge.BADGE_TYPES:
        badge_list = list(
            Badge.objects.filter(type=badge_type).order_by('threshold').values()
        )

        add_badge_earned_date(course_id, badge_list, earned_badges)

        badges.append({
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
