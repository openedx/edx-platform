from django.conf import settings


def notes_enabled_for_course(course):

    '''
    Returns True if the notes app is enabled for the course, False otherwise.

    In order for the app to be enabled it must be:
        1) enabled globally via FEATURES.
        2) present in the course tab configuration.
    '''

    tab_found = "notes" in course.advanced_modules
    feature_enabled = settings.FEATURES.get('ENABLE_STUDENT_NOTES')

    return feature_enabled and tab_found
