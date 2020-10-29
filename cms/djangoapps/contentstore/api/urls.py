""" Course API URLs. """


from django.conf import settings
from django.conf.urls import url

from cms.djangoapps.contentstore.api.views import course_import, course_quality, course_validation

app_name = 'contentstore'

urlpatterns = [
    url(r'^v0/import/{course_id}/$'.format(course_id=settings.COURSE_ID_PATTERN,),
        course_import.CourseImportView.as_view(), name='course_import'),
    url(r'^v1/validation/{course_id}/$'.format(course_id=settings.COURSE_ID_PATTERN,),
        course_validation.CourseValidationView.as_view(), name='course_validation'),
    url(r'^v1/quality/{course_id}/$'.format(course_id=settings.COURSE_ID_PATTERN,),
        course_quality.CourseQualityView.as_view(), name='course_quality'),
]
