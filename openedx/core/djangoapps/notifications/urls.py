from django.urls import path
from rest_framework import routers
from .views import CourseEnrollmentListView

app_name = 'openedx.core.djangoapps.notifications'

router = routers.DefaultRouter()

urlpatterns = [
    path('enrollments/', CourseEnrollmentListView.as_view(), name='enrollment-list'),
]

urlpatterns += router.urls
