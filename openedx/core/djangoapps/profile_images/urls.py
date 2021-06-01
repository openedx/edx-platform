# pylint: disable=unicode-format-string
"""
Defines the URL routes for this app.

NOTE: These views are deprecated.  These routes are superseded by
``/api/user/v1/accounts/{username}/image``, found in
``openedx.core.djangoapps.user_api.urls``.
"""
# pylint: enable=unicode-format-string


from django.conf import settings
from django.conf.urls import url

from .views import ProfileImageRemoveView, ProfileImageUploadView

urlpatterns = [
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
]
