"""
Grades API URLs.
"""


from django.conf.urls import include
from django.urls import path

app_name = 'lms.djangoapps.grades'

urlpatterns = [
    path('v1/', include('lms.djangoapps.grades.rest_api.v1.urls', namespace='v1'))
]
