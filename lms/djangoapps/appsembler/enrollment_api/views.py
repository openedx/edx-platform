import logging

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import Http404
from opaque_keys.edx.keys import CourseKey
from openedx.core.lib.api.authentication import (
    OAuth2AuthenticationAllowInactiveUser,
)
from openedx.core.lib.api.permissions import IsStaffOrOwner
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from course_modes.models import CourseMode
from courseware.courses import get_course_by_id
from enrollment.views import EnrollmentCrossDomainSessionAuth
from instructor.views.api import save_registration_code
from shoppingcart.exceptions import (
    RedemptionCodeError
)
from shoppingcart.models import (
    RegistrationCodeRedemption,
    CourseRegistrationCode)
from shoppingcart.views import get_reg_code_validity
from student.models import CourseEnrollment, EnrollmentClosedError, CourseFullError, \
    AlreadyEnrolledError
from util.bad_request_rate_limiter import BadRequestRateLimiter

log = logging.getLogger(__name__)


class GenerateRegistrationCodesView(APIView):
    authentication_classes = OAuth2AuthenticationAllowInactiveUser, EnrollmentCrossDomainSessionAuth
    permission_classes = IsStaffOrOwner,

    def post(self, request):
        course_id = CourseKey.from_string(request.data.get('course_id'))

        try:
            course_code_number = int(request.data.get('total_registration_codes'))
        except ValueError:
            course_code_number = int(float(request.data.get('total_registration_codes')))

        course_mode = 'audit'

        registration_codes = []
        for __ in range(course_code_number):
            generated_registration_code = save_registration_code(
                request.user, course_id, course_mode, order=None,
            )
            registration_codes.append(generated_registration_code.code)

        return Response(
            data={
                'codes': registration_codes,
                'course_id': request.data.get('course_id'),
                'course_url': reverse('about_course', kwargs={'course_id': request.data.get('course_id')})
            }
        )


class EnrollUserWithEnrollmentCodeView(APIView):
    authentication_classes = OAuth2AuthenticationAllowInactiveUser, EnrollmentCrossDomainSessionAuth
    permission_classes = IsStaffOrOwner,

    def post(self, request):
        enrollment_code = request.data.get('enrollment_code')
        limiter = BadRequestRateLimiter()
        error_reason = ""
        try:
            user = User.objects.get(email=request.data.get('email'))
            user_is_valid = True
        except User.DoesNotExist:
            user_is_valid = False
            error_reason = "User not found"
        try:
            reg_code_is_valid, reg_code_already_redeemed, course_registration = get_reg_code_validity(
                enrollment_code,
                request,
                limiter
            )
        except Http404:
            reg_code_is_valid = False
            reg_code_already_redeemed = False
            error_reason = "Enrollment code not found"
        if user_is_valid and reg_code_is_valid:
            course = get_course_by_id(course_registration.course_id, depth=0)
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
                error_reason = "Enrollment code error"
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


class EnrollmentCodeStatusView(APIView):
    authentication_classes = OAuth2AuthenticationAllowInactiveUser, EnrollmentCrossDomainSessionAuth
    permission_classes = IsStaffOrOwner,

    def post(self, request):
        code = request.data.get('enrollment_code')
        action = request.data.get('action')
        try:
            registration_code = CourseRegistrationCode.objects.get(code=code)
        except CourseRegistrationCode.DoesNotExist:
            return Response(
                data={
                    'reason': 'The enrollment code ({code}) was not found'.format(code=code),
                    'success': False},
                status=400
            )

        redemption = RegistrationCodeRedemption.get_registration_code_redemption(registration_code.code,
                                                                                 registration_code.course_id)
        if action == 'cancel':
            if redemption:
                CourseEnrollment.unenroll(redemption.course_enrollment.user, registration_code.course_id)
            registration_code.is_valid = False
            registration_code.save()

        if action == 'restore':
            registration_code.is_valid = True
            registration_code.save()
        return Response(data={'success': True})
