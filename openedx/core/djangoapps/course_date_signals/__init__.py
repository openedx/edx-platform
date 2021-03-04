"""
Django app to manage course content dates, and ingesting them into edx-when for later use by the LMS.
"""

default_app_config = 'openedx.core.djangoapps.course_date_signals.apps.CourseDatesSignalsConfig'  # pylint: disable=invalid-name
