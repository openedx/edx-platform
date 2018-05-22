from common.djangoapps.student.views import get_course_related_keys
from django.core.urlresolvers import reverse
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from openedx.core.djangoapps.models.course_details import CourseDetails
from lms.djangoapps.courseware.courses import get_course_by_id
from student.models import Registration
from util.json_request import JsonResponse
from util.request import safe_get_host
from common.lib.mandrill_client.client import MandrillClient
from crum import get_current_request
from django.conf import settings


def get_course_details(course_id):
    course_descriptor = get_course_by_id(course_id)
    course = CourseDetails.populate(course_descriptor)
    return course


def send_account_activation_email(request, registration, user):
    activation_link = '{protocol}://{site}/activate/{key}'.format(
            protocol='https' if request.is_secure() else 'http',
            site=safe_get_host(request),
            key=registration.activation_key
        )

    context = {
        'first_name': user.first_name,
        'activation_link': activation_link,
    }
    MandrillClient().send_mail(MandrillClient.USER_ACCOUNT_ACTIVATION_TEMPLATE, user.email, context)


def reactivation_email_for_user_custom(request, user):
    try:
        reg = Registration.objects.get(user=user)
        send_account_activation_email(request, reg, user)
    except Registration.DoesNotExist:
        return JsonResponse({
            "success": False,
            "error": _('No inactive user with this e-mail exists'),
        })  # TODO: this should be status code 400  # pylint: disable=fixme


def get_course_first_chapter_link(course):
    course_key = SlashSeparatedCourseKey.from_deprecated_string(
        course.id.to_deprecated_string())

    request = get_current_request()

    first_chapter_url, first_section = get_course_related_keys(
        request, get_course_by_id(course_key, 0))
    first_target = reverse('courseware_section', args=[
        course.id.to_deprecated_string(),
        first_chapter_url,
        first_section
    ])
    base_url = settings.LMS_ROOT_URL
    return base_url + first_target


