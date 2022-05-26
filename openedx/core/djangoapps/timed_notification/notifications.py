from django.conf import settings
from django.dispatch import receiver

from common.lib.mandrill_client.client import MandrillClient
from lms.djangoapps.philu_api.helpers import get_course_custom_settings
from openedx.core.djangoapps.timed_notification.core import get_course_link
from openedx.features.ondemand_email_preferences.helpers import (
    get_chapters_text,
    send_self_paced_course_enrollment_email
)
from student.models import ENROLL_STATUS_CHANGE, EnrollStatusChange
from xmodule.modulestore.django import modulestore


@receiver(ENROLL_STATUS_CHANGE)
def enrollment_confirmation(sender, event=None, user=None, **kwargs):
    if event == EnrollStatusChange.enroll:
        course = modulestore().get_course(kwargs.get('course_id'))

        is_enrollment_email_enabled = True
        is_mini_lesson = False
        custom_settings = get_course_custom_settings(course.id)
        if custom_settings:
            is_enrollment_email_enabled = custom_settings.enable_enrollment_email
            is_mini_lesson = custom_settings.is_mini_lesson

        # context = {
        #     'course_name': course.display_name,
        #     # TODO: find a way to move this code to PhilU overrides
        #     'course_url': get_course_link(course_id=course.id),
        # }
        #
        # subject = None
        if is_enrollment_email_enabled:
            if is_mini_lesson:
                pass
                # template = MandrillClient.MINI_COURSE_ENROLMENT
                # context.update(
                #     {'full_name': user.get_full_name()}
                # )
            elif course.self_paced:
                course_url = get_course_link(course_id=course.id)
                module_list = get_chapters_text(course.id, user)
                send_self_paced_course_enrollment_email(user, course.display_name, course_url, module_list)
            else:
                pass
                # template = MandrillClient.ENROLLMENT_CONFIRMATION_TEMPLATE
                # context.update(
                #     {'signin_url': settings.LMS_ROOT_URL + '/login',
                #      'full_name': user.get_full_name()}
                # )

