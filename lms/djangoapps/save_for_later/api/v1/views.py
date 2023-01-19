"""
Save for later views
"""

import logging

from django.conf import settings
from django.utils.decorators import method_decorator
from ratelimit.decorators import ratelimit
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError

from openedx.core.djangoapps.user_api.accounts.api import get_email_validation_error
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.catalog.utils import get_programs

from lms.djangoapps.save_for_later.helper import send_email
from lms.djangoapps.save_for_later.models import SavedCourse, SavedProgram

log = logging.getLogger(__name__)

POST_EMAIL_KEY = 'openedx.core.djangoapps.util.ratelimit.request_data_email'
REAL_IP_KEY = 'openedx.core.djangoapps.util.ratelimit.real_ip'
USER_SEND_SAVE_FOR_LATER_EMAIL = 'user.send.save.for.later.email'


class CourseSaveForLaterApiView(APIView):
    """
    Save course API VIEW
    """

    @transaction.atomic
    @method_decorator(ratelimit(key=POST_EMAIL_KEY, rate=settings.SAVE_FOR_LATER_EMAIL_RATE_LIMIT, method='POST'))
    @method_decorator(ratelimit(key=REAL_IP_KEY, rate=settings.SAVE_FOR_LATER_IP_RATE_LIMIT, method='POST'))
    def post(self, request):
        """
        **Use Case**

            * Send favorite course through email to user for later learning.

        **Example Request for course**

            POST /api/v1/save/course/

        **Example POST Request for course**

            {
                "email": "test@edx.org",
                "course_id": "course-v1:edX+DemoX+2021",
                "marketing_url": "https://test.com",
                "org_img_url": "https://test.com/logo.png",
                "weeks_to_complete": 7,
                "min_effort": 4,
                "max_effort": 5,

            }
        """
        user = request.user
        data = request.data
        course_id = data.get('course_id')
        email = data.get('email')
        org_img_url = data.get('org_img_url')
        marketing_url = data.get('marketing_url')
        weeks_to_complete = data.get('weeks_to_complete', 0)
        min_effort = data.get('min_effort', 0)
        max_effort = data.get('max_effort', 0)
        user_id = request.user.id
        pref_lang = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME, 'en')
        send_to_self = bool(not request.user.is_anonymous and request.user.email == email)

        if getattr(request, 'limited', False):
            return Response({'error_code': 'rate-limited'}, status=403)

        if get_email_validation_error(email):
            return Response({'error_code': 'incorrect-email'}, status=400)

        try:
            course_key = CourseKey.from_string(course_id)
            course = CourseOverview.get_from_id(course_key)
        except InvalidKeyError:
            return Response({'error_code': 'invalid-course-key'}, status=400)
        except CourseOverview.DoesNotExist:
            return Response({'error_code': 'course-not-found'}, status=404)

        SavedCourse.objects.update_or_create(
            email=email,
            course_id=course_id,
            defaults={
                'user_id': user.id,
                'org_img_url': org_img_url,
                'marketing_url': marketing_url,
                'weeks_to_complete': weeks_to_complete,
                'min_effort': min_effort,
                'max_effort': max_effort,
                'reminder_email_sent': False,
            }
        )
        course_data = {
            'course': course,
            'send_to_self': send_to_self,
            'user_id': user_id,
            'pref-lang': pref_lang,
            'org_img_url': org_img_url,
            'marketing_url': marketing_url,
            'weeks_to_complete': weeks_to_complete,
            'min_effort': min_effort,
            'max_effort': max_effort,
            'type': 'course',
            'reminder': False,
            'braze_event': USER_SEND_SAVE_FOR_LATER_EMAIL,
        }
        if send_email(email, course_data):
            return Response({'result': 'success'}, status=200)
        else:
            return Response({'error_code': 'email-not-send'}, status=400)


class ProgramSaveForLaterApiView(APIView):
    """
    API VIEW
    """

    @transaction.atomic
    @method_decorator(ratelimit(key=POST_EMAIL_KEY, rate=settings.SAVE_FOR_LATER_EMAIL_RATE_LIMIT, method='POST'))
    @method_decorator(ratelimit(key=REAL_IP_KEY, rate=settings.SAVE_FOR_LATER_IP_RATE_LIMIT, method='POST'))
    def post(self, request):
        """
        **Use Case**

            * Send favorite program through email to user for later learning.

        **Example Request for program**

            POST /api/v1/save/program/

        **Example POST Request for program**

            {
                "email": "test@edx.org",
                "program_uuid": "587f6abe-bfa4-4125-9fbe-4789bf3f97f1"
            }
        """
        user = request.user
        data = request.data
        program_uuid = data.get('program_uuid')
        email = data.get('email')
        user_id = request.user.id
        pref_lang = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME, 'en')
        send_to_self = bool(not request.user.is_anonymous and request.user.email == email)

        if getattr(request, 'limited', False):
            return Response({'error_code': 'rate-limited'}, status=403)

        if get_email_validation_error(email):
            return Response({'error_code': 'incorrect-email'}, status=400)

        if not program_uuid:
            return Response({'error_code': 'program-uuid-missing'}, status=400)

        program = get_programs(uuid=program_uuid)
        SavedProgram.objects.update_or_create(
            email=email,
            program_uuid=program_uuid,
            defaults={
                'user_id': user.id,
                'reminder_email_sent': False,
            }
        )
        if program:
            program_data = {
                'program': program,
                'send_to_self': send_to_self,
                'user_id': user_id,
                'pref-lang': pref_lang,
                'type': 'program',
                'reminder': False,
                'braze_event': USER_SEND_SAVE_FOR_LATER_EMAIL,
            }
            if send_email(email, program_data):
                return Response({'result': 'success'}, status=200)
            else:
                return Response({'error_code': 'email-not-send'}, status=400)

        return Response({'error_code': 'program-not-found'}, status=404)
