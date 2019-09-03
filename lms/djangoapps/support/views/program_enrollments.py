"""
Support tool for changing course enrollments.
"""
from __future__ import absolute_import

import six
import csv
import json
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseBadRequest
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import View
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from rest_framework.generics import GenericAPIView
from six import text_type
from django.core.exceptions import ValidationError

from course_modes.models import CourseMode
from edxmako.shortcuts import render_to_response
from lms.djangoapps.support.decorators import require_support_permission
from lms.djangoapps.support.serializers import ManualEnrollmentSerializer
from lms.djangoapps.verify_student.models import VerificationDeadline
from openedx.core.djangoapps.credit.email_utils import get_credit_provider_attribute_values
from openedx.core.djangoapps.enrollments.api import get_enrollments, update_enrollment
from openedx.core.djangoapps.enrollments.errors import CourseModeNotFoundError
from openedx.core.djangoapps.enrollments.serializers import ModeSerializer
from student.models import ENROLLED_TO_ENROLLED, CourseEnrollment, CourseEnrollmentAttribute, ManualEnrollmentAudit
from util.json_request import JsonResponse

from openedx.core.djangoapps.catalog.utils import get_programs
from lms.djangoapps.program_enrollments.link_program_enrollments import link_program_enrollments_to_lms_users

# class EnrollmentSupportView(View):
#     """
#     View for viewing and changing learner enrollments, used by the
#     support team.
#     """

#     @method_decorator(require_support_permission)
#     def get(self, request):
#         """Render the enrollment support tool view."""
#         return render_to_response('support/enrollment.html', {
#             'username': request.GET.get('user', ''),
#             'enrollmentsUrl': reverse('support:enrollment_list'),
#             'enrollmentSupportUrl': reverse('support:enrollment')
#         })


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
        """
        Returns a list of enrollments for the given user, along with
        information about previous manual enrollment changes.
        """
        return render_to_response(TEMPLATE_PATH,
            {
                'successes': [],
                'errors': [],
                'program_uuid': '',
                'text': '',
            }
        )

    @method_decorator(require_support_permission)
    def post(self, request):
        import pdb;pdb.set_trace()
        program_uuid = request.POST.get('program_uuid', '').strip()
        text = request.POST.get('text', '')
        successes = []
        errors = []
        if not program_uuid or not text:
            errors = ['You must provide both a program uuid and a comma separated list of external_student_key, username']
        else:
            reader = csv.DictReader(text.splitlines(), fieldnames=('external_key', 'username'))
            ext_key_to_lms_username = {item['external_key'].strip(): item['username'].strip() for item in reader}
            try:
                link_errors = link_program_enrollments_to_lms_users(program_uuid, ext_key_to_lms_username)
            except ValidationError as e:
                errors = ['{} is not a valid UUID'.format(program_uuid)]
            else:
                successes = [str(item) for item in ext_key_to_lms_username.items() if item not in link_errors]
                errors = [message for message in link_errors.values()]

        return render_to_response(TEMPLATE_PATH,
            {
                'successes': successes,
                'errors': errors,
                'program_uuid': program_uuid,
                'text': text,
            }
        )