"""
URLs for genplus learning API v1.
"""
from django.conf.urls import url
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ProgramViewSet,
    ClassStudentViewSet,
    ClassSummaryViewSet,
    StudentDashboardAPIView
)

router = DefaultRouter()
router.register('lessons', ProgramViewSet, basename='lessons')
router.register('class-summary', ClassSummaryViewSet, basename='class-summary')


app_name = 'genplus_learning_api_v1'

urlpatterns = [
    url(r'^class-students/(?P<group_id>\w+)/$', ClassStudentViewSet.as_view({'get': 'list'})),
    url(r'^student-dashboard/$', StudentDashboardAPIView.as_view()),
    url(r'^class-summary/lesson/unlock/(?P<lesson_id>\d+)/$', ClassSummaryViewSet.as_view({"put": "unlock_lesson"})),
    path('', include(router.urls)),
]
