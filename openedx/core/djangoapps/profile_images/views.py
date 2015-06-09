"""
This module implements the upload and remove endpoints of the profile image api.
"""
from contextlib import closing
import datetime
import logging

from django.utils.translation import ugettext as _
from django.utils.timezone import utc
from rest_framework import permissions, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView

from openedx.core.djangoapps.user_api.errors import UserNotFound
from openedx.core.lib.api.authentication import (
    OAuth2AuthenticationAllowInactiveUser,
    SessionAuthenticationAllowInactiveUser,
)
from openedx.core.lib.api.permissions import IsUserInUrl, IsUserInUrlOrStaff
from openedx.core.djangoapps.user_api.accounts.image_helpers import get_profile_image_names, set_has_profile_image
from .images import validate_uploaded_image, create_profile_images, remove_profile_images, ImageValidationError

log = logging.getLogger(__name__)

LOG_MESSAGE_CREATE = 'Generated and uploaded images %(image_names)s for user %(user_id)s'
LOG_MESSAGE_DELETE = 'Deleted images %(image_names)s for user %(user_id)s'


def _make_upload_dt():
    """
    Generate a server-side timestamp for the upload.  This is in a separate
    function so its behavior can be overridden in tests.
    """
    return datetime.datetime.utcnow().replace(tzinfo=utc)


class ProfileImageUploadView(APIView):
    """
    **Use Cases**

        Upload an image to be used for the user's profile.

        The requesting user must be signed in. The signed in user can only
        upload his or her own profile image.

    **Example Requests**

        POST /api/profile_images/v1/{username}/upload

    **Response for POST**

        If the requesting user tries to upload the image for a different user:

        * If the requesting user has staff access, the request returns a 403
          error.

        * If the requesting user does not have staff access, the request returns
          a 404 error.

        If no user matches the "username" parameter, the request returns a 404
        error.

        If the upload could not be performed, the request returns a 400 error is
        with details.

        If the upload is successful, the request returns a 204 status with no
        additional content.

    """
    parser_classes = (MultiPartParser, FormParser,)

    authentication_classes = (OAuth2AuthenticationAllowInactiveUser, SessionAuthenticationAllowInactiveUser)
    permission_classes = (permissions.IsAuthenticated, IsUserInUrl)

    def post(self, request, username):
        """
        POST /api/profile_images/v1/{username}/upload
        """
        # validate request:
        # verify that the user's
        # ensure any file was sent
        if 'file' not in request.FILES:
            return Response(
                {
                    "developer_message": u"No file provided for profile image",
                    "user_message": _(u"No file provided for profile image"),

                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # process the upload.
        uploaded_file = request.FILES['file']

        # no matter what happens, delete the temporary file when we're done
        with closing(uploaded_file):

            # image file validation.
            try:
                validate_uploaded_image(uploaded_file)
            except ImageValidationError as error:
                return Response(
                    {"developer_message": error.message, "user_message": error.user_message},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # generate profile pic and thumbnails and store them
            profile_image_names = get_profile_image_names(username)
            create_profile_images(uploaded_file, profile_image_names)

            # update the user account to reflect that a profile image is available.
            set_has_profile_image(username, True, _make_upload_dt())

            log.info(
                LOG_MESSAGE_CREATE,
                {'image_names': profile_image_names.values(), 'user_id': request.user.id}
            )

        # send client response.
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProfileImageRemoveView(APIView):
    """
    **Use Cases**

        Remove all of the profile images associated with the user's account.

        The requesting user must be signed in.

        Users with staff access can remove profile images for other user
        accounts.

        Users without staff access can only remove their own profile images.

    **Example Requests**

        POST /api/profile_images/v1/{username}/remove

    **Response for POST**

        Requesting users who do not have staff access and try to remove another
        user's profile image receive a 404 error.

        If no user matches the "username" parameter, the request returns a 404
        error.

        If the request could not remove the image, the request returns a 400
        error with details.

        If the request successfully removes the image, the request returns a 204
        status with no additional content.

    """
    authentication_classes = (OAuth2AuthenticationAllowInactiveUser, SessionAuthenticationAllowInactiveUser)
    permission_classes = (permissions.IsAuthenticated, IsUserInUrlOrStaff)

    def post(self, request, username):  # pylint: disable=unused-argument
        """
        POST /api/profile_images/v1/{username}/remove
        """
        try:
            # update the user account to reflect that the images were removed.
            set_has_profile_image(username, False)

            # remove physical files from storage.
            profile_image_names = get_profile_image_names(username)
            remove_profile_images(profile_image_names)

            log.info(
                LOG_MESSAGE_DELETE,
                {'image_names': profile_image_names.values(), 'user_id': request.user.id}
            )
        except UserNotFound:
            return Response(status=status.HTTP_404_NOT_FOUND)

        # send client response.
        return Response(status=status.HTTP_204_NO_CONTENT)
