"""
URLs for the Studio API [Course Run]
"""

from rest_framework.routers import DefaultRouter

from .views.course_runs import CourseRunViewSet
from .views.discussion_settings import DiscussionSettingsViewSet

app_name = 'cms.djangoapps.api.v1'

router = DefaultRouter()
router.register(r'course_runs', CourseRunViewSet, basename='course_run')
router.register(r'discussion_settings', DiscussionSettingsViewSet, base_name='discussion_settings')
urlpatterns = router.urls
