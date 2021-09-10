"""
Defines the URL routes for this app.
"""

from . import views
from django.urls import path

app_name = 'catalog'
urlpatterns = [
    path('management/cache_programs/', views.cache_programs, name='cache_programs'),
]
