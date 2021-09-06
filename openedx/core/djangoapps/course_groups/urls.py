"""
Cohort API URLs
"""


from django.conf import settings
from django.conf.urls import url

import lms.djangoapps.instructor.views.api
import openedx.core.djangoapps.course_groups.views

urlpatterns = [
    url(
        r'^v1/settings/{}$'.format(
            settings.COURSE_KEY_PATTERN,
        ),
        openedx.core.djangoapps.course_groups.views.CohortSettings.as_view(),
        name='cohort_settings',
    ),
    url(
        r'^v1/courses/{}/cohorts/(?P<cohort_id>[0-9]+)?$'.format(
            settings.COURSE_KEY_PATTERN,
        ),
        openedx.core.djangoapps.course_groups.views.CohortHandler.as_view(),
        name='cohort_handler',
    ),
    url(
        r'^v1/courses/{}/cohorts/(?P<cohort_id>[0-9]+)/users/(?P<username>.+)?$'.format(
            settings.COURSE_KEY_PATTERN,
        ),
        openedx.core.djangoapps.course_groups.views.CohortUsers.as_view(),
        name='cohort_users',
    ),
    url(
        r'^v1/courses/{}/users?$'.format(
            settings.COURSE_KEY_PATTERN,
        ),
        lms.djangoapps.instructor.views.api.CohortCSV.as_view(),
        name='cohort_users_csv',
    ),
]
