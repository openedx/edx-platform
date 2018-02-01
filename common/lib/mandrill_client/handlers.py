
from openedx.core.djangoapps.signals.signals import COURSE_CERT_AWARDED
from django.dispatch import receiver
from core import get_course_link
from lms.djangoapps.courseware.courses import get_course
from lms.djangoapps.certificates.api import get_certificate_url
from common.lib.mandrill_client.client import MandrillClient


@receiver(COURSE_CERT_AWARDED)
def handle_course_cert_awarded(sender, user, course_key, mode, status, **kwargs):
    course = get_course(course_key)
    context = {
        'course_name': course.display_name,
        'course_url': get_course_link(course_id=course.id),
        'full_name': user.first_name + " " + user.last_name,
        'certificate_url': get_certificate_url(user_id=user.id, course_id=course.id)
    }
    MandrillClient().send_mail(
        MandrillClient.COURSE_COMPLETION_TEMPLATE,
        user.email,
        context
    )
