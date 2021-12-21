"""
URLs for save_for_later v1
"""

from django.urls import path

from lms.djangoapps.save_for_later.api.v1.views import SaveForLaterApiView

urlpatterns = [
    path('save/course/', SaveForLaterApiView.as_view(), name='save_course'),
]
