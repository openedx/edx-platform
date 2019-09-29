"""
Support tool for changing course enrollments.
"""
from __future__ import absolute_import, unicode_literals

import csv
from uuid import UUID

from django.utils.decorators import method_decorator
from django.views.generic import View

from edxmako.shortcuts import render_to_response
from lms.djangoapps.program_enrollments.api import link_program_enrollments
from lms.djangoapps.support.decorators import require_support_permission

TEMPLATE_PATH = 'support/link_program_enrollments.html'


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
