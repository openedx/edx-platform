"""
Save for later views
"""


import logging

from django.conf import settings
from django.utils.decorators import method_decorator
from django.contrib.sites.models import Site
from ratelimit.decorators import ratelimit
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from opaque_keys.edx.keys import CourseKey
from edx_ace import ace
from edx_ace.recipient import Recipient
from eventtracking import tracker

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.user_api.accounts.api import get_email_validation_error
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.ace_common.template_context import get_base_template_context

from lms.djangoapps.save_for_later.message_types import SaveForLater
from lms.djangoapps.save_for_later.models import SavedCourse

log = logging.getLogger(__name__)

POST_EMAIL_KEY = 'post:email'
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
        course_id = request.POST.get('course_id')
        email = request.POST.get('email')
        marketing_url = request.POST.get('marketing_url')
        org_img_url = request.POST.get('org_img_url')

        course_key = CourseKey.from_string(course_id)

        if getattr(request, 'limited', False):
            return Response({'result': 'failure'}, status=403)

        if get_email_validation_error(email):
            return Response({'result': 'failure'}, status=400)

        try:
            course_overview = CourseOverview.get_from_id(course_key)
            SavedCourse.objects.update_or_create(
                user_id=user.id,
                email=email,
                course_id=course_id,
            )
        except CourseOverview.DoesNotExist:
            return Response({'result': 'failure'}, status=404)

        site = Site.objects.get_current()
        message_context = get_base_template_context(site)
        message_context.update({
            'course_image_url': course_overview.course_image_url,
            'partner_image_url': org_img_url,
            'enroll_course_url': '/register?course_id={course_key}&enrollment_action=enroll&email_opt_in=false&'
                                 'save_for_later=true'.format(course_key=course_key),
            'view_course_url': marketing_url + '?save_for_later=true' if marketing_url else '#',
            'course_key': course_key,
            'display_name': course_overview.display_name,
            'short_description': course_overview.short_description,
            'lms_url': configuration_helpers.get_value('LMS_ROOT_URL', settings.LMS_ROOT_URL),
            'from_address': configuration_helpers.get_value('email_from_address', settings.DEFAULT_FROM_EMAIL),
        })

        msg = SaveForLater().personalize(
            recipient=Recipient(lms_user_id=0, email_address=email),
            language=settings.LANGUAGE_CODE,
            user_context=message_context,
        )
        try:
            ace.send(msg)
            tracker.emit(
                USER_SENT_EMAIL_SAVE_FOR_LATER,
                {
                    'user_id': user.id,
                    'category': 'save-for-later',
                    'type': 'course' if course_id else 'program'
                }
            )
        except Exception:  # pylint: disable=broad-except
            log.warning('Unable to send save for later email ', exc_info=True)
            return Response({'result': 'failure'}, status=400)
        else:
            return Response({'result': 'success'}, status=200)
