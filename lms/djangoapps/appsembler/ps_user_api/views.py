import logging

from django.core.exceptions import NON_FIELD_ERRORS, ValidationError

from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response

from openedx.core.djangoapps.user_api.accounts.api import check_account_exists, get_account_settings
from openedx.core.djangoapps.user_api.errors import UserNotFound
from student.views import create_account_with_params


from openedx.core.lib.api.authentication import (
    OAuth2AuthenticationAllowInactiveUser,
)
from openedx.core.lib.api.permissions import IsStaffOrOwner


log = logging.getLogger(__name__)


class CreateUserAccountView(APIView):
    authentication_classes = OAuth2AuthenticationAllowInactiveUser,
    permission_classes = IsStaffOrOwner,


    def post(self, request):
        """
        Creates a new user account
        URL: /api/ps_user_api/v1/accounts/create
        Arguments:
            request (HttpRequest)
            JSON (application/json)
            {
                "username": "staff4",
                "password": "edx",
                "email": "staff4@example.com",
                "name": "stafftest"
            }
        Returns:
            HttpResponse: 200 on success, {"user_id ": 9, "success": true }
            HttpResponse: 400 if the request is not valid.
            HttpResponse: 409 if an account with the given username or email
                address already exists
        """
        data = request.data

        # set the honor_code and honor_code like checked,
        # so we can use the already defined methods for creating an user
        data['honor_code'] = "True"
        data['terms_of_service'] = "True"

        email = request.data.get('email')
        username = request.data.get('username')

        # Handle duplicate email/username
        conflicts = check_account_exists(email=email, username=username)
        if conflicts:
            errors = {"user_message": "User already exists"}
            return Response(errors, status=409)

        try:
            user = create_account_with_params(request, data)
            # set the user as active
            user.is_active = True
            user.save()
            user_id = user.id
        except ValidationError as err:
            # Should only get non-field errors from this function
            assert NON_FIELD_ERRORS not in err.message_dict
            # Only return first error for each field
            errors = {"user_message": "Wrong parameters on user creation"}
            return Response(errors, status=400)

        response = Response({'user_id ': user_id }, status=200)
        return response


class GetUserAccountView(APIView):
    authentication_classes = OAuth2AuthenticationAllowInactiveUser,
    permission_classes = IsStaffOrOwner,

    def get(self, request, username):
        """
        check if a user exists based in the username

        URL: /api/ps_user_api/v1/accounts/{username}
        Args:
            username: the username you are looking for

        Returns:
            200 OK and the user id
            404 NOT_FOUND if the user doesn't exists

        """
        try:
            account_settings = get_account_settings(request, username, view=request.query_params.get('view'))
        except UserNotFound:
            return Response(
                status=status.HTTP_404_NOT_FOUND
            )

        return Response({'user_id': account_settings['username']}, status=200)