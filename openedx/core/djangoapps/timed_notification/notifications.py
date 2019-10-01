from openedx.core.djangoapps.timed_notification.core import get_course_link
from openedx.features.ondemand_email_preferences.helpers import get_chapters_text
from student.models import ENROLL_STATUS_CHANGE, EnrollStatusChange
from lms.djangoapps.philu_api.helpers import get_course_custom_settings
from xmodule.modulestore.django import modulestore
from django.dispatch import receiver
from common.lib.mandrill_client.client import MandrillClient
from django.conf import settings


@receiver(ENROLL_STATUS_CHANGE)
def enrollment_confirmation(sender, event=None, user=None, **kwargs):
    if event == EnrollStatusChange.enroll:
        course = modulestore().get_course(kwargs.get('course_id'))

        is_enrollment_email_enabled = True
        custom_settings = get_course_custom_settings(course.id)
        if custom_settings:
            is_enrollment_email_enabled = custom_settings.enable_enrollment_email

        context = {
            'course_name': course.display_name,
            # TODO: find a way to move this code to PhilU overrides
            'course_url': get_course_link(course_id=course.id),
        }

        subject = None
        if is_enrollment_email_enabled:
            if course.self_paced:
                template = MandrillClient.ON_DEMAND_SCHEDULE_EMAIL_TEMPLATE
                context.update(
                    {'module_list': get_chapters_text(course.id, user),
                     'first_name': user.first_name}
                )
                subject = 'Welcome to %s!' % course.display_name
            else:
                template = MandrillClient.ENROLLMENT_CONFIRMATION_TEMPLATE
                context.update(
                    {'signin_url': settings.LMS_ROOT_URL + '/login',
                     'full_name': user.first_name + " " + user.last_name}
                )
            MandrillClient().send_mail(
                template,
                user.email,
                context,
                subject=subject
            )
