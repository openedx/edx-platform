"""
Coverage Context Listener URLs.
"""
from .views import update_context
from django.urls import path

urlpatterns = [
    path('update_context', update_context),
]
