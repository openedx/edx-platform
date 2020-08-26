"""
URLs for the Studio API [Course Run]
"""

from django.conf import settings
from django.conf.urls import url
from rest_framework.routers import DefaultRouter

from .views.course_runs import CourseRunViewSet
from .views.discussion_settings import discussion_settings_handler

app_name = 'cms.djangoapps.api.v1'

router = DefaultRouter()
router.register(r'course_runs', CourseRunViewSet, basename='course_run')
urlpatterns = router.urls + [
    url(r'^discussion_settings/{}'.format(settings.COURSE_KEY_PATTERN), discussion_settings_handler, name='discussion_settings')
]
