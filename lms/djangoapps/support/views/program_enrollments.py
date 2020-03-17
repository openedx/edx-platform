"""
Support tool for changing course enrollments.
"""


import csv
from uuid import UUID

from django.contrib.auth.models import User
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.generic import View
from social_django.models import UserSocialAuth

from edxmako.shortcuts import render_to_response
from lms.djangoapps.program_enrollments.api import (
    fetch_program_enrollments_by_student,
    link_program_enrollments
)
from lms.djangoapps.support.decorators import require_support_permission
from third_party_auth.models import SAMLProviderConfig

TEMPLATE_PATH = 'support/link_program_enrollments.html'
DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S'


class LinkProgramEnrollmentSupportView(View):
    """
    Allows viewing and changing learner enrollments by support
    staff.
    """
    # TODO: ARCH-91
    # This view is excluded from Swagger doc generation because it
    # does not specify a serializer class.
    exclude_from_schema = True

    @method_decorator(require_support_permission)
    def get(self, request):
        return render_to_response(
            TEMPLATE_PATH,
            {
                'successes': [],
                'errors': [],
                'program_uuid': '',
                'text': '',
            }
        )

    @method_decorator(require_support_permission)
    def post(self, request):
        """
        Link the given program enrollments and lms users
        """
        program_uuid = request.POST.get('program_uuid', '').strip()
        text = request.POST.get('text', '')
        successes, errors = self._validate_and_link(program_uuid, text)
        return render_to_response(
            TEMPLATE_PATH,
            {
                'successes': successes,
                'errors': errors,
                'program_uuid': program_uuid,
                'text': text,
            }
        )

    @staticmethod
    def _validate_and_link(program_uuid_string, linkage_text):
        """
        Validate arguments, and if valid, call `link_program_enrollments`.

        Returns: (successes, errors)
            where successes and errors are both list[str]
        """
        if not (program_uuid_string and linkage_text):
            error = (
                "You must provide both a program uuid "
                "and a series of lines with the format "
                "'external_user_key,lms_username'."
            )
            return [], [error]
        try:
            program_uuid = UUID(program_uuid_string)
        except ValueError:
            return [], [
                "Supplied program UUID '{}' is not a valid UUID.".format(program_uuid_string)
            ]
        reader = csv.DictReader(
            linkage_text.splitlines(), fieldnames=('external_key', 'username')
        )
        ext_key_to_username = {
            (item.get('external_key') or '').strip(): (item['username'] or '').strip()
            for item in reader
        }
        if not (all(ext_key_to_username.keys()) and all(ext_key_to_username.values())):
            return [], [
                "All linking lines must be in the format 'external_user_key,lms_username'"
            ]
        link_errors = link_program_enrollments(
            program_uuid, ext_key_to_username
        )
        successes = [
            str(item)
            for item in ext_key_to_username.items()
            if item not in link_errors
        ]
        errors = [message for message in link_errors.values()]
        return successes, errors


