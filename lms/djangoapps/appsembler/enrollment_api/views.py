import logging

from opaque_keys.edx.keys import CourseKey
from rest_framework.response import Response
from rest_framework.views import APIView

from enrollment.views import EnrollmentCrossDomainSessionAuth
from instructor.views.api import save_registration_code
from openedx.core.lib.api.authentication import (
    OAuth2AuthenticationAllowInactiveUser,
)
from openedx.core.lib.api.permissions import IsStaffOrOwner

log = logging.getLogger(__name__)


class GenerateRegistrationCodesView(APIView):
    authentication_classes = OAuth2AuthenticationAllowInactiveUser, EnrollmentCrossDomainSessionAuth
    permission_classes = IsStaffOrOwner,

    def post(self, request):
        """
            Respond with csv which contains a summary of all Generated Codes.
            """
        course_id = CourseKey.from_string(request.data.get('course_id'))

        # covert the course registration code number into integer
        try:
            course_code_number = int(request.data.get('total_registration_codes'))
        except ValueError:
            course_code_number = int(float(request.data.get('total_registration_codes')))

        course_mode = 'honor'

        registration_codes = []
        for __ in range(course_code_number):
            generated_registration_code = save_registration_code(
                request.user, course_id, course_mode, order=None,
            )
            registration_codes.append(generated_registration_code)

        return Response(
            data={
                'codes': registration_codes
            }
        )
