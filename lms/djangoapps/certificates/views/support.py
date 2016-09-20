"""
Certificate end-points used by the student support UI.

See lms/djangoapps/support for more details.

"""
import logging
import urllib
from functools import wraps

from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseServerError
)
from django.views.decorators.http import require_GET, require_POST
from django.db import transaction
from django.db.models import Q
from django.utils.translation import ugettext as _

from certificates import api
from certificates.models import CertificateInvalidation
from courseware.access import has_access
from instructor_task.api import generate_certificates_for_students
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from student.models import User, CourseEnrollment
from util.json_request import JsonResponse
from xmodule.modulestore.django import modulestore


log = logging.getLogger(__name__)


def require_certificate_permission(func):
    """
    View decorator that requires permission to view and regenerate certificates.
    """
    @wraps(func)
    def inner(request, *args, **kwargs):  # pylint:disable=missing-docstring
        if has_access(request.user, "certificates", "global"):
            return func(request, *args, **kwargs)
        else:
            return HttpResponseForbidden()

    return inner


@require_GET
@require_certificate_permission
def search_certificates(request):
    """
    Search for certificates for a particular user OR along with the given course.

    Supports search by either username or email address along with course id.

    First filter the records for the given username/email and then filter against the given course id (if given).
    Show the 'Regenerate' button if a record found in 'generatedcertificate' model otherwise it will show the Generate
    button.

    Arguments:
        request (HttpRequest): The request object.

    Returns:
        JsonResponse

    Example Usage:
        GET /certificates/search?user=bob@example.com
        GET /certificates/search?user=bob@example.com&course_id=xyz

        Response: 200 OK
        Content-Type: application/json
        [
            {
                "username": "bob",
                "course_key": "edX/DemoX/Demo_Course",
                "type": "verified",
                "status": "downloadable",
                "download_url": "http://www.example.com/cert.pdf",
                "grade": "0.98",
                "created": 2015-07-31T00:00:00Z,
                "modified": 2015-07-31T00:00:00Z
            }
        ]

    """
    user_filter = urllib.unquote(urllib.quote_plus(request.GET.get("user", "")))
    if not user_filter:
        msg = _("user is not given.")
        return HttpResponseBadRequest(msg)

    try:
        user = User.objects.get(Q(email=user_filter) | Q(username=user_filter))
    except User.DoesNotExist:
        return HttpResponseBadRequest(_("user '{user}' does not exist").format(user=user_filter))

    certificates = api.get_certificates_for_user(user.username)
    for cert in certificates:
        cert["course_key"] = unicode(cert["course_key"])
        cert["created"] = cert["created"].isoformat()
        cert["modified"] = cert["modified"].isoformat()
        cert["regenerate"] = True

    course_id = urllib.quote_plus(request.GET.get("course_id", ""), safe=':/')
    if course_id:
        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            return HttpResponseBadRequest(_("Course id '{course_id}' is not valid").format(course_id=course_id))
        else:
            try:
                if CourseOverview.get_from_id(course_key):
                    certificates = [certificate for certificate in certificates
                                    if certificate['course_key'] == course_id]
                    if not certificates:
                        return JsonResponse([{'username': user.username, 'course_key': course_id, 'regenerate': False}])
            except CourseOverview.DoesNotExist:
                msg = _("The course does not exist against the given key '{course_key}'").format(course_key=course_key)
                return HttpResponseBadRequest(msg)

    return JsonResponse(certificates)


def _validate_post_params(params):
    """
    Validate request POST parameters to the generate and regenerate certificates end-point.

    Arguments:
        params (QueryDict): Request parameters.

    Returns: tuple of (dict, HttpResponse)

    """
    # Validate the username
    try:
        username = params.get("username")
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        msg = _("User {username} does not exist").format(username=username)
        return None, HttpResponseBadRequest(msg)

    # Validate the course key
    try:
        course_key = CourseKey.from_string(params.get("course_key"))
    except InvalidKeyError:
        msg = _("{course_key} is not a valid course key").format(course_key=params.get("course_key"))
        return None, HttpResponseBadRequest(msg)

    return {"user": user, "course_key": course_key}, None