class ProgramEnrollmentsInspectorView(View):
    """
    The view to search and display the program enrollments
    information of a learner.
    """
    exclude_from_schema = True
    CONSOLE_TEMPLATE_PATH = 'support/program_enrollments_inspector.html'

    @method_decorator(require_support_permission)
    def get(self, request):
        """
        Based on the query string parameters passed through the GET request
        Search the data store for information about ProgramEnrollment and
        SSO linkage with the user.
        """
        errors = []
        edx_username_or_email = request.GET.get('edx_user', '').strip()
        org_key = request.GET.get('IdPSelect', '').strip()
        external_user_key = request.GET.get('external_user_key', '').strip()
        learner_program_enrollments = {}
        if edx_username_or_email:
            learner_program_enrollments, error = self._get_account_info(edx_username_or_email)
            if error:
                errors.append(error)
        elif org_key and external_user_key:
            learner_program_enrollments = {}
        elif not external_user_key and org_key:
            errors.append(
                'You must provide either the edX username or email, or the '
                'Learner Account Provider and External Key pair to do search!'
            )

        return render_to_response(
            self.CONSOLE_TEMPLATE_PATH,
            {
                'successes': [],
                'errors': errors,
                'learner_program_enrollments': learner_program_enrollments,
                'org_keys': self._get_org_keys_with_idp(),
            }
        )

    def _get_org_keys_with_idp(self):
        """
        From our Third_party_auth models, return a list
        of organizations whose SAMLProviders are active and configured
        """
        saml_providers = SAMLProviderConfig.objects.current_set().filter(
            enabled=True,
            organization__isnull=False
        ).select_related('organization')

        return [saml_provider.organization.short_name for saml_provider in saml_providers]

    def _get_account_info(self, username_or_email):
        """
        Provided the edx account username or email, return edx account info
        and program_enrollments_info. If we cannot identify the user, return
        empty object and error.
        """
        user_info = {}
        external_key = None
        try:
            user = User.objects.get(Q(username=username_or_email) | Q(email=username_or_email))
            user_info['username'] = user.username
            user_info['email'] = user.email
            try:
                user_social_auth = UserSocialAuth.objects.get(user=user)
                _, external_key = user_social_auth.uid.split(':', 1)
                user_info['external_user_key'] = external_key
                user_info['SSO'] = {
                    'uid': user_social_auth.uid,
                    'provider': user_social_auth.provider
                }
            except UserSocialAuth.DoesNotExist:
                pass

            enrollments = self._get_enrollments(user=user)
            result = {'user': user_info}
            if enrollments:
                result['enrollments'] = enrollments

            return result, ''
        except User.DoesNotExist:
            return {}, 'Could not find edx account with {}'.format(username_or_email)

    def _get_enrollments(self, user=None, external_user_key=None):
        """
        With the user or external_user_key passed in,
        return an array of dictionariers with corresponding ProgramEnrollments
        and ProgramCourseEnrollments all serialized for view
        """
        program_enrollments = fetch_program_enrollments_by_student(
            user=user,
            external_user_key=external_user_key
        ).prefetch_related('program_course_enrollments')

        enrollments_by_program_uuid = {}
        for program_enrollment in program_enrollments:
            serialized_program_enrollment = self._serialize_program_enrollment(program_enrollment)
            enrollment_item = {
                'program_enrollment': serialized_program_enrollment
            }
            program_course_enrollments = program_enrollment.program_course_enrollments.all()
            for program_course_enrollment in program_course_enrollments.select_related(
                'course_enrollment'
            ):
                serialized_program_course_enrollment = self._serialize_program_course_enrollment(
                    program_course_enrollment
                )
                enrollment_item.setdefault('program_course_enrollments', []).append(
                    serialized_program_course_enrollment
                )
            enrollments_by_program_uuid[program_enrollment.program_uuid] = enrollment_item

        return list(enrollments_by_program_uuid.values())

    def _serialize_program_enrollment(self, program_enrollment):
        if not program_enrollment:
            return {}

        return {
            'created': program_enrollment.created.strftime(DATETIME_FORMAT),
            'modified': program_enrollment.modified.strftime(DATETIME_FORMAT),
            'program_uuid': str(program_enrollment.program_uuid),
            'external_user_key': program_enrollment.external_user_key,
            'status': program_enrollment.status
        }

    def _serialize_program_course_enrollment(self, program_course_enrollment):
        """
        Return a dictionary of ProgramCourseEnrollment serialized
        """
        if not program_course_enrollment:
            return {}

        course_enrollment = program_course_enrollment.course_enrollment
        return {
            'created': program_course_enrollment.created.strftime(DATETIME_FORMAT),
            'modified': program_course_enrollment.modified.strftime(DATETIME_FORMAT),
            'course_enrollment': {
                'course_id': str(course_enrollment.course_id),
                'is_active': course_enrollment.is_active,
                'mode': course_enrollment.mode,
            },
            'status': program_course_enrollment.status,
            'course_key': str(program_course_enrollment.course_key),
        }
