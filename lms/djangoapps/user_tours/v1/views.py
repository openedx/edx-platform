""" API for User Tours. """

from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from lms.djangoapps.user_tours.models import UserTour
from lms.djangoapps.user_tours.v1.serializers import UserTourSerializer


class UserTourView(RetrieveUpdateAPIView):
    """
    Supports retrieving and patching the UserTour model

    **Example Requests**

        GET /api/user_tours/v1/{username}
        PATCH /api/user_tours/v1/{username}
    """
    authentication_classes = (JwtAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = UserTourSerializer

    def get(self, request, username):  # pylint: disable=arguments-differ
        """
        Retrieve the User Tour for the given username.

        Allows staff users to retrieve any user's User Tour.

        Returns
            200 with the following fields:
                course_home_tour_status (str): one of UserTour.CourseHomeChoices
                show_courseware_tour (bool): indicates if courseware tour should be shown.

            400 if there is a not allowed request (requesting a user you don't have access to)
            401 if unauthorized request
            403 if waffle flag is not enabled
            404 if the UserTour does not exist (shouldn't happen, but safety first)
        """
        if request.user.username != username and not request.user.is_staff:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        try:
            user_tour = UserTour.objects.get(user__username=username)
        # Should never really happen, but better safe than sorry.
        except UserTour.DoesNotExist as e:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(self.get_serializer_class()(user_tour).data, status=status.HTTP_200_OK)

    def patch(self, request, username):  # pylint: disable=arguments-differ
        """
        Patch the User Tour for the request.user.

        Supports updating the `course_home_tour_status` and `show_courseware_tour` fields.

        Returns:
            200 response if update was successful

            400 if update was unsuccessful or there was nothing to update
            401 if unauthorized request
            403 if waffle flag is not enabled
        """
        if request.user.username != username:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated = UserTour.objects.filter(user__username=username).update(**serializer.validated_data)
        if updated:
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    def put(self, *_args, **_kwargs):
        """ Unsupported method. """
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
