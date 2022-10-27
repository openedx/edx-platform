"Contentstore Views"
import copy

from opaque_keys.edx.keys import CourseKey
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from cms.djangoapps.contentstore.views.course import get_course_and_check_access
from cms.djangoapps.models.settings.course_metadata import CourseMetadata
from xmodule.course_block import get_available_providers  # lint-amnesty, pylint: disable=wrong-import-order
from openedx.core.djangoapps.course_apps.toggles import exams_ida_enabled
from openedx.core.lib.api.view_utils import view_auth_classes
from xmodule.modulestore.django import modulestore  # lint-amnesty, pylint: disable=wrong-import-order

from .serializers import (
    LimitedProctoredExamSettingsSerializer,
    ProctoredExamConfigurationSerializer,
    ProctoredExamSettingsSerializer
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
