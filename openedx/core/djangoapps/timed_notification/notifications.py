from student.models import ENROLL_STATUS_CHANGE, EnrollStatusChange
from xmodule.modulestore.django import modulestore

from core import send_course_notification_email, get_course_link

from django.dispatch import receiver
from common.lib.mandrill_client.client import MandrillClient


@receiver(ENROLL_STATUS_CHANGE)
def enrollment_confirmation(sender, event=None, user=None, **kwargs):
    if event == EnrollStatusChange.enroll:
        course = modulestore().get_course(kwargs.get('course_id'))
        context = {
            'course_name': course.display_name,
            'course_link': get_course_link(course_id=course.id),
            'full_name': user.extended_profile.first_name + " " + user.\
                extended_profile.last_name
        }
        MandrillClient().send_email(
            MandrillClient.ENROLLMENT_CONFIRMATION_TEMPLATE,
            user.email,
            context
        )
