
from openedx.core.djangoapps.signals.signals import COURSE_CERT_AWARDED
from core import get_course_link
from lms.djangoapps.courseware.courses import get_course
from common.lib.mandrill_client.client import MandrillClient

@receiver(COURSE_CERT_AWARDED)
def handle_course_cert_awarded(sender, user, course_key, mode, status, **kwargs):
    course = get_course(course_key)
    context = {
        'course_name': course.display_name,
        'course_link': get_course_link(course_id=course.id),
        'full_name': user.extended_profile.first_name + " " + user.\
        extended_profile.last_name
    }
    MandrillClient().send_course_notification_email(
        user.email,
        template_name='course-completion',
        context=context
    )
