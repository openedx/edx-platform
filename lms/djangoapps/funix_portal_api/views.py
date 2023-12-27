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
from lms.djangoapps.ora_staff_grader.utils import call_xblock_json_handler, is_json
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

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

                student_code = profile.student_code
                if not student_code:
                    student_code = email.split('@')[0]
                    profile.student_code = student_code
                    profile.save()

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



class GradeLearningProjectXblockAPIView(APIView): 
    """
    **Use Case**
        Grade a student's learning project. Just grade if 'result' is 'passed' or 'did_not_pass'.

    **Example Request**
        POST http://localhost:18000/api/funix_portal/project/grade_project
        Content-Type: application/json

        {
            "project_name":  "project",
            "course_code":"course-v1:o1+c1+r1",
            "email": "edx@example.com",
            "result": "did_not_pass"
        }

    **Example Response**
        - 200: 
        {
            "message": "Graded"
        }

        - 400, 500: 
        {
            "message": "error message"
        }
    """

    authentication_classes = []
    # permission_classes = (IsStaff,)
    # throttle_classes = (EnrollmentUserThrottle,)
    @method_decorator(csrf_exempt)
    def post(self, request):

        data = request.data
        course_code = data.get('course_code')
        project_name = data.get('project_name')
        email = data.get('email')
        result = data.get('result')

        if not course_code:
            return Response(data={
                 "message": "Missing course_code",
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not email:
            return Response(data={
                 "message": "Missing email",
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not project_name:
            return Response(data={
                 "message": "Missing project_name",
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not result:
            return Response(data={
                 "message": "Missing result",
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if result not in ['passed', 'did_not_pass']:
            return Response(data={
                 "message": "This result will not be took into account. The result value must be 'passed' or 'did_not_pass'",
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            student = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(data={
                 "message": f"Not found student with email '{email}'",
            }, status=status.HTTP_400_BAD_REQUEST)


        usage_id = ''
        found_learningprojectxblock = False
        found_learningproject = False
        try:
            course_overview = CourseOverview.get_from_id(course_code)
            print(course_overview)
            if not course_overview:
                return Response(data={
                    "message": f"Not found course with course_code '{course_code}'",
                }, status=status.HTTP_400_BAD_REQUEST)
        
            course = course_overview._original_course
            sections = course.get_children()

            for section in sections:
                subsections = section.get_children()
                for sub in subsections:
                    if sub.display_name == project_name:
                        found_learningproject = True
                        units = sub.get_children()
                        for unit in units:
                            components = unit.get_children()
                            for component in components:
                                if type(component).__name__ == 'AssignmentXBlockWithMixins':
                                    if (component.has_score):
                                        found_learningprojectxblock = True
                                        usage_id = str(component.scope_ids.usage_id)
                                        break

        except Exception as e:
            logging.error(str(e))
            return Response(data={
                "message": f"Could not load course with course_code '{course_code}'",
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if not found_learningproject:
            return Response(data={
                 "message": f"Not found learning project '{project_name}'",
            }, status=status.HTTP_400_BAD_REQUEST)

        if not found_learningprojectxblock:
            return Response(data={
                 "message": f"Not found learningprojectxblock in learning project '{project_name}'",
            }, status=status.HTTP_400_BAD_REQUEST)

        if usage_id == '':
            return Response(data={
                 "message": "Not found usage_id",
            }, status=status.HTTP_400_BAD_REQUEST)

        
        req = request
        req.user = student

        try:
            response = call_xblock_json_handler(req, usage_id, "portal_grade", {"result": result})
        except Exception as e:
            logging.error(str(e))
            error_message = str(e) if str(e) != '' else "Internal Server Error"
            return Response(data={
                "message": error_message,
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if response.status_code != 200:
            details = (
                json.loads(response.content).get("error", "")
                if is_json(response.content)
                else ""
            )
            logging.error(details)
            response_message = details or "Internal Server Error"
            return Response(data={
                "message": response_message,
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


        return Response(data={
            "message": "Graded",
        }, status=status.HTTP_200_OK)