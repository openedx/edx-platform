""" Course API URLs. """


from django.conf import settings
from django.conf.urls import url

from cms.djangoapps.contentstore.api.views import course_import, course_quality, course_validation

app_name = 'contentstore'

urlpatterns = [
    url(fr'^v0/import/{settings.COURSE_ID_PATTERN}/$',
        course_import.CourseImportView.as_view(), name='course_import'),
    url(fr'^v1/validation/{settings.COURSE_ID_PATTERN}/$',
        course_validation.CourseValidationView.as_view(), name='course_validation'),
    url(fr'^v1/quality/{settings.COURSE_ID_PATTERN}/$',
        course_quality.CourseQualityView.as_view(), name='course_quality'),
]