# Grades can potentially be written - if so, let grading manage the transaction.
@transaction.non_atomic_requests
@require_POST
@require_certificate_permission
def regenerate_certificate_for_user(request):
    """
    Regenerate certificates for a user.

    This is meant to be used by support staff through the UI in lms/djangoapps/support

    Arguments:
        request (HttpRequest): The request object

    Returns:
        HttpResponse

    Example Usage:

        POST /certificates/regenerate
            * username: "bob"
            * course_key: "edX/DemoX/Demo_Course"

        Response: 200 OK

    """
    # Check the POST parameters, returning a 400 response if they're not valid.
    params, response = _validate_post_params(request.POST)
    if response is not None:
        return response

    # Check that the course exists
    course = modulestore().get_course(params["course_key"])
    if course is None:
        msg = _("The course {course_key} does not exist").format(course_key=params["course_key"])
        return HttpResponseBadRequest(msg)

    # Check that the user is enrolled in the course
    if not CourseEnrollment.is_enrolled(params["user"], params["course_key"]):
        msg = _("User {username} is not enrolled in the course {course_key}").format(
            username=params["user"].username,
            course_key=params["course_key"]
        )
        return HttpResponseBadRequest(msg)

    # Attempt to regenerate certificates
    try:
        certificate = api.regenerate_user_certificates(params["user"], params["course_key"], course=course)
    except:  # pylint: disable=bare-except
        # We are pessimistic about the kinds of errors that might get thrown by the
        # certificates API.  This may be overkill, but we're logging everything so we can
        # track down unexpected errors.
        log.exception(
            "Could not regenerate certificates for user %s in course %s",
            params["user"].id,
            params["course_key"]
        )
        return HttpResponseServerError(_("An unexpected error occurred while regenerating certificates."))

    # Deactivate certificate invalidation by setting active to False.
    _deactivate_invalidation(certificate)

    log.info(
        "Started regenerating certificates for user %s in course %s from the support page.",
        params["user"].id, params["course_key"]
    )
    return HttpResponse(200)


@transaction.non_atomic_requests
@require_POST
@require_certificate_permission
def generate_certificate_for_user(request):
    """
    Generate certificates for a user.

    This is meant to be used by support staff through the UI in lms/djangoapps/support

    Arguments:
        request (HttpRequest): The request object

    Returns:
        HttpResponse

    Example Usage:

        POST /certificates/generate
            * username: "bob"
            * course_key: "edX/DemoX/Demo_Course"

        Response: 200 OK

    """
    # Check the POST parameters, returning a 400 response if they're not valid.
    params, response = _validate_post_params(request.POST)
    if response is not None:
        return response

    try:
        # Check that the course exists
        CourseOverview.get_from_id(params["course_key"])
    except CourseOverview.DoesNotExist:
        msg = _("The course {course_key} does not exist").format(course_key=params["course_key"])
        return HttpResponseBadRequest(msg)
    else:
        # Check that the user is enrolled in the course
        if not CourseEnrollment.is_enrolled(params["user"], params["course_key"]):
            msg = _("User {username} is not enrolled in the course {course_key}").format(
                username=params["user"].username,
                course_key=params["course_key"]
            )
            return HttpResponseBadRequest(msg)

        # Attempt to generate certificate
        generate_certificates_for_students(
            request,
            params["course_key"],
            student_set="specific_student",
            specific_student_id=params["user"].id
        )
        return HttpResponse(200)


def _deactivate_invalidation(certificate):
    """
    Deactivate certificate invalidation by setting active to False.

    Arguments:
        certificate : The student certificate object

    Return:
        None
    """
    try:
        # Fetch CertificateInvalidation object
        certificate_invalidation = CertificateInvalidation.objects.get(
            generated_certificate=certificate,
            active=True
        )
        # Deactivate certificate invalidation if it was fetched successfully.
        certificate_invalidation.deactivate()
    except CertificateInvalidation.DoesNotExist:  # pylint: disable=bare-except
        pass
