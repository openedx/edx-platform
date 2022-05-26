"""
PhilU overrides the courseware views
"""
import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST
from opaque_keys.edx.keys import CourseKey

from certificates import api as certs_api
from common.lib.mandrill_client.client import MandrillClient
from common.lib.hubspot_client.client import HubSpotClient
from common.lib.hubspot_client.tasks import task_send_hubspot_email
from lms.djangoapps.certificates.api import get_certificate_url
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.timed_notification.core import get_course_link
from xmodule.modulestore.django import modulestore

log = logging.getLogger("edx.courseware")


@transaction.non_atomic_requests
@require_POST
def generate_user_cert(request, course_id):
    """Start generating a new certificate for the user.

    Certificate generation is allowed if:
    * The user has passed the course, and
    * The user does not already have a pending/completed certificate.

    Note that if an error occurs during certificate generation
    (for example, if the queue is down), then we simply mark the
    certificate generation task status as "error" and re-run
    the task with a management command.  To students, the certificate
    will appear to be "generating" until it is re-run.

    Args:
        request (HttpRequest): The POST request to this view.
        course_id (unicode): The identifier for the course.

    Returns:
        HttpResponse: 200 on success, 400 if a new certificate cannot be generated.

    """
    from lms.djangoapps.courseware.views.views import is_course_passed, _track_successful_certificate_generation

    if not request.user.is_authenticated():
        log.info(u"Anon user trying to generate certificate for %s", course_id)
        return HttpResponseBadRequest(
            _('You must be signed in to {platform_name} to create a certificate.').format(
                platform_name=configuration_helpers.get_value('PLATFORM_NAME', settings.PLATFORM_NAME)
            )
        )

    student_id = request.POST.get('student_id')
    student = request.user

    if request.user.is_staff and student_id:
        try:
            student = User.objects.get(id=student_id)
        except User.DoesNotExist:
            raise Http404

    course_key = CourseKey.from_string(course_id)

    course = modulestore().get_course(course_key, depth=2)
    if not course:
        return HttpResponseBadRequest(_("Course is not valid"))

    if not is_course_passed(student, course):
        return HttpResponseBadRequest(_("Your certificate will be available when you pass the course."))

    certificate_status = certs_api.certificate_downloadable_status(student, course.id)

    if certificate_status["is_downloadable"]:
        return HttpResponseBadRequest(_("Certificate has already been created."))
    elif certificate_status["is_generating"]:
        return HttpResponseBadRequest(_("Certificate is being created."))
    else:
        # If the certificate is not already in-process or completed,
        # then create a new certificate generation task.
        # If the certificate cannot be added to the queue, this will
        # mark the certificate with "error" status, so it can be re-run
        # with a management command.  From the user's perspective,
        # it will appear that the certificate task was submitted successfully.
        base_url = settings.LMS_ROOT_URL

        context = {
            'emailId': HubSpotClient.COURSE_COMPLETION,
            'message': {
                'to': student.email
            },
            'customProperties': {
                'course_name': course.display_name,
                'course_url': get_course_link(course_id=course.id),
                'full_name': student.first_name + ' ' + student.last_name,
                'certificate_url': base_url + get_certificate_url(user_id=student.id, course_id=course.id),
                'course_library_url': base_url + '/courses'
            }
        }
        task_send_hubspot_email.delay(context)

        certs_api.generate_user_certificates(student, course.id, course=course, generation_mode='self')
        _track_successful_certificate_generation(student.id, course.id)
        return HttpResponse()


def get_course_related_keys(request, course):
    """
        Get course first chapter & first section keys
    """
    from courseware.model_data import FieldDataCache
    from lms.djangoapps.courseware.module_render import get_module_for_descriptor

    first_chapter_url = ""
    first_section = ""

    field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
        course.id, request.user, course, depth=2,
    )
    course_module = get_module_for_descriptor(
        request.user, request, course, field_data_cache, course.id, course=course
    )

    chapters = course_module.get_display_items()
    if chapters:
        first_chapter = chapters[0]
        first_chapter_url = first_chapter.url_name
        subsections = first_chapter.get_display_items()
        first_section = subsections[0].url_name if subsections else ""

    return first_chapter_url, first_section
