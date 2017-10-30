"""
URLs for EdxNotes.
"""
from django.conf.urls import url

from edxnotes.views import edxnotes, notes, get_token, edxnotes_visibility

# Additionally, we include login URLs for the browseable API.
urlpatterns = [
    url(r"^/$", edxnotes, name="edxnotes"),
    url(r"^/notes/$", notes, name="notes"),
    url(r"^/token/$", get_token, name="get_token"),
    url(r"^/visibility/$", edxnotes_visibility, name="edxnotes_visibility"),
]
