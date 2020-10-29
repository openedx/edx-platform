"""
URLs for the Studio API [Course Run]
"""

from __future__ import absolute_import

from rest_framework.routers import DefaultRouter

from .views.course_runs import CourseRunViewSet

router = DefaultRouter()
router.register(r'course_runs', CourseRunViewSet, base_name='course_run')
urlpatterns = router.urls
