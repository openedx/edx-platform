import json
import logging
from django.http import HttpResponse
from common.djangoapps.student.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from openedx.core.lib.api.authentication import BearerAuthentication
from openedx.core.lib.api.permissions import IsStaff
from openedx.core.djangoapps.enrollments.views import EnrollmentUserThrottle
from rest_framework import status
from openedx.core.djangoapps.user_api.accounts.api import get_password_validation_error
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.utils.decorators import method_decorator
from rest_framework.exceptions import ValidationError
from openedx.core.djangoapps.user_authn.views.registration_form import AccountCreationForm
from common.djangoapps.student.helpers import do_create_account, AccountValidationError
from .validators import funix_user_validator

def check_missing_fields(fields, data):
    errors = {}
    for field in fields: 
        if data.get(field) is None: 
            errors[field] = ["This field is required"]
    return errors

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

    authentication_classes = []
    # permission_classes = (IsStaff,)
    # throttle_classes = (EnrollmentUserThrottle,)
    @method_decorator(csrf_exempt)
    def post(self, request):
        data = request.data
        email = data.get("email")
        password = data.get("password")
        new_password = data.get("new_password")

        missing_fields = check_missing_fields(["email", "password", "new_password"], data)
        if missing_fields:
            return Response(data={
                "message": "Missing fields",
                "errors": missing_fields
            }, status=status.HTTP_400_BAD_REQUEST)

        password_error = get_password_validation_error(new_password)
        if password_error:
            return Response(data={
                "message": "Invalid new password",
                "errors": {"new_password": [password_error]}
            })

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
                    "message": "Wrong password.",
                    "errors": {"password": ["Wrong password"]}
                }, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response(data={
                 "message": f"Not found user with email '{email}'",
                 "errors": {"email": [f"Not found user with email '{email}'"]}
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e: 
            logging.error(str(e))
            return Response(data={
                "message": "Internal Server Error", 
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CreateUserAPIView(APIView):
    """
    **Use Case**
        Create a single user.

    **Example Request**

        POST http://localhost:18000/api/funix_portal/user/create_user
        Content-Type: application/json
        users: [
            {
                "name": "full name",
                "username": "ntav0010",
                "email": "ntav0009@@@example.com",
                "password": "plain_text"
            }
        ]

    **Example Response**
        {
            "message": "+-Created successfully x users. +-Failed to create y users.",
            "results": [
                {
                    "user": {
                        "name": "full name",
                        "username": "ntav0010",
                        "email": "ntav0009@@@example.com",
                        "password": "plain_text",
                        "student_code": "student_code"
                    },
                    "ok": True/False,
                    "errors": {
                        "field1": ["error1", "error2"],
                    }
                }
            ]
        }

        {
            "message": "Invalid fields",
            "errors": {
                "username": [
                    "User with username 'test0006' already exists."
                ],
                "password": [
                    "Password 'x!' is invalid. Password must be at least 8 characters."
                ]
            }
        }

    """

    authentication_classes = []
    # permission_classes = (IsStaff,)
    # throttle_classes = (EnrollmentUserThrottle,)

    @method_decorator(csrf_exempt)
    def post(self, request):  # lint-amnesty, pylint: disable=missing-function-docstring
        users = request.data

        if type(users) != list: 
            return Response(data={
                "message": "users payload must be an array.",
            }, status=status.HTTP_400_BAD_REQUEST)

        results = []
        users_created = 0

        def _append_results(status, user, errors = {}): 
            results.append({
                "ok": status, 
                "user": user, 
                "errors": errors
            })

        for user in users: 
            if type(user) != dict:
                return Response(data={
                    "message": "Invalid data: user must be a dict.",
                }, status=status.HTTP_400_BAD_REQUEST)
            validation_errors = funix_user_validator.validate(user)
            if validation_errors: 
                return Response(data={
                    "message": "Invalid fields",
                    "errors": validation_errors,
                }, status=status.HTTP_400_BAD_REQUEST)
            
        for user in users: 
            username = user.get('username')
            email = user.get('email')
            password = user.get('password')
            name = user.get('name')

            form = AccountCreationForm(
                data={
                    'username': username,
                    'email': email,
                    'password': password,
                    'name': name,
                },
                tos_required=False
            )

            try:
                new_user, profile, reg = do_create_account(form)
                new_user.is_active = True
                new_user.save()

                student_code = ""
                try:
                    student_code = profile.student_code
                except Exception as e:
                    logging.error(str(e))

                _append_results(True, 
                    {
                        "username": username,
                        "email": email,
                        "name": name,
                        "student_code": student_code
                    }
                )
                users_created += 1
            except ValidationError as e:
                logging.error(str(e))
                # shape of ValidationError: [ "field_name": ["error message"]]
                errors = {}
                for field_error in e:
                    errors[field_error[0]] = field_error[1]
                _append_results(False, user, errors)
            except Exception as e:
                logging.error(str(e))
                _append_results(False, user, {"message": str(e)})

        response_message = ""
        if users_created > 0: 
            response_message += f"Created successfully {users_created} users. "
        if len(results) > users_created:
            response_message += f"Failed to create {len(results) - users_created} users."

        return Response(data={
            "message": response_message,
            "results": results,
        }, status=status.HTTP_200_OK)
