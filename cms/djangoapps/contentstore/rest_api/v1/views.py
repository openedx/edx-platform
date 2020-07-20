"Contentstore Views"

from opaque_keys.edx.keys import CourseKey
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from common.lib.xmodule.xmodule.course_module import get_available_providers
from contentstore.views.course import get_course_and_check_access
from models.settings.course_metadata import CourseMetadata
from openedx.core.lib.api.view_utils import view_auth_classes
from xmodule.modulestore.django import modulestore

from contentstore.rest_api.v1.serializers import ProctoredExamConfigurationSerializer


@view_auth_classes()
class ProctoredExamSettingsView(APIView):
    """
    A view for retrieving information about proctored exam settings for a course.

    Path: ``/api/contentstore/v1/proctored_exam_settings/{course_id}``

    Accepts: [GET]

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
            "is_staff": true
        }
    """
    def get(self, request, course_id):
        course_module = self._get_and_validate_course(course_id)

        # todo: should this be wrapped as a bulk operation?
        course_metadata = CourseMetadata().fetch_all(course_module)
        data = {}

        # specify only the advanced settings we want to return
        proctored_exam_settings_advanced_settings_keys = [
            'enable_proctored_exams',
            'allow_proctoring_opt_out',
            'proctoring_provider',
            'proctoring_escalation_email',
            'create_zendesk_tickets',
            'start'
        ]
        proctored_exam_settings_data = {
            setting_key: setting_value.get('value')
            for (setting_key, setting_value) in course_metadata.items()
            if setting_key in proctored_exam_settings_advanced_settings_keys
        }

        data['proctored_exam_settings'] = proctored_exam_settings_data
        data['available_proctoring_providers'] = get_available_providers()

        # move start key:value out of proctored_exam_settings dictionary and change key
        data['course_start_date'] = proctored_exam_settings_data['start']
        del data['proctored_exam_settings']['start']

        data['is_staff'] = self.request.user.is_staff

        serializer = ProctoredExamConfigurationSerializer(data)

        return Response(serializer.data)

    def _get_and_validate_course(self, course_id):
        course_key = CourseKey.from_string(course_id)
        course_module = get_course_and_check_access(course_key, self.request.user)

        if not course_module:
            return Response(
                'Course with course_id {} does not exist.'.format(course_id),
                status=status.HTTP_404_NOT_FOUND
            )

        return course_module