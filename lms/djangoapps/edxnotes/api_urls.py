"""
API URLs for EdxNotes
"""

from lms.djangoapps.edxnotes import views
from django.urls import path

urlpatterns = [
    path('retire_user/', views.RetireUserView.as_view(), name="edxnotes_retire_user"),
]
