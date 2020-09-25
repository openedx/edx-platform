"""
Urls for badging app
"""
from django.conf import settings
from django.conf.urls import url

from .views import my_badges, trophycase

urlpatterns = [
    url(r'^trophycase/$', trophycase, name='trophycase'),
    url(r'^courses/{course_id}/my_badges/$'.format(course_id=settings.COURSE_ID_PATTERN), my_badges, name='my_badges'),
]
