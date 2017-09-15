"""
Course Goals API URLs
"""
from django.conf.urls import include, patterns, url
from rest_framework import routers

from .views import CourseGoalViewSet

router = routers.DefaultRouter()
router.register(r'course_goal', CourseGoalViewSet, base_name='course_goal_base')

urlpatterns = patterns(
    '',
    url(r'^api/v0/', include(router.urls, namespace='course_goal_api')),
)
