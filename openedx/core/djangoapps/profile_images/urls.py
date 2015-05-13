"""
Defines the URL routes for this app.
"""
from .views import ProfileImageUploadView, ProfileImageRemoveView

from django.conf.urls import patterns, url
from django.conf import settings


urlpatterns = patterns(
    '',
    url(
        r'^v1/' + settings.USERNAME_PATTERN + '/upload$',
        ProfileImageUploadView.as_view(),
        name="profile_image_upload"
    ),
    url(
        r'^v1/' + settings.USERNAME_PATTERN + '/remove$',
        ProfileImageRemoveView.as_view(),
        name="profile_image_remove"
    ),
)
