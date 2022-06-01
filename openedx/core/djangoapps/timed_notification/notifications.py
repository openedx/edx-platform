from django.dispatch import receiver

from lms.djangoapps.philu_api.helpers import get_course_custom_settings
from openedx.core.djangoapps.timed_notification.core import get_course_link
from openedx.features.ondemand_email_preferences.helpers import (
    get_chapters_text,
    send_self_paced_course_enrollment_email,
    send_instructor_paced_course_enrollment_email,
    send_mini_course_enrollment_email
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

        course_url = get_course_link(course_id=course.id)
        if is_enrollment_email_enabled:
            if is_mini_lesson:
                send_mini_course_enrollment_email(user, course.display_name, course_url)
            elif course.self_paced:
                module_list = get_chapters_text(course.id, user)
                send_self_paced_course_enrollment_email(user, course.display_name, course_url, module_list)
            else:
                send_instructor_paced_course_enrollment_email(user, course.display_name, course_url)
