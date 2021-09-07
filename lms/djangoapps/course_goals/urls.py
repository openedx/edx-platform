"""
Course Goals URLs
"""


from django.conf.urls import include, url
from rest_framework import routers

from .views import CourseGoalViewSet, PopulateUserActivity

router = routers.DefaultRouter()
router.register(r'course_goals', CourseGoalViewSet, basename='course_goal')

urlpatterns = [
    url(r'^v0/', include((router.urls, "api"), namespace='v0')),
    url(r'^populate_user_activity$', PopulateUserActivity.as_view(), name='populate_user_activity'),
]
