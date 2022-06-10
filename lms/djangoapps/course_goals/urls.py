"""
Course Goals URLs
"""


from django.urls import include, path
from rest_framework import routers

from .views import CourseGoalViewSet

router = routers.DefaultRouter()
router.register(r'course_goals', CourseGoalViewSet, basename='course_goal')

urlpatterns = [
    path('v0/', include((router.urls, "api"), namespace='v0')),
]
