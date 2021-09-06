"""
Course Goals URLs
"""


from django.conf.urls import include, url
from rest_framework import routers

from .views import CourseGoalViewSet

router = routers.DefaultRouter()
router.register(r'course_goals', CourseGoalViewSet, basename='course_goal')

urlpatterns = [
    url(r'^v0/', include((router.urls, "api"), namespace='v0')),
]
