"""
Utils function for notifications app
"""
from common.djangoapps.student.models import CourseEnrollment

from .config.waffle import SHOW_NOTIFICATIONS_TRAY


def find_app_in_normalized_apps(app_name, apps_list):
    """
    Returns app preference based on app_name
    """
    for app in apps_list:
        if app.get('name') == app_name:
            return app
    return None


def find_pref_in_normalized_prefs(pref_name, app_name, prefs_list):
    """
    Returns preference based on preference_name and app_name
    """
    for pref in prefs_list:
        if pref.get('name') == pref_name and pref.get('app_name') == app_name:
            return pref
    return None


def get_show_notifications_tray(user):
    """
    Returns show_notifications_tray as boolean for the courses in which user is enrolled
    """
    show_notifications_tray = False
    learner_enrollments_course_ids = CourseEnrollment.objects.filter(
        user=user,
        is_active=True
    ).values_list('course_id', flat=True)

    for course_id in learner_enrollments_course_ids:
        if SHOW_NOTIFICATIONS_TRAY.is_enabled(course_id):
            show_notifications_tray = True
            break

    return show_notifications_tray


def get_list_in_batches(input_list, batch_size):
    """
    Divides the list of objects into list of list of objects each of length batch_size.
    """
    list_length = len(input_list)
    for index in range(0, list_length, batch_size):
        yield input_list[index: index + batch_size]
