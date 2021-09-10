"""
URLs for EdxNotes.
"""

from . import views
from django.urls import path

# Additionally, we include login URLs for the browseable API.
urlpatterns = [
    path('', views.edxnotes, name="edxnotes"),
    path('notes/', views.notes, name="notes"),
    path('token/', views.get_token, name="get_token"),
    path('visibility/', views.edxnotes_visibility, name="edxnotes_visibility"),
]
