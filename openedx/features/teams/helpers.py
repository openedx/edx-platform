"""
Helpers for teams application
"""
from random import choice

from django.conf import settings
from opaque_keys.edx.keys import CourseKey

from courseware.courses import get_course_with_access
from lms.djangoapps.teams.models import CourseTeam

USER_ICON_COLORS = [
    '#f44336', '#e91e63', '#9c27b0', '#673ab7', '#3f51b5',
    '#2196f3', '#009688', '#1b5e20', '#33691e', '#827717',
    '#e65100', '#ff5722', '#795548', '#607d8b'
]

TEAM_BANNER_COLORS = [
    '#AB4642', '#DC9656', '#F7CA88', '#A1B56C', '#86C1B9',
    '#7CAFC2', '#BA8BAF', '#A16946'
]


def serialize(queryset, request, serializer_cls, serializer_ctx, many=True):
    """
    Serialize and paginate objects in a queryset.

    :param QuerySet queryset: QuerySet of model
    :param HttpRequest request: http request
    :param class serializer_cls: Django Rest Framework Serializer subclass.
    :param dict serializer_ctx: Context dictionary to pass to the serializer
    :param bool many: True, to serialize a queryset or list of objects instead of a single object instance
    :return: serialized data
    :rtype: json
    """
    serializer_ctx["request"] = request  # Serialize

    serializer = serializer_cls(queryset, context=serializer_ctx, many=many)
    return serializer.data


def generate_random_user_icon_color():
    """
    Create random color code form given choices

    :return: Color code i.e. #f44336
    :rtype: string
    """
    return choice(USER_ICON_COLORS)


def generate_random_team_banner_color():
    """
    Create random color code form given choices

    :return: Color code i.e. #f44336
    :rtype: string
    """
    return choice(TEAM_BANNER_COLORS)


def make_embed_url(team_group_chat, user, topic_url=None):
    """
    Create an embeddable url, for team group chat, to embed into iFrame. First try to make url from topic_url,
    if it is None then from `team_group_chat` slug and if both are None then from room id.

    :param TeamGroupChat team_group_chat: Team group chat object
    :param User user: User object
    :param string topic_url: Topic url extracted from http request
    :return: An embeddable url
    :rtype: string
    """
    if topic_url:
        topic = topic_url.split("topic/")[1]
        return '{}/embed/{}?iframe=embedView&isTopic=True'.format(settings.NODEBB_ENDPOINT, topic)
    if team_group_chat.slug:
        return '{}/category/{}?iframe=embedView'.format(settings.NODEBB_ENDPOINT, team_group_chat.slug)
    else:
        return '{}/user/{}/chats/{}?iframe=embedView'.format(
            settings.NODEBB_ENDPOINT, user.username.lower(), team_group_chat.room_id
        )


def get_user_recommended_team(course_key, user):
    """
    Get recommended teams for the user

    :param CourseKey course_key: Course key object
    :param User user: user object
    :return: List of recommended teams
    :rtype: list
    """
    user_country = user.profile.country
    recommended_teams = CourseTeam.objects.filter(course_id=course_key,
                                                  country=user_country).exclude(users__in=[user]).all()

    return list(recommended_teams)


def get_user_course_with_access(course_id, user):
    """
    Method that wraps the `courseware.courses.get_course_with_access` to use
    `course_id` in string format with it

    :param string course_id: Id of a course
    :param User user: User object
    :return: course if user has access in this course
    :rtype: Course
    """
    course_key = CourseKey.from_string(course_id)
    return get_course_with_access(user, "load", course_key)


def get_team_topic(course, topic_id):
    """
    Get topic by `topic_id` from course

    :param Course course: course object
    :param string topic_id: Topic id
    :return: A valid topic in a course else None
    :rtype: dict or None
    """
    if not topic_id:
        return

    topics = [topic for topic in course.teams_topics if topic['id'] == topic_id] or (None,)
    return topics[0]
