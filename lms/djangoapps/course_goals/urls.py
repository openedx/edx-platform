"""
Course Goals URLs
"""
from django.conf.urls import include, url
from rest_framework import routers

from .views import CourseGoalViewSet

router = routers.DefaultRouter()
router.register(r'course_goals', CourseGoalViewSet, base_name='course_goal')

app_name = 'course_goals'
urlpatterns = [
    url(r'^v0/', include(router.urls, namespace='v0')),
]
