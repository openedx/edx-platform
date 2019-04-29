"""
Grades API URLs.
"""

from django.conf.urls import include, url


app_name = 'lms.djangoapps.program_enrollments'

urlpatterns = [
    url(r'^v1/', include('program_enrollments.api.v1.urls', namespace='v1'))
]
