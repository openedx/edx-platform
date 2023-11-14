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

    # authentication_classes = (JwtAuthentication, BearerAuthentication,)
    # permission_classes = (IsStaff,)
    # throttle_classes = (EnrollmentUserThrottle,)
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

