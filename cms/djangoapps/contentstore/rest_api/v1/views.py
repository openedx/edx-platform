"Contentstore Views"
import copy

import edx_api_doc_tools as apidocs
from django.conf import settings
from django.core.exceptions import ValidationError
from common.djangoapps.util.json_request import JsonResponseBadRequest
from opaque_keys.edx.keys import CourseKey
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from cms.djangoapps.contentstore.views.course import get_course_and_check_access
from cms.djangoapps.models.settings.course_grading import CourseGradingModel
from cms.djangoapps.models.settings.course_metadata import CourseMetadata
from common.djangoapps.student.auth import has_studio_read_access
from lms.djangoapps.certificates.api import can_show_certificate_available_date_field
from xmodule.course_block import get_available_providers  # lint-amnesty, pylint: disable=wrong-import-order
from openedx.core.djangoapps.course_apps.toggles import exams_ida_enabled
from openedx.core.djangoapps.credit.api import is_credit_course
from openedx.core.djangoapps.credit.tasks import update_credit_course_requirements
from openedx.core.djangoapps.models.course_details import CourseDetails
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, verify_course_exists, view_auth_classes
from xmodule.modulestore.django import modulestore  # lint-amnesty, pylint: disable=wrong-import-order

from .serializers import (
    LimitedProctoredExamSettingsSerializer,
    ProctoredExamConfigurationSerializer,
    ProctoredExamSettingsSerializer,
    CourseGradingModelSerializer,
    CourseGradingSerializer,
    CourseDetailsSerializer,
    CourseSettingsSerializer
)

from ...utils import get_course_grading, get_course_settings, update_course_details


