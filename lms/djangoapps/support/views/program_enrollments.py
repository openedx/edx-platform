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
    get_users_by_external_keys_and_org_key,
    link_program_enrollments
)
from lms.djangoapps.program_enrollments.exceptions import (
    BadOrganizationShortNameException,
    ProviderConfigurationException,
    ProviderDoesNotExistException
)
from lms.djangoapps.support.decorators import require_support_permission
from lms.djangoapps.support.serializers import (
    ProgramEnrollmentSerializer,
    serialize_user_info
)
from lms.djangoapps.verify_student.services import IDVerificationService
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
            learner_program_enrollments = self._get_external_user_info(
                external_user_key,
                org_key
            )
            if not learner_program_enrollments:
                errors.append(
                    'No user found for external key {} for institution {}'.format(
                        external_user_key, org_key
                    )
                )
        else:
            errors.append(
                "To perform a search, you must provide either the student's "
                "(a) edX username, "
                "(b) email address associated with their edX account, or "
                "(c) Identity-providing institution and external key!"
            )

        return render_to_response(
            self.CONSOLE_TEMPLATE_PATH,
            {
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
        try:
            user = User.objects.get(Q(username=username_or_email) | Q(email=username_or_email))
            user_social_auth = None
            try:
                user_social_auth = UserSocialAuth.objects.get(user=user)
            except UserSocialAuth.DoesNotExist:
                pass
            user_info = serialize_user_info(user, user_social_auth)
            enrollments = self._get_enrollments(user=user)
            result = {'user': user_info}
            if enrollments:
                result['enrollments'] = enrollments

            result['id_verification'] = IDVerificationService.user_status(user)
            return result, ''
        except User.DoesNotExist:
            return {}, 'Could not find edx account with {}'.format(username_or_email)

    def _get_external_user_info(self, external_user_key, org_key):
        """
        Provided the external_user_key and org_key, return edx account info
        and program_enrollments_info if any. If we cannot identify the data,
        return empty object.
        """
        found_user = None
        result = {}
        try:
            users_by_key = get_users_by_external_keys_and_org_key(
                [external_user_key],
                org_key
            )
            found_user = users_by_key.get(external_user_key)
        except (
            BadOrganizationShortNameException,
            ProviderConfigurationException,
            ProviderDoesNotExistException
        ):
            # We cannot identify edX user from external_user_key and org_key pair
            pass

        if found_user:
            try:
                user_social_auth = UserSocialAuth.objects.get(user=found_user)
            except UserSocialAuth.DoesNotExist:
                user_social_auth = None
            user_info = serialize_user_info(found_user, user_social_auth)
            result['user'] = user_info
            result['id_verification'] = IDVerificationService.user_status(found_user)
        enrollments = self._get_enrollments(external_user_key=external_user_key)
        if enrollments:
            result['enrollments'] = enrollments
        return result

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
        serialized = ProgramEnrollmentSerializer(program_enrollments, many=True)
        return serialized.data
