"""
This module implements the upload and remove endpoints of the profile image api.
"""
from contextlib import closing

from rest_framework import permissions, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView

from openedx.core.lib.api.authentication import (
    OAuth2AuthenticationAllowInactiveUser,
    SessionAuthenticationAllowInactiveUser,
)
from openedx.core.lib.api.permissions import IsUserInUrl, IsUserInUrlOrStaff
from ..user_api.accounts.api import set_has_profile_image, get_profile_image_names
from .images import validate_uploaded_image, create_profile_images, remove_profile_images, ImageValidationError


class ProfileImageUploadView(APIView):
    """
    Provides a POST endpoint to generate new profile image files for a given
    user, using an uploaded source image.
    """
    parser_classes = (MultiPartParser, FormParser,)

    authentication_classes = (OAuth2AuthenticationAllowInactiveUser, SessionAuthenticationAllowInactiveUser)
    permission_classes = (permissions.IsAuthenticated, IsUserInUrl)

    def post(self, request, username):
        """
        HTTP POST handler.
        """
        # validate request:
        # ensure any file was sent
        if 'file' not in request.FILES:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # process the upload.
        uploaded_file = request.FILES['file']

        # no matter what happens, delete the temporary file when we're done
        with closing(uploaded_file):

            # image file validation.
            try:
                validate_uploaded_image(uploaded_file)
            except ImageValidationError, exc:
                return Response(
                    {"developer_message": exc.message, "user_message": exc.user_message},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # generate profile pic and thumbnails and store them
            create_profile_images(uploaded_file, get_profile_image_names(username))

            # update the user account to reflect that a profile image is available.
            set_has_profile_image(username, True)

        # send client response.
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProfileImageRemoveView(APIView):
    """
    Provides a POST endpoint to delete all profile image files for a given user
    """
    authentication_classes = (OAuth2AuthenticationAllowInactiveUser, SessionAuthenticationAllowInactiveUser)
    permission_classes = (permissions.IsAuthenticated, IsUserInUrlOrStaff)

    def post(self, request, username):  # pylint: disable=unused-argument
        """
        HTTP POST handler.
        """
        # update the user account to reflect that the images were removed.
        set_has_profile_image(username, False)

        # remove physical files from storage.
        remove_profile_images(get_profile_image_names(username))

        # send client response.
        return Response(status=status.HTTP_204_NO_CONTENT)