@view_auth_classes()
class ProctoredExamSettingsView(APIView):
    """
    A view for retrieving information about proctored exam settings for a course.

    Path: ``/api/contentstore/v1/proctored_exam_settings/{course_id}``

    Accepts: [GET, POST]

    ------------------------------------------------------------------------------------
    GET
    ------------------------------------------------------------------------------------

    **Returns**

        * 200: OK - Contains a set of course proctored exam settings.
        * 401: The requesting user is not authenticated.
        * 403: The requesting user lacks access to the course.
        * 404: The requested course does not exist.

    **Response**

        In the case of a 200 response code, the response will proctored exam settings data
        as well as other metadata about the course or the requesting user that are necessary
        for rendering the settings page.

    **Example**

        {
            "proctored_exam_settings": {
                "enable_proctored_exams": true,
                "allow_proctoring_opt_out": true,
                "proctoring_provider": "mockprock",
                "proctoring_escalation_email": null,
                "create_zendesk_tickets": true
            },
            "available_proctoring_providers": [
                "mockprock",
                "proctortrack"
            ],
            "course_start_date": "2013-02-05T05:00:00Z",
        }

    ------------------------------------------------------------------------------------
    POST
    ------------------------------------------------------------------------------------

    **Returns**

        * 200: OK - Proctored exam settings saved.
        * 400: Bad Request - Unable to save requested settings.
        * 401: The requesting user is not authenticated.
        * 403: The requesting user lacks access to the course.
        * 404: The requested course does not exist.

    **Response**

        In the case of a 200 response code, the response will echo the updated proctored
        exam settings data.
    """
    PROCTORED_EXAM_SETTINGS_KEYS = [
        'enable_proctored_exams',
        'allow_proctoring_opt_out',
        'proctoring_provider',
        'proctoring_escalation_email',
        'create_zendesk_tickets',
    ]

    def get(self, request, course_id):
        """ GET handler """
        with modulestore().bulk_operations(CourseKey.from_string(course_id)):
            course_block = self._get_and_validate_course_access(request.user, course_id)
            course_metadata = CourseMetadata().fetch_all(course_block)
            proctored_exam_settings = self._get_proctored_exam_setting_values(course_metadata)

            data = {}

            data['proctored_exam_settings'] = proctored_exam_settings
            data['course_start_date'] = course_metadata['start'].get('value')

            available_providers = get_available_providers()
            if not exams_ida_enabled(CourseKey.from_string(course_id)):
                available_providers.remove('lti_external')

            data['available_proctoring_providers'] = available_providers

            serializer = ProctoredExamConfigurationSerializer(data)

            return Response(serializer.data)

    def post(self, request, course_id):
        """ POST handler """
        serializer = ProctoredExamSettingsSerializer if request.user.is_staff \
            else LimitedProctoredExamSettingsSerializer
        exam_config = serializer(data=request.data.get('proctored_exam_settings', {}))
        valid_request = exam_config.is_valid()
        if not request.user.is_staff and valid_request and ProctoredExamSettingsSerializer(
            data=request.data.get('proctored_exam_settings', {})
        ).is_valid():
            return Response(status=status.HTTP_403_FORBIDDEN)

        with modulestore().bulk_operations(CourseKey.from_string(course_id)):
            course_block = self._get_and_validate_course_access(request.user, course_id)
            course_metadata = CourseMetadata().fetch_all(course_block)

            models_to_update = {}
            for setting_key, value in exam_config.data.items():
                model = course_metadata.get(setting_key)
                if model:
                    models_to_update[setting_key] = copy.deepcopy(model)
                    models_to_update[setting_key]['value'] = value

            # validate data formats and update the course block object
            is_valid, errors, updated_data = CourseMetadata.validate_and_update_from_json(
                course_block,
                models_to_update,
                user=request.user,
            )

            if not is_valid:
                error_messages = [{error.get('key'): error.get('message')} for error in errors]
                return Response(
                    {'detail': error_messages},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # save to mongo
            modulestore().update_item(course_block, request.user.id)

            # merge updated settings with all existing settings.
            # do this because fields that could not be modified are excluded from the result
            course_metadata = {**course_metadata, **updated_data}
            updated_settings = self._get_proctored_exam_setting_values(course_metadata)
            serializer = ProctoredExamSettingsSerializer(updated_settings)
            return Response({
                'proctored_exam_settings': serializer.data
            })

    @classmethod
    def _get_proctored_exam_setting_values(cls, course_metadata):
        return {
            setting_key: course_metadata[setting_key].get('value')
            for setting_key in cls.PROCTORED_EXAM_SETTINGS_KEYS
        }

    @staticmethod
    def _get_and_validate_course_access(user, course_id):
        """
        Check if course_id exists and is accessible by the user.

        Returns a course_block object
        """
        course_key = CourseKey.from_string(course_id)
        course_block = get_course_and_check_access(course_key, user)

        if not course_block:
            raise NotFound(
                f'Course with course_id {course_id} does not exist.'
            )

        return course_block


@view_auth_classes(is_authenticated=True)
class CourseGradingView(DeveloperErrorViewMixin, APIView):
    """
    View for Course Grading policy configuration.
    """

    @apidocs.schema(
        parameters=[
            apidocs.string_parameter("course_id", apidocs.ParameterLocation.PATH, description="Course ID"),
        ],
        responses={
            200: CourseGradingSerializer,
            401: "The requester is not authenticated.",
            403: "The requester cannot access the specified course.",
            404: "The requested course does not exist.",
        },
    )
    @verify_course_exists()
    def get(self, request: Request, course_id: str):
        """
        Get an object containing course grading settings with model.

        **Example Request**

            GET /api/contentstore/v1/course_grading/{course_id}

        **Response Values**

        If the request is successful, an HTTP 200 "OK" response is returned.

        The HTTP 200 response contains a single dict that contains keys that
        are the course's grading.

        **Example Response**

        ```json
        {
            "mfe_proctored_exam_settings_url": "",
            "course_assignment_lists": {
                "Homework": [
                "Section :754c5e889ac3489e9947ba62b916bdab - Subsection :56c1bc20d270414b877e9c178954b6ed"
                ]
            },
            "course_details": {
                "graders": [
                {
                    "type": "Homework",
                    "min_count": 1,
                    "drop_count": 0,
                    "short_label": "",
                    "weight": 100,
                    "id": 0
                }
                ],
                "grade_cutoffs": {
                    "A": 0.75,
                    "B": 0.63,
                    "C": 0.57,
                    "D": 0.5
                },
                "grace_period": {
                    "hours": 12,
                    "minutes": 0
                },
                "minimum_grade_credit": 0.7
            },
            "show_credit_eligibility": false,
            "is_credit_course": true
        }
        ```
        """
        course_key = CourseKey.from_string(course_id)

        if not has_studio_read_access(request.user, course_key):
            self.permission_denied(request)

        with modulestore().bulk_operations(course_key):
            credit_eligibility_enabled = settings.FEATURES.get("ENABLE_CREDIT_ELIGIBILITY", False)
            show_credit_eligibility = is_credit_course(course_key) and credit_eligibility_enabled

            grading_context = get_course_grading(course_key)
            grading_context['show_credit_eligibility'] = show_credit_eligibility

            serializer = CourseGradingSerializer(grading_context)
            return Response(serializer.data)

    @apidocs.schema(
        body=CourseGradingModelSerializer,
        parameters=[
            apidocs.string_parameter("course_id", apidocs.ParameterLocation.PATH, description="Course ID"),
        ],
        responses={
            200: CourseGradingModelSerializer,
            401: "The requester is not authenticated.",
            403: "The requester cannot access the specified course.",
            404: "The requested course does not exist.",
        },
    )
    @verify_course_exists()
    def post(self, request: Request, course_id: str):
        """
        Update a course's grading.

        **Example Request**

            PUT /api/contentstore/v1/course_grading/{course_id}

        **POST Parameters**

        The data sent for a post request should follow next object.
        Here is an example request data that updates the ``course_grading``

        ```json
        {
            "graders": [
                {
                    "type": "Homework",
                    "min_count": 1,
                    "drop_count": 0,
                    "short_label": "",
                    "weight": 100,
                    "id": 0
                }
            ],
            "grade_cutoffs": {
                "A": 0.75,
                "B": 0.63,
                "C": 0.57,
                "D": 0.5
            },
            "grace_period": {
                "hours": 12,
                "minutes": 0
            },
            "minimum_grade_credit": 0.7,
            "is_credit_course": true
        }
        ```

        **Response Values**

        If the request is successful, an HTTP 200 "OK" response is returned,
        """
        course_key = CourseKey.from_string(course_id)

        if not has_studio_read_access(request.user, course_key):
            self.permission_denied(request)

        if 'minimum_grade_credit' in request.data:
            update_credit_course_requirements.delay(str(course_key))

        updated_data = CourseGradingModel.update_from_json(course_key, request.data, request.user)
        serializer = CourseGradingModelSerializer(updated_data)
        return Response(serializer.data)


@view_auth_classes(is_authenticated=True)
class CourseDetailsView(DeveloperErrorViewMixin, APIView):
    """
    View for getting and setting the course details.
    """
    @apidocs.schema(
        parameters=[
            apidocs.string_parameter("course_id", apidocs.ParameterLocation.PATH, description="Course ID"),
        ],
        responses={
            200: CourseDetailsSerializer,
            401: "The requester is not authenticated.",
            403: "The requester cannot access the specified course.",
            404: "The requested course does not exist.",
        },
    )
    @verify_course_exists()
    def get(self, request: Request, course_id: str):
        """
        Get an object containing all the course details.
        **Example Request**
            GET /api/contentstore/v1/course_details/{course_id}
        **Response Values**
        If the request is successful, an HTTP 200 "OK" response is returned.
        The HTTP 200 response contains a single dict that contains keys that
        are the course's details.
        **Example Response**
        ```json
        {
            "about_sidebar_html": "",
            "banner_image_name": "images_course_image.jpg",
            "banner_image_asset_path": "/asset-v1:edX+E2E-101+course+type@asset+block@images_course_image.jpg",
            "certificate_available_date": "2029-01-02T00:00:00Z",
            "certificates_display_behavior": "end",
            "course_id": "E2E-101",
            "course_image_asset_path": "/static/studio/images/pencils.jpg",
            "course_image_name": "",
            "description": "",
            "duration": "",
            "effort": null,
            "end_date": "2023-08-01T01:30:00Z",
            "enrollment_end": "2023-05-30T01:00:00Z",
            "enrollment_start": "2023-05-29T01:00:00Z",
            "entrance_exam_enabled": "",
            "entrance_exam_id": "",
            "entrance_exam_minimum_score_pct": "50",
            "intro_video": null,
            "language": "creative-commons: ver=4.0 BY NC ND",
            "learning_info": [],
            "license": "creative-commons: ver=4.0 BY NC ND",
            "org": "edX",
            "overview": "<section class='about'></section>",
            "pre_requisite_courses": [],
            "run": "course",
            "self_paced": false,
            "short_description": "",
            "start_date": "2023-06-01T01:30:00Z",
            "subtitle": "",
            "syllabus": null,
            "title": "",
            "video_thumbnail_image_asset_path": "/asset-v1:edX+E2E-101+course+type@asset+block@images_course_image.jpg",
            "video_thumbnail_image_name": "images_course_image.jpg",
            "instructor_info": {
                "instructors": [{
                    "name": "foo bar",
                    "title": "title",
                    "organization": "org",
                    "image": "image",
                    "bio": ""
                }]
            }
        }
        ```
        """
        course_key = CourseKey.from_string(course_id)
        if not has_studio_read_access(request.user, course_key):
            self.permission_denied(request)

        course_details = CourseDetails.fetch(course_key)
        serializer = CourseDetailsSerializer(course_details)
        return Response(serializer.data)

    @apidocs.schema(
        body=CourseDetailsSerializer,
        parameters=[
            apidocs.string_parameter("course_id", apidocs.ParameterLocation.PATH, description="Course ID"),
        ],
        responses={
            200: CourseDetailsSerializer,
            401: "The requester is not authenticated.",
            403: "The requester cannot access the specified course.",
            404: "The requested course does not exist.",
        },
    )
    @verify_course_exists()
    def put(self, request: Request, course_id: str):
        """
        Update a course's details.
        **Example Request**
            PUT /api/contentstore/v1/course_details/{course_id}
        **PUT Parameters**
        The data sent for a put request should follow a similar format as
        is returned by a ``GET`` request. Multiple details can be updated in
        a single request, however only the ``value`` field can be updated
        any other fields, if included, will be ignored.
        Example request data that updates the ``course_details`` the same as in GET method
        **Response Values**
        If the request is successful, an HTTP 200 "OK" response is returned,
        along with all the course's details similar to a ``GET`` request.
        """
        course_key = CourseKey.from_string(course_id)
        if not has_studio_read_access(request.user, course_key):
            self.permission_denied(request)

        course_block = modulestore().get_course(course_key)

        try:
            updated_data = update_course_details(request, course_key, request.data, course_block)
        except ValidationError as err:
            return JsonResponseBadRequest({"error": err.message})

        serializer = CourseDetailsSerializer(updated_data)
        return Response(serializer.data)


@view_auth_classes(is_authenticated=True)
class CourseSettingsView(DeveloperErrorViewMixin, APIView):
    """
    View for getting the settings for a course.
    """

    @apidocs.schema(
        parameters=[
            apidocs.string_parameter("course_id", apidocs.ParameterLocation.PATH, description="Course ID"),
        ],
        responses={
            200: CourseSettingsSerializer,
            401: "The requester is not authenticated.",
            403: "The requester cannot access the specified course.",
            404: "The requested course does not exist.",
        },
    )
    @verify_course_exists()
    def get(self, request: Request, course_id: str):
        """
        Get an object containing all the course settings.
        **Example Request**
            GET /api/contentstore/v1/course_settings/{course_id}
        **Response Values**
        If the request is successful, an HTTP 200 "OK" response is returned.
        The HTTP 200 response contains a single dict that contains keys that
        are the course's settings.
        **Example Response**
        ```json
        {
            "about_page_editable": false,
            "can_show_certificate_available_date_field": false,
            "course_display_name": "E2E Test Course",
            "course_display_name_with_default": "E2E Test Course",
            "credit_eligibility_enabled": true,
            "enable_extended_course_details": true,
            "enrollment_end_editable": true,
            "is_credit_course": false,
            "is_entrance_exams_enabled": true,
            "is_prerequisite_courses_enabled": true,
            "language_options": [
                [
                "aa",
                "Afar"
                ],
                [
                "uk",
                "Ukrainian"
                ],
                ...
            ],
            "lms_link_for_about_page": "http://localhost:18000/courses/course-v1:edX+E2E-101+course/about",
            "marketing_enabled": true,
            "mfe_proctored_exam_settings_url": "",
            "possible_pre_requisite_courses": [
                {
                "course_key": "course-v1:edX+M12+2T2023",
                "display_name": "Differential Equations",
                "lms_link": "//localhost:18000/courses/course-v1:edX+M1...",
                "number": "M12",
                "org": "edX",
                "rerun_link": "/course_rerun/course-v1:edX+M12+2T2023",
                "run": "2T2023",
                "url": "/course/course-v1:edX+M12+2T2023"
                },
            ],
            "short_description_editable": true,
            "show_min_grade_warning": false,
            "sidebar_html_enabled": true,
            "upgrade_deadline": null,
            "use_v2_cert_display_settings": false
            }
        ```
        """
        course_key = CourseKey.from_string(course_id)
        if not has_studio_read_access(request.user, course_key):
            self.permission_denied(request)

        with modulestore().bulk_operations(course_key):
            course_block = modulestore().get_course(course_key)
            settings_context = get_course_settings(request, course_key, course_block)
            settings_context.update({
                'can_show_certificate_available_date_field': can_show_certificate_available_date_field(course_block),
                'course_display_name': course_block.display_name,
                'course_display_name_with_default': course_block.display_name_with_default,
                'use_v2_cert_display_settings': settings.FEATURES.get("ENABLE_V2_CERT_DISPLAY_SETTINGS", False),
            })

            serializer = CourseSettingsSerializer(settings_context)
            return Response(serializer.data)
