"""
URL definitions for the course_modes API.
"""


from django.conf.urls import include, url

app_name = 'common.djangoapps.course_modes.rest_api'

urlpatterns = [
    url(r'^v1/', include('common.djangoapps.course_modes.rest_api.v1.urls', namespace='v1')),
]
