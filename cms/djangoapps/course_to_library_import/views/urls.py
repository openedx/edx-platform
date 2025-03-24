"""
Course to Library Import API URLs.
"""

from django.urls import include, path

app_name = 'course_to_library_import'
urlpatterns = [
    path('v0/', include('cms.djangoapps.course_to_library_import.views.v0.urls', namespace='v0')),
]
