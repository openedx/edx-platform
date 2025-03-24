"""
Course to Library Import API v0 URLs.
"""

from django.urls import path

from .views import ImportBlocksView

app_name = 'v0'
urlpatterns = [
    path('import_blocks/', ImportBlocksView.as_view(), name='import_blocks'),
]
