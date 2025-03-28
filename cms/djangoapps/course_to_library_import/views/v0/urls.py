"""
Course to Library Import API v0 URLs.
"""

from django.urls import path

from .views import (
    CreateCourseToLibraryImportView,
    ImportBlocksView,
    GetCourseStructureToLibraryImportView,
)

app_name = 'v0'
urlpatterns = [
    path('import_blocks/', ImportBlocksView.as_view(), name='import_blocks'),
    path('create_import/<str:content_library_id>/', CreateCourseToLibraryImportView.as_view(), name='create_import'),
    path('get_import/<uuid:course_to_lib_uuid>/', GetCourseStructureToLibraryImportView.as_view(), name='get_import'),
]
