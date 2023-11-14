import json
import logging
from django.http import HttpResponse, HttpResponseNotFound
from django.http import JsonResponse
from openedx.core.djangoapps.user_authn.views.registration_form import AccountCreationForm
from common.djangoapps.student.helpers import (
    AccountValidationError,
    authenticate_new_user,
    create_or_set_user_attribute_created_on_site,
    do_create_account
)

from common.djangoapps.student.models import (  # lint-amnesty, pylint: disable=unused-import
    CourseEnrollmentAllowed,
    LoginFailures,
    ManualEnrollmentAudit,
    PendingEmailChange,
    PendingNameChange,
    User,
    UserProfile,
    get_potentially_retired_user_by_username,
    get_retired_email_by_email,
    get_retired_username_by_username,
    is_email_retired,
    is_username_retired
)

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from common.djangoapps.student.models import CourseEnrollment, CourseFullError, AlreadyEnrolledError, EnrollmentClosedError
from openedx.core.lib.courses import get_course_by_id
from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError
from django.urls.exceptions import NoReverseMatch

# refactor
from rest_framework.views import APIView
from rest_framework.response import Response
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from openedx.core.lib.api.authentication import BearerAuthentication
from openedx.core.lib.api.permissions import IsStaff
from openedx.core.djangoapps.enrollments.views import EnrollmentUserThrottle
from rest_framework import status
from django.core.validators import ValidationError

class CreateUserAPIView(APIView):
    """
    **Use Case**
        Create a single user.

    **Example Request**

        POST http://localhost:18000/api/funix_portal/user/create_user
        Content-Type: application/json

        {
            "full_name": "",
            "username": "ntav0010",
            "email": "ntav0009@@@example.com",
            "password": "Anhvu123456!"
        }

    **Example Response**
        {
            "message": "success/error message",
            if message is Validation Error, extra field:
            "errors": [ 
                [ "email", ["A properly formatted e-mail is required"] ],
                [ "name", ["Your legal name must be a minimum of one character long"] ]
            ]
        }

    """

    # authentication_classes = (JwtAuthentication, BearerAuthentication,)
    # permission_classes = (IsStaff,)
    # throttle_classes = (EnrollmentUserThrottle,)

    def post(self, request):  # lint-amnesty, pylint: disable=missing-function-docstring
        data = request.data

        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        full_name = data.get('full_name')

        if username is None or email is None or password is None or full_name is None:
            return Response(data={
                "message": f"Missing field. Required fields: username, email, password, full_name"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            return Response(data={
                "message": f"User with email {email} already exists"
            }, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            pass
        except Exception as e: 
            logging.error(str(e))
            return Response(data={
                "message": "Internal Server Error", 
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            user = User.objects.get(username=username)
            return Response(data={
                "message": f"User with username {username} already exists"
            }, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist: 
            pass
        except Exception as e: 
            logging.error(str(e))
            return Response(data={
                "message": "Internal Server Error", 
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        form = AccountCreationForm(
            data={
                'username': username,
                'email': email,
                'password': password,
                'name': full_name,
            },
            tos_required=False
        )

        try:
            user, profile, reg = do_create_account(form)
            user.is_active = True
            user.save()

            return Response(data={
                "message":  "success",
            }, status=status.HTTP_200_OK)
        except ValidationError as e:
            logging.error(str(e))
            return Response(data={
                "message": "Validation Error", 
                "errors": e,
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logging.error(str(e))
            return Response(data={
                "message": "Internal Server Error", 
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UpdateUserPasswordAPIView(APIView): 
    """
    **Use Case**
        Update user password

    **Example Request**
        POST http://localhost:18000/api/funix_portal/user/update_password
        Content-Type: application/json

        {
            "email": "example@example.com",
            "password": "current_password",
            "new_password": "new_password"
        }

    **Example Response**
    
        {
            "message": "Updated new password/error message"
        }
    """

    # authentication_classes = (JwtAuthentication, BearerAuthentication,)
    # permission_classes = (IsStaff,)
    # throttle_classes = (EnrollmentUserThrottle,)
    def post(self, request):
        data = request.data
        email = data.get("email")
        password = data.get("password")
        new_password = data.get("new_password")

        if email is None or password is None or new_password is None:
            return Response(data={
                "message": f"Missing field. Required fields: email, password, new_password"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            password_matches = user.check_password(password)
            if password_matches: 
                try:
                    user.set_password(new_password)
                    user.save()
                    return Response(data={
                        "message": "Updated new password"
                    }, status=status.HTTP_200_OK)
                except Exception as e:
                    logging.error(str(e))
                    return Response(data={
                        "message": "Internal Server Error", 
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return Response(data={
                    "message": "Wrong password."
                }, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response(data={
                 "message": f"Not found user with email {email}"
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e: 
            logging.error(str(e))
            return Response(data={
                "message": "Internal Server Error", 
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

