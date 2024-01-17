import json
import logging
from django.http import HttpResponse,JsonResponse, HttpResponseNotFound, HttpResponseNotAllowed, HttpResponseBadRequest
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
from opaque_keys.edx.keys import UsageKey, CourseKey
from opaque_keys import InvalidKeyError
from xmodule.modulestore.exceptions import ItemNotFoundError, NoPathToItem
from openedx.features.course_experience.url_helpers import get_courseware_url
from common.djangoapps.util.course import course_location_from_key
from django.conf import settings
import requests
from django.contrib.staticfiles import finders
import mimetypes
from openedx.core.djangoapps.site_configuration.models import SiteConfiguration



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
    
def get_portal_host(request):
    from django.contrib.sites.models import Site

    def get_site_config(domain, setting_name, default_value=None):
        try:
            site = Site.objects.filter(domain=domain).first()
            if site is None: 
                print('NOT FOUND SITE')
                return default_value
            site_config = SiteConfiguration.objects.filter(site=site).first()
            if site_config is None:
                print('NOT FOUND SITE CONFIG')
                return default_value

            return site_config.get_value(setting_name, default_value)
        except Exception as e:
            print(str(e))
            return None

    LMS_BASE = settings.LMS_BASE
    PORTAL_HOST = get_site_config(LMS_BASE, 'PORTAL_HOST') 
    return  JsonResponse( {
            'HOST':PORTAL_HOST
            }
        ,
        status=200)

def get_resume_path(request, course_id, location):

    try:
        course_key = CourseKey.from_string(course_id)
        usage_key = UsageKey.from_string(location).replace(course_key=course_key)
    except InvalidKeyError as exc:
        return  JsonResponse({
                'message': 'Invalid usage key or course key.'
            }
            ,
            status=400
        )

    try:
        redirect_url = get_courseware_url(
            usage_key=usage_key,
            request=request,
        )
    except (ItemNotFoundError, NoPathToItem):
        # We used to 404 here, but that's ultimately a bad experience. There are real world use cases where a user
        # hits a no-longer-valid URL (for example, "resume" buttons that link to no-longer-existing block IDs if the
        # course changed out from under the user). So instead, let's just redirect to the beginning of the course,
        # as it is at least a valid page the user can interact with...
        redirect_url = get_courseware_url(
            usage_key=course_location_from_key(course_key),
            request=request,
        )

    return  JsonResponse({
            'message': 'Success',
            'data': {
                'redirect_url': redirect_url
            },
        }
        ,
        status=200
    )

def funix_get_thumb(request):
    FALLBACK_COURSE_IMAGE_PATH = 'images/default_course_thumb.png'
    FALLBACK_DEFAULT_PATH = 'images/image_error.png'

    if request.method != 'GET':
        return HttpResponseNotAllowed('Not allowed method.')
    
    img_path = request.GET['path']

    if not img_path: 
        logging.error('From funix_get_thumb: Missing img_path.')
        return HttpResponseBadRequest('Missing img_path')
    
    try:
        ext = img_path.split('.')[-1]
    except:
        logging.error('From funix_get_thumb: Missing image extension.')
        return HttpResponseBadRequest('Invalid image path: missing extension.')

    schema = 'https://' if settings.HTTPS == 'on' else 'http://'
    img_url = f"{schema}{settings.LMS_BASE}/{img_path}"

    response = requests.get(img_url)

    if response.status_code == 200:
        mimetype = _get_mime_type(ext)
        return HttpResponse(response.content, content_type=mimetype)
    else: 
        logging.error(f'From funix_get_thumb: image_path: {img_path}. img_url: {img_url}. status code: {response.status_code}')

    fallback_path = FALLBACK_DEFAULT_PATH

    if request.GET.get('type') == 'course_thumb':
        fallback_path = FALLBACK_COURSE_IMAGE_PATH
    
    fallback_img_path = finders.find(fallback_path)

    if fallback_img_path:
        with open(fallback_img_path, 'rb') as f:
            image_data = f.read()
            mimetype = _get_mime_type(fallback_img_path.split('.')[-1])
            return HttpResponse(image_data, content_type=mimetype)
    else:
        return HttpResponseNotFound("Image not found.")
    
def _get_mime_type(extension):
    mime_type, _ = mimetypes.guess_type(f"dummy.{extension}")
    return mime_type
    