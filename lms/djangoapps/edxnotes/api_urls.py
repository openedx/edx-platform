"""
API URLs for EdxNotes
"""


from django.conf.urls import url

from edxnotes import views

urlpatterns = [
    url(r"^retire_user/$", views.RetireUserView.as_view(), name="edxnotes_retire_user"),
]
