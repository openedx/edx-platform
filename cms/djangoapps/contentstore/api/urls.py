""" Course API URLs. """


from django.conf import settings
from django.urls import re_path

from cms.djangoapps.contentstore.api.views import course_import, course_quality, course_validation, xblock

app_name = 'contentstore'

urlpatterns = [
    re_path(fr'^v0/import/{settings.COURSE_ID_PATTERN}/$',
            course_import.CourseImportView.as_view(), name='course_import'),
    re_path(fr'^v1/validation/{settings.COURSE_ID_PATTERN}/$',
            course_validation.CourseValidationView.as_view(), name='course_validation'),
    re_path(fr'^v1/quality/{settings.COURSE_ID_PATTERN}/$',
            course_quality.CourseQualityView.as_view(), name='course_quality'),
    re_path(fr'^v1/xblock/{settings.COURSE_ID_PATTERN}/{settings.USAGE_KEY_PATTERN}/$',
            xblock.XblockView.as_view(), name='xblock'),
]
