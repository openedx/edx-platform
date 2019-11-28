"""
Coverage Context Listener URLs.
"""
from django.conf.urls import url
from .views import update_context

urlpatterns = [
    url(r'update_context', update_context),
]
