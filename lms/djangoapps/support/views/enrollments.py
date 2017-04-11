"""
Support tool for changing course enrollments.
"""
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseBadRequest
from django.utils.decorators import method_decorator
from django.views.generic import View
from rest_framework.generics import GenericAPIView
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from certificates import api as cert_api
from course_modes.models import CourseMode
from edxmako.shortcuts import render_to_response
from enrollment.api import get_enrollments, update_enrollment
from enrollment.errors import CourseModeNotFoundError
from enrollment.serializers import ModeSerializer
from lms.djangoapps.support.decorators import require_support_permission
from lms.djangoapps.support.serializers import ManualEnrollmentSerializer
from lms.djangoapps.verify_student.models import VerificationDeadline
from student.models import CourseEnrollment, ManualEnrollmentAudit, ENROLLED_TO_ENROLLED
from util.json_request import JsonResponse


class EnrollmentSupportView(View):
    """
    View for viewing and changing learner enrollments, used by the
    support team.
    """

    @method_decorator(require_support_permission)
    def get(self, request):
        """Render the enrollment support tool view."""
        return render_to_response('support/enrollment.html', {
            'username': request.GET.get('user', ''),
            'enrollmentsUrl': reverse('support:enrollment_list'),
            'enrollmentSupportUrl': reverse('support:enrollment')
        })


class EnrollmentSupportListView(GenericAPIView):
    """
    Allows viewing and changing learner enrollments by support
    staff.
    """

    @method_decorator(require_support_permission)
    def get(self, request, username_or_email):
        """
        Returns a list of enrollments for the given user, along with
        information about previous manual enrollment changes.
        """
        try:
            user = User.objects.get(Q(username=username_or_email) | Q(email=username_or_email))
        except User.DoesNotExist:
            return JsonResponse([])

        enrollments = get_enrollments(user.username)
        for enrollment in enrollments:
            # Folds the course_details field up into the main JSON object.
            enrollment.update(**enrollment.pop('course_details'))
            course_key = CourseKey.from_string(enrollment['course_id'])
            # get the all courses modes and replace with existing modes.
            enrollment['course_modes'] = self.get_course_modes(course_key)
            # Add the price of the course's verified mode.
            self.include_verified_mode_info(enrollment, course_key)
            # Add manual enrollment history, if it exists
            enrollment['manual_enrollment'] = self.manual_enrollment_data(enrollment, course_key)
        return JsonResponse(enrollments)

    @method_decorator(require_support_permission)
    def post(self, request, username_or_email):
        """Allows support staff to alter a user's enrollment."""
        try:
            user = User.objects.get(Q(username=username_or_email) | Q(email=username_or_email))
            course_id = request.data['course_id']
            course_key = CourseKey.from_string(course_id)
            old_mode = request.data['old_mode']
            new_mode = request.data['new_mode']
            reason = request.data['reason']
            enrollment = CourseEnrollment.objects.get(user=user, course_id=course_key)
            if enrollment.mode != old_mode:
                return HttpResponseBadRequest(u'User {username} is not enrolled with mode {old_mode}.'.format(
                    username=user.username,
                    old_mode=old_mode
                ))
            if new_mode == CourseMode.CREDIT_MODE:
                return HttpResponseBadRequest(u'Enrollment cannot be changed to credit mode.')
        except KeyError as err:
            return HttpResponseBadRequest(u'The field {} is required.'.format(err.message))
        except InvalidKeyError:
            return HttpResponseBadRequest(u'Could not parse course key.')
        except (CourseEnrollment.DoesNotExist, User.DoesNotExist):
            return HttpResponseBadRequest(
                u'Could not find enrollment for user {username} in course {course}.'.format(
                    username=username_or_email,
                    course=unicode(course_key)
                )
            )
        try:
            # Wrapped in a transaction so that we can be sure the
            # ManualEnrollmentAudit record is always created correctly.
            with transaction.atomic():
                update_enrollment(user.username, course_id, mode=new_mode, include_expired=True)
                manual_enrollment = ManualEnrollmentAudit.create_manual_enrollment_audit(
                    request.user,
                    enrollment.user.email,
                    ENROLLED_TO_ENROLLED,
                    reason=reason,
                    enrollment=enrollment
                )
                # Invalidate user certificate after enrolment has changed.
                user_certificate = cert_api.get_certificate_for_user(user, course_key, format=False)
                if user_certificate:
                    # Invalidate if certificate exists.
                    user_certificate.invalidate()
                return JsonResponse(ManualEnrollmentSerializer(instance=manual_enrollment).data)
        except CourseModeNotFoundError as err:
            return HttpResponseBadRequest(err.message)

    @staticmethod
    def include_verified_mode_info(enrollment_data, course_key):
        """
        Add information about the verified mode for the given
        `course_key`, if that course has a verified mode.

        Args:
          enrollment_data (dict): Dictionary representing a single enrollment.
          course_key (CourseKey): The course which this enrollment belongs to.

        Returns:
          None
        """
        course_modes = enrollment_data['course_modes']
        for mode in course_modes:
            if mode['slug'] == CourseMode.VERIFIED:
                enrollment_data['verified_price'] = mode['min_price']
                enrollment_data['verified_upgrade_deadline'] = mode['expiration_datetime']
                enrollment_data['verification_deadline'] = VerificationDeadline.deadline_for_course(course_key)

    @staticmethod
    def manual_enrollment_data(enrollment_data, course_key):
        """
        Returns serialized information about the manual enrollment
        belonging to this enrollment, if it exists.

        Args:
          enrollment_data (dict): Representation of a single course enrollment.
          course_key (CourseKey): The course for this enrollment.

        Returns:
          None: If no manual enrollment change has been made.
          dict: Serialization of the latest manual enrollment change.
        """
        user = User.objects.get(username=enrollment_data['user'])
        enrollment = CourseEnrollment.get_enrollment(user, course_key)
        manual_enrollment_audit = ManualEnrollmentAudit.get_manual_enrollment(enrollment)
        if manual_enrollment_audit is None:
            return {}
        return ManualEnrollmentSerializer(instance=manual_enrollment_audit).data

    @staticmethod
    def get_course_modes(course_key):
        """
        Returns a list of all modes including expired modes for a given course id

        Arguments:
            course_id (CourseKey): Search for course modes for this course.

        Returns:
            list of `Mode`

        """
        course_modes = CourseMode.modes_for_course(
            course_key,
            include_expired=True
        )
        return [
            ModeSerializer(mode).data
            for mode in course_modes
        ]
