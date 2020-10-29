"""
URLs for EdxNotes.
"""
from __future__ import absolute_import

from django.conf.urls import url

from edxnotes import views

# Additionally, we include login URLs for the browseable API.
urlpatterns = [
    url(r"^$", views.edxnotes, name="edxnotes"),
    url(r"^notes/$", views.notes, name="notes"),
    url(r"^token/$", views.get_token, name="get_token"),
    url(r"^visibility/$", views.edxnotes_visibility, name="edxnotes_visibility"),
]
