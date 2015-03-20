"""
This module implements the upload and remove endpoints of the profile image api.
"""
from contextlib import closing
import logging

from django.utils.translation import ugettext as _
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
from openedx.core.djangoapps.user_api.accounts.api import set_has_profile_image, get_profile_image_names
from .images import validate_uploaded_image, create_profile_images, remove_profile_images, ImageValidationError

log = logging.getLogger(__name__)

LOG_MESSAGE_CREATE = 'Generated and uploaded images %(image_names)s for user %(user_id)s'
LOG_MESSAGE_DELETE = 'Deleted images %(image_names)s for user %(user_id)s'


class ProfileImageUploadView(APIView):
    """
    **Use Cases**

        Uploads an image to be used for the user's profile.

    **Example Requests**:

        POST /api/profile_images/v0/{username}/upload

    **Response for POST**

        Users can only upload their own profile image. If the requesting user does not have username
        "username", this method will return with a status of 403 for staff access but a 404 for ordinary
        users to avoid leaking the existence of the account.

        This method will also return a 404 if no user exists with username "username".

        If the upload could not be performed then this method returns a 400 with specific errors
        in the returned JSON.

        If the update is successful, a 204 status is returned with no additional content.

    """
    parser_classes = (MultiPartParser, FormParser,)

    authentication_classes = (OAuth2AuthenticationAllowInactiveUser, SessionAuthenticationAllowInactiveUser)
    permission_classes = (permissions.IsAuthenticated, IsUserInUrl)

    def post(self, request, username):
        """
        POST /api/profile_images/v0/{username}/upload
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

        try:
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
                set_has_profile_image(username, True)

                log.info(
                    LOG_MESSAGE_CREATE,
                    {'image_names': profile_image_names.values(), 'user_id': request.user.id}
                )
        except Exception as error:
            return Response(
                {
                    "developer_message": u"Upload failed for profile image: {error}".format(error=error),
                    "user_message": _(u"Upload failed for profile image"),

                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # send client response.
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProfileImageRemoveView(APIView):
    """
    **Use Cases**

        Removes all of the profile images associated with the user's account.

    **Example Requests**:

        POST /api/profile_images/v0/{username}/remove

    **Response for POST**

        Users are authorized to delete their own profile images, while staff can delete images for
        any account. All other users will receive a 404 to avoid leaking the existence of the account.

        This method will also return a 404 if no user exists with username "username".

        If the delete could not be performed then this method returns a 400 with specific errors
        in the returned JSON.

        If the delete is successful, a 204 status is returned with no additional content.

    """
    authentication_classes = (OAuth2AuthenticationAllowInactiveUser, SessionAuthenticationAllowInactiveUser)
    permission_classes = (permissions.IsAuthenticated, IsUserInUrlOrStaff)

    def post(self, request, username):  # pylint: disable=unused-argument
        """
        POST /api/profile_images/v0/{username}/remove
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
        except Exception as error:
            return Response(
                {
                    "developer_message": u"Delete failed for profile image: {error}".format(error=error),
                    "user_message": _(u"Delete failed for profile image"),

                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # send client response.
        return Response(status=status.HTTP_204_NO_CONTENT)
