"""
URLs for save_for_later v1
"""

from django.urls import re_path

from lms.djangoapps.save_for_later.api.v1.views import CourseSaveForLaterApiView, ProgramSaveForLaterApiView

urlpatterns = [
    re_path(r'^save/program/$', ProgramSaveForLaterApiView.as_view(), name='save_program'),
    re_path(r'^save/course/$', CourseSaveForLaterApiView.as_view(), name='save_course'),
]
