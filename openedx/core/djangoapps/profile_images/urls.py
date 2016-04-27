"""
Defines the URL routes for this app.

NOTE: These views are deprecated.  These routes are superseded by
``/api/user/v1/accounts/{username}/image``, found in
``openedx.core.djangoapps.user_api.urls``.
"""

from django.conf.urls import patterns, url

from .views import ProfileImageUploadView, ProfileImageRemoveView

USERNAME_PATTERN = r'(?P<username>[\w.+-]+)'

urlpatterns = patterns(
    '',
    url(
        r'^v1/' + USERNAME_PATTERN + '/upload$',
        ProfileImageUploadView.as_view(),
        name="profile_image_upload"
    ),
    url(
        r'^v1/' + USERNAME_PATTERN + '/remove$',
        ProfileImageRemoveView.as_view(),
        name="profile_image_remove"
    ),
)
