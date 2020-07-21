"Contentstore Views"

from opaque_keys.edx.keys import CourseKey
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from common.lib.xmodule.xmodule.course_module import get_available_providers
from contentstore.views.course import get_course_and_check_access
from models.settings.course_metadata import CourseMetadata
from openedx.core.lib.api.view_utils import view_auth_classes
from xmodule.modulestore.django import modulestore

from contentstore.rest_api.v1.serializers import (
    ProctoredExamConfigurationSerializer,
    ProctoredExamSettingsSerializer,
)


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

        * 200: OK - Proctored exam settings saved.
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
            "is_staff": true
        }

    ------------------------------------------------------------------------------------
    POST
    ------------------------------------------------------------------------------------

    **Returns**

        * 200: OK - Contains a set of course proctored exam settings.
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
        'start'
    ]

    def get(self, request, course_id):
        # todo: should this be wrapped as a bulk operation?
        course_module = self._get_and_validate_course(request.user, course_id)
        proctored_exam_settings = self._get_proctored_exam_settings(course_module)

        data = {}

        data['proctored_exam_settings'] = self._get_settings_values(proctored_exam_settings)
        data['available_proctoring_providers'] = get_available_providers()

        # move start key:value out of proctored_exam_settings dictionary and change key
        data['course_start_date'] = proctored_exam_settings['start'].get('value')
        del data['proctored_exam_settings']['start']

        data['is_staff'] = request.user.is_staff

        serializer = ProctoredExamConfigurationSerializer(data)

        return Response(serializer.data)
        
    def post(self, request, course_id):
        exam_config = ProctoredExamSettingsSerializer(data=request.data.get('proctored_exam_settings', {}))
        exam_config.is_valid(raise_exception=True)
        with modulestore().bulk_operations(CourseKey.from_string(course_id)):
            course_module = self._get_and_validate_course(request.user, course_id)
            proctored_exam_settings = self._get_proctored_exam_settings(course_module)

            for setting_key, value in exam_config.data.items():
                model = proctored_exam_settings.get(setting_key)
                if model:
                    model['value'] = value

            # validate data formats and update the course module object
            is_valid, errors, updated_data = CourseMetadata.validate_and_update_from_json(
                course_module,
                proctored_exam_settings,
                user=request.user,
            )

            if not is_valid:
                return Response(errors, status=status.HTTP_400_BAD_REQUEST)

            # save to mongo
            modulestore().update_item(course_module, request.user.id)
            return Response({
                'proctored_exam_settings': self._get_settings_values(proctored_exam_settings)
            })

    @classmethod
    def _get_proctored_exam_settings(cls, course_module):
        course_metadata = CourseMetadata().fetch_all(course_module)
        return {
            setting_key: course_metadata[setting_key]
            for setting_key in cls.PROCTORED_EXAM_SETTINGS_KEYS
        }
    
    @staticmethod
    def _get_settings_values(settings):
        return {
            setting_key: setting_value.get('value')
            for (setting_key, setting_value) in settings.items()
        }

    @staticmethod
    def _get_and_validate_course(user, course_id):
        course_key = CourseKey.from_string(course_id)
        course_module = get_course_and_check_access(course_key, user)

        if not course_module:
            raise NotFound(
                'Course with course_id {} does not exist.'.format(course_id)
            )

        return course_module
