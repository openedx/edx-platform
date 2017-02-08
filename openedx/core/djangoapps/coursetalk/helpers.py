"""
CourseTalk widget helpers
"""
from __future__ import unicode_literals

from openedx.core.djangoapps.coursetalk import models


def get_coursetalk_course_key(course_key):
    """
    Return course key for coursetalk widget

    CourseTalk unique key for a course contains only organization and course code.
    :param course_key: SlashSeparatedCourseKey instance
    :type course_key: SlashSeparatedCourseKey
    :return: CourseTalk course key
    :rtype: str
    """
    return '{0.org}_{0.course}'.format(course_key)


def inject_coursetalk_keys_into_context(context, course_key):
    """
    Set params to view context based on course_key and CourseTalkWidgetConfiguration

    :param context: view context
    :type context: dict
    :param course_key: SlashSeparatedCourseKey instance
    :type course_key: SlashSeparatedCourseKey
    """
    show_coursetalk_widget = models.CourseTalkWidgetConfiguration.is_enabled()
    if show_coursetalk_widget:
        context['show_coursetalk_widget'] = True
        context['platform_key'] = models.CourseTalkWidgetConfiguration.get_platform_key()
        context['course_review_key'] = get_coursetalk_course_key(course_key)
