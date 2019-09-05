"""
Support tool for changing course enrollments.
"""
from __future__ import absolute_import

import csv
from django.utils.decorators import method_decorator
from django.views.generic import View

from edxmako.shortcuts import render_to_response
from lms.djangoapps.support.decorators import require_support_permission

from lms.djangoapps.program_enrollments.api import link_program_enrollments_to_lms_users

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
        successes = []
        errors = []
        if not program_uuid or not text:
            error = 'You must provide both a program uuid and a comma separated list of external_student_key, username'
            errors = [error]
        else:
            reader = csv.DictReader(text.splitlines(), fieldnames=('external_key', 'username'))
            ext_key_to_lms_username = {
                (item['external_key'] or '').strip(): (item['username'] or '').strip()
                for item in reader
            }
            try:
                link_errors = link_program_enrollments_to_lms_users(program_uuid, ext_key_to_lms_username)
            except ValueError as e:
                errors = [str(e)]
            else:
                successes = [str(item) for item in ext_key_to_lms_username.items() if item not in link_errors]
                errors = [message for message in link_errors.values()]

        return render_to_response(
            TEMPLATE_PATH,
            {
                'successes': successes,
                'errors': errors,
                'program_uuid': program_uuid,
                'text': text,
            }
        )
