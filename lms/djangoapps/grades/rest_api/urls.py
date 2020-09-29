"""
Grades API URLs.
"""


from django.conf.urls import include, url

app_name = 'lms.djangoapps.grades'

urlpatterns = [
    url(r'^v1/', include('lms.djangoapps.grades.rest_api.v1.urls', namespace='v1'))
]
