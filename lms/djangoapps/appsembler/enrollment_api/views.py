import logging

from django.contrib.auth.models import User
from django.shortcuts import redirect
from ipware.ip import get_ip
from opaque_keys.edx.keys import CourseKey
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from course_modes.models import CourseMode
from courseware.courses import get_course_by_id
from edxmako.shortcuts import render_to_response
from embargo import api as embargo_api
from enrollment.views import EnrollmentCrossDomainSessionAuth
from instructor.views.api import save_registration_code
from openedx.core.lib.api.authentication import (
    OAuth2AuthenticationAllowInactiveUser,
)
from openedx.core.lib.api.permissions import IsStaffOrOwner
from shoppingcart.exceptions import (
    ItemNotFoundInCartException, RedemptionCodeError
)
from shoppingcart.models import (
    Order, PaidCourseRegistration, RegistrationCodeRedemption, CourseRegCodeItem
)
from shoppingcart.views import get_reg_code_validity
from student.models import CourseEnrollment, EnrollmentClosedError, CourseFullError, \
    AlreadyEnrolledError
from util.bad_request_rate_limiter import BadRequestRateLimiter

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
            registration_codes.append(generated_registration_code.code)

        return Response(
            data={
                'codes': registration_codes
            }
        )


class EnrollUserWithEnrollmentCodeView(APIView):
    authentication_classes = OAuth2AuthenticationAllowInactiveUser, EnrollmentCrossDomainSessionAuth
    permission_classes = IsStaffOrOwner,

    def post(self, request):
        user = User.objects.get(email=request.data.get('email'))
        enrollment_code = request.data.get('enrollment_code')
        limiter = BadRequestRateLimiter()
        reg_code_is_valid, reg_code_already_redeemed, course_registration = get_reg_code_validity(
            enrollment_code,
            request,
            limiter
        )
        course = get_course_by_id(course_registration.course_id, depth=0)
        error_reason = ""
        if reg_code_is_valid and not reg_code_already_redeemed:
            # now redeem the reg code.
            redemption = RegistrationCodeRedemption.create_invoice_generated_registration_redemption(
                course_registration,
                user)
            try:
                kwargs = {}
                if course_registration.mode_slug is not None:
                    if CourseMode.mode_for_course(course.id, course_registration.mode_slug):
                        kwargs['mode'] = course_registration.mode_slug
                    else:
                        raise RedemptionCodeError()
                redemption.course_enrollment = CourseEnrollment.enroll(user, course.id, **kwargs)
                redemption.save()
                return Response(data={
                    'success': True,
                })
            except RedemptionCodeError:
                error_reason = "Redemption code error"
            except EnrollmentClosedError:
                error_reason = "Enrollment closed"
            except CourseFullError:
                error_reason = "Course full"
            except AlreadyEnrolledError:
                error_reason = "Already enrolled"
        return Response(
            data={
                'success': False,
                'reason': error_reason,
            },
            status=status.HTTP_400_BAD_REQUEST
        )
