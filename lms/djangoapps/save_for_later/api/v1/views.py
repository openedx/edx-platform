"""
Save for later views
"""

from datetime import datetime
import logging

from django.conf import settings
from django.utils.decorators import method_decorator
from ratelimit.decorators import ratelimit
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from opaque_keys.edx.keys import CourseKey
from braze.client import BrazeClient
from eventtracking import tracker

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.user_api.accounts.api import get_email_validation_error
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

from lms.djangoapps.save_for_later.models import SavedCourse

log = logging.getLogger(__name__)

POST_EMAIL_KEY = 'openedx.core.djangoapps.util.ratelimit.request_data_email'
REAL_IP_KEY = 'openedx.core.djangoapps.util.ratelimit.real_ip'
USER_SENT_EMAIL_SAVE_FOR_LATER = 'edx.bi.user.save.for.later.email.sent'


class SaveForLaterApiView(APIView):
    """
    API VIEW
    """
    @transaction.atomic
    @method_decorator(ratelimit(key=POST_EMAIL_KEY, rate=settings.SAVE_FOR_LATER_EMAIL_RATE_LIMIT, method='POST'))
    @method_decorator(ratelimit(key=REAL_IP_KEY, rate=settings.SAVE_FOR_LATER_IP_RATE_LIMIT, method='POST'))
    def post(self, request):
        """
        **Use Case**

            * Send favorite course through email to user for later learning.

        **Example Request**

            POST /api/v1/save/course/

        **Example POST Request**

            {
                "email": "test@edx.org",
                "course_id": "course-v1:edX+DemoX+2021",
                "marketing_url": "https://test.com",
                "org_img_url": "https://test.com/logo.png"

            }
        """
        user = request.user
        data = request.data
        course_id = data.get('course_id')
        email = data.get('email')
        marketing_url = data.get('marketing_url')
        org_img_url = data.get('org_img_url')

        course_key = CourseKey.from_string(course_id)

        if getattr(request, 'limited', False):
            return Response({'error_code': 'rate-limited'}, status=403)

        if get_email_validation_error(email):
            return Response({'error_code': 'incorrect-email'}, status=400)

        try:
            course_overview = CourseOverview.get_from_id(course_key)
            SavedCourse.objects.update_or_create(
                user_id=user.id,
                email=email,
                course_id=course_id,
            )
        except CourseOverview.DoesNotExist:
            return Response({'error_code': 'course-not-found'}, status=404)

        lms_url = configuration_helpers.get_value('LMS_ROOT_URL', settings.LMS_ROOT_URL)
        event_properties = {
            'time': datetime.now().isoformat(),
            'name': 'user.send.save.for.later.email',
            'properties': {
                'course_image_url': '{base_url}{image_path}'.format(
                    base_url=lms_url, image_path=course_overview.course_image_url
                ),
                'partner_image_url': org_img_url,
                'enroll_course_url': '{base_url}/register?course_id={course_id}&enrollment_action=enroll&email_opt_in='
                                     'false&save_for_later=true'.format(base_url=lms_url, course_id=course_key),
                'view_course_url': marketing_url + '?save_for_later=true' if marketing_url else '#',
                'display_name': course_overview.display_name,
                'short_description': course_overview.short_description,
            }
        }

        braze_client = BrazeClient(
            api_key=settings.EDX_BRAZE_API_KEY,
            api_url=settings.EDX_BRAZE_API_SERVER,
            app_id='',
        )

        try:
            attributes = None
            external_id = braze_client.get_braze_external_id(email)
            if external_id:
                event_properties.update({'external_id': external_id})
            else:
                braze_client.create_braze_alias(emails=[email], alias_label='save_for_later')
                user_alias = {
                    'alias_label': 'save_for_later',
                    'alias_name': email,
                }
                event_properties.update({'user_alias': user_alias})
                attributes = [{
                    'user_alias': user_alias,
                    'pref-lang': request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME, 'en')
                }]

            braze_client.track_user(events=[event_properties], attributes=attributes)
            tracker.emit(
                USER_SENT_EMAIL_SAVE_FOR_LATER,
                {
                    'user_id': user.id,
                    'category': 'save-for-later',
                    'type': 'course' if course_id else 'program',
                    'send_to_self': bool(not user.is_anonymous and user.email == email),
                }
            )
        except Exception:  # pylint: disable=broad-except
            log.warning('Unable to send save for later email ', exc_info=True)
            return Response({'error_code': 'email-not-send'}, status=400)
        else:
            return Response({'result': 'success'}, status=200)
