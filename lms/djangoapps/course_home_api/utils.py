"""Utility functions for course home"""

from django.conf import settings


def get_microfrontend_url(course_key, view_name=None):
    """
    Takes in a course key and view name, returns the appropriate course home mfe route
    """
    mfe_link = '{}/course/{}'.format(settings.LEARNING_MICROFRONTEND_URL, course_key)

    if view_name:
        mfe_link += '/{}'.format(view_name)

    return mfe_link
