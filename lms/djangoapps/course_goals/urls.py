"""
Course Goals URLs
"""


from django.conf.urls import include
from rest_framework import routers

from .views import CourseGoalViewSet
from django.urls import path

router = routers.DefaultRouter()
router.register(r'course_goals', CourseGoalViewSet, basename='course_goal')

urlpatterns = [
    path('v0/', include((router.urls, "api"), namespace='v0')),
]
