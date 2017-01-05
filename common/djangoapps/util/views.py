import json
import logging
from smtplib import SMTPException
import sys
from functools import wraps

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.cache import caches
from django.core.mail import send_mail
from django.core.validators import ValidationError, validate_email
from django.views.decorators.csrf import requires_csrf_token
from django.views.defaults import server_error
from django.http import (Http404, HttpResponse, HttpResponseNotAllowed,
                         HttpResponseServerError, HttpResponseForbidden)
import dogstats_wrapper as dog_stats_api
import zendesk
import calc

from opaque_keys import InvalidKeyError

from opaque_keys.edx.keys import CourseKey, UsageKey

from edxmako.shortcuts import render_to_response, render_to_string
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
import track.views
from student.roles import GlobalStaff
from student.models import CourseEnrollment

log = logging.getLogger(__name__)

DATADOG_FEEDBACK_METRIC = "lms_feedback_submissions"
SUPPORT_BACKEND_ZENDESK = "support_ticket"
SUPPORT_BACKEND_EMAIL = "email"


def ensure_valid_course_key(view_func):
    """
    This decorator should only be used with views which have argument course_key_string (studio) or course_id (lms).
    If course_key_string (studio) or course_id (lms) is not valid raise 404.
    """
    @wraps(view_func)
    def inner(request, *args, **kwargs):
        course_key = kwargs.get('course_key_string') or kwargs.get('course_id')
        if course_key is not None:
            try:
                CourseKey.from_string(course_key)
            except InvalidKeyError:
                raise Http404

        response = view_func(request, *args, **kwargs)
        return response

    return inner


def ensure_valid_usage_key(view_func):
    """
    This decorator should only be used with views which have argument usage_key_string.
    If usage_key_string is not valid raise 404.
    """
    @wraps(view_func)
    def inner(request, *args, **kwargs):  # pylint: disable=missing-docstring
        usage_key = kwargs.get('usage_key_string')
        if usage_key is not None:
            try:
                UsageKey.from_string(usage_key)
            except InvalidKeyError:
                raise Http404

        response = view_func(request, *args, **kwargs)
        return response

    return inner


def require_global_staff(func):
    """View decorator that requires that the user have global staff permissions. """
    @wraps(func)
    def wrapped(request, *args, **kwargs):  # pylint: disable=missing-docstring
        if GlobalStaff().has_user(request.user):
            return func(request, *args, **kwargs)
        else:
            return HttpResponseForbidden(
                u"Must be {platform_name} staff to perform this action.".format(
                    platform_name=settings.PLATFORM_NAME
                )
            )
    return login_required(wrapped)


@requires_csrf_token
def jsonable_server_error(request, template_name='500.html'):
    """
    500 error handler that serves JSON on an AJAX request, and proxies
    to the Django default `server_error` view otherwise.
    """
    if request.is_ajax():
        msg = {"error": "The edX servers encountered an error"}
        return HttpResponseServerError(json.dumps(msg))
    else:
        return server_error(request, template_name=template_name)


def handle_500(template_path, context=None, test_func=None):
    """
    Decorator for view specific 500 error handling.
    Custom handling will be skipped only if test_func is passed and it returns False

    Usage:

        @handle_500(
            template_path='certificates/server-error.html',
            context={'error-info': 'Internal Server Error'},
            test_func=lambda request: request.GET.get('preview', None)
        )
        def my_view(request):
            # Any unhandled exception in this view would be handled by the handle_500 decorator
            # ...

    """
    def decorator(func):
        """
        Decorator to render custom html template in case of uncaught exception in wrapped function
        """
        @wraps(func)
        def inner(request, *args, **kwargs):
            """
            Execute the function in try..except block and return custom server-error page in case of unhandled exception
            """
            try:
                return func(request, *args, **kwargs)
            except Exception:  # pylint: disable=broad-except
                if settings.DEBUG:
                    # In debug mode let django process the 500 errors and display debug info for the developer
                    raise
                elif test_func is None or test_func(request):
                    # Display custom 500 page if either
                    #   1. test_func is None (meaning nothing to test)
                    #   2. or test_func(request) returns True
                    log.exception("Error in django view.")
                    return render_to_response(template_path, context)
                else:
                    # Do not show custom 500 error when test fails
                    raise
        return inner
    return decorator


def calculate(request):
    ''' Calculator in footer of every page. '''
    equation = request.GET['equation']
    try:
        result = calc.evaluator({}, {}, equation)
    except:
        event = {'error': map(str, sys.exc_info()),
                 'equation': equation}
        track.views.server_track(request, 'error:calc', event, page='calc')
        return HttpResponse(json.dumps({'result': 'Invalid syntax'}))
    return HttpResponse(json.dumps({'result': str(result)}))


class _ZendeskApi(object):

    CACHE_PREFIX = 'ZENDESK_API_CACHE'
    CACHE_TIMEOUT = 60 * 60

    def __init__(self):
        """
        Instantiate the Zendesk API.

        All of `ZENDESK_URL`, `ZENDESK_USER`, and `ZENDESK_API_KEY` must be set
        in `django.conf.settings`.
        """
        self._zendesk_instance = zendesk.Zendesk(
            settings.ZENDESK_URL,
            settings.ZENDESK_USER,
            settings.ZENDESK_API_KEY,
            use_api_token=True,
            api_version=2,
            # As of 2012-05-08, Zendesk is using a CA that is not
            # installed on our servers
            client_args={"disable_ssl_certificate_validation": True}
        )

    def create_ticket(self, ticket):
        """
        Create the given `ticket` in Zendesk.

        The ticket should have the format specified by the zendesk package.
        """
        ticket_url = self._zendesk_instance.create_ticket(data=ticket)
        return zendesk.get_id_from_url(ticket_url)

    def update_ticket(self, ticket_id, update):
        """
        Update the Zendesk ticket with id `ticket_id` using the given `update`.

        The update should have the format specified by the zendesk package.
        """
        self._zendesk_instance.update_ticket(ticket_id=ticket_id, data=update)

    def get_group(self, name):
        """
        Find the Zendesk group named `name`. Groups are cached for
        CACHE_TIMEOUT seconds.

        If a matching group exists, it is returned as a dictionary
        with the format specifed by the zendesk package.

        Otherwise, returns None.
        """
        cache = caches['default']
        cache_key = '{prefix}_group_{name}'.format(prefix=self.CACHE_PREFIX, name=name)
        cached = cache.get(cache_key)
        if cached:
            return cached
        groups = self._zendesk_instance.list_groups()['groups']
        for group in groups:
            if group['name'] == name:
                cache.set(cache_key, group, self.CACHE_TIMEOUT)
                return group
        return None


def _get_zendesk_custom_field_context(request):
    """
    Construct a dictionary of data that can be stored in Zendesk custom fields.
    """
    context = {}

    course_id = request.POST.get("course_id")
    if not course_id:
        return context

    context["course_id"] = course_id
    if not request.user.is_authenticated():
        return context

    enrollment = CourseEnrollment.get_enrollment(request.user, CourseKey.from_string(course_id))
    if enrollment and enrollment.is_active:
        context["enrollment_mode"] = enrollment.mode

    return context


def _format_zendesk_custom_fields(context):
    """
    Format the data in `context` for compatibility with the Zendesk API.
    Ignore any keys that have not been configured in `ZENDESK_CUSTOM_FIELDS`.
    """
    custom_fields = []
    for key, val, in settings.ZENDESK_CUSTOM_FIELDS.items():
        if key in context:
            custom_fields.append({"id": val, "value": context[key]})

    return custom_fields


def _record_feedback_in_zendesk(
        realname,
        email,
        subject,
        details,
        tags,
        additional_info,
        group_name=None,
        require_update=False,
        support_email=None,
        custom_fields=None
):
    """
    Create a new user-requested Zendesk ticket.

    Once created, the ticket will be updated with a private comment containing
    additional information from the browser and server, such as HTTP headers
    and user state. Returns a boolean value indicating whether ticket creation
    was successful, regardless of whether the private comment update succeeded.

    If `group_name` is provided, attaches the ticket to the matching Zendesk group.

    If `require_update` is provided, returns False when the update does not
    succeed. This allows using the private comment to add necessary information
    which the user will not see in followup emails from support.

    If `custom_fields` is provided, submits data to those fields in Zendesk.
    """
    zendesk_api = _ZendeskApi()

    additional_info_string = (
        u"Additional information:\n\n" +
        u"\n".join(u"%s: %s" % (key, value) for (key, value) in additional_info.items() if value is not None)
    )

    # Tag all issues with LMS to distinguish channel in Zendesk; requested by student support team
    zendesk_tags = list(tags.values()) + ["LMS"]

    # Per edX support, we would like to be able to route white label feedback items
    # via tagging
    white_label_org = configuration_helpers.get_value('course_org_filter')
    if white_label_org:
        zendesk_tags = zendesk_tags + ["whitelabel_{org}".format(org=white_label_org)]

    new_ticket = {
        "ticket": {
            "requester": {"name": realname, "email": email},
            "subject": subject,
            "comment": {"body": details},
            "tags": zendesk_tags
        }
    }

    if custom_fields:
        new_ticket["ticket"]["custom_fields"] = custom_fields

    group = None
    if group_name is not None:
        group = zendesk_api.get_group(group_name)
        if group is not None:
            new_ticket['ticket']['group_id'] = group['id']
    if support_email is not None:
        # If we do not include the `recipient` key here, Zendesk will default to using its default reply
        # email address when support agents respond to tickets. By setting the `recipient` key here,
        # we can ensure that WL site users are responded to via the correct Zendesk support email address.
        new_ticket['ticket']['recipient'] = support_email
    try:
        ticket_id = zendesk_api.create_ticket(new_ticket)
        if group_name is not None and group is None:
            # Support uses Zendesk groups to track tickets. In case we
            # haven't been able to correctly group this ticket, log its ID
            # so it can be found later.
            log.warning('Unable to find group named %s for Zendesk ticket with ID %s.', group_name, ticket_id)
    except zendesk.ZendeskError:
        log.exception("Error creating Zendesk ticket")
        return False

    # Additional information is provided as a private update so the information
    # is not visible to the user.
    ticket_update = {"ticket": {"comment": {"public": False, "body": additional_info_string}}}
    try:
        zendesk_api.update_ticket(ticket_id, ticket_update)
    except zendesk.ZendeskError:
        log.exception("Error updating Zendesk ticket with ID %s.", ticket_id)
        # The update is not strictly necessary, so do not indicate
        # failure to the user unless it has been requested with
        # `require_update`.
        if require_update:
            return False
    return True


def _record_feedback_in_datadog(tags):
    datadog_tags = [u"{k}:{v}".format(k=k, v=v) for k, v in tags.items()]
    dog_stats_api.increment(DATADOG_FEEDBACK_METRIC, tags=datadog_tags)


def get_feedback_form_context(request):
    """
    Extract the submitted form fields to be used as a context for
    feedback submission.
    """
    context = {}

    context["subject"] = request.POST["subject"]
    context["details"] = request.POST["details"]
    context["tags"] = dict(
        [(tag, request.POST[tag]) for tag in ["issue_type", "course_id"] if tag in request.POST]
    )

    context["additional_info"] = {}

    if request.user.is_authenticated():
        context["realname"] = request.user.profile.name
        context["email"] = request.user.email
        context["additional_info"]["username"] = request.user.username
    else:
        context["realname"] = request.POST["name"]
        context["email"] = request.POST["email"]

    for header, pretty in [("HTTP_REFERER", "Page"), ("HTTP_USER_AGENT", "Browser"), ("REMOTE_ADDR", "Client IP"),
                           ("SERVER_NAME", "Host")]:
        context["additional_info"][pretty] = request.META.get(header)

    context["support_email"] = configuration_helpers.get_value('email_from_address', settings.DEFAULT_FROM_EMAIL)

    return context


def submit_feedback(request):
    """
    Create a Zendesk ticket or if not available, send an email with the
    feedback form fields.

    If feedback submission is not enabled, any request will raise `Http404`.
    If any configuration parameter (`ZENDESK_URL`, `ZENDESK_USER`, or
    `ZENDESK_API_KEY`) is missing, any request will raise an `Exception`.
    The request must be a POST request specifying `subject` and `details`.
    If the user is not authenticated, the request must also specify `name` and
    `email`. If the user is authenticated, the `name` and `email` will be
    populated from the user's information. If any required parameter is
    missing, a 400 error will be returned indicating which field is missing and
    providing an error message. If Zendesk ticket creation fails, 500 error
    will be returned with no body; if ticket creation succeeds, an empty
    successful response (200) will be returned.
    """
    if not settings.FEATURES.get('ENABLE_FEEDBACK_SUBMISSION', False):
        raise Http404()
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    def build_error_response(status_code, field, err_msg):
        return HttpResponse(json.dumps({"field": field, "error": err_msg}), status=status_code)

    required_fields = ["subject", "details"]

    if not request.user.is_authenticated():
        required_fields += ["name", "email"]

    required_field_errs = {
        "subject": "Please provide a subject.",
        "details": "Please provide details.",
        "name": "Please provide your name.",
        "email": "Please provide a valid e-mail.",
    }
    for field in required_fields:
        if field not in request.POST or not request.POST[field]:
            return build_error_response(400, field, required_field_errs[field])

    if not request.user.is_authenticated():
        try:
            validate_email(request.POST["email"])
        except ValidationError:
            return build_error_response(400, "email", required_field_errs["email"])

    success = False
    context = get_feedback_form_context(request)
    support_backend = configuration_helpers.get_value('CONTACT_FORM_SUBMISSION_BACKEND', SUPPORT_BACKEND_ZENDESK)

    if support_backend == SUPPORT_BACKEND_EMAIL:
        try:
            send_mail(
                subject=render_to_string('emails/contact_us_feedback_email_subject.txt', context),
                message=render_to_string('emails/contact_us_feedback_email_body.txt', context),
                from_email=context["support_email"],
                recipient_list=[context["support_email"]],
                fail_silently=False
            )
            success = True
        except SMTPException:
            log.exception('Error sending feedback to contact_us email address.')
            success = False

    else:
        if not settings.ZENDESK_URL or not settings.ZENDESK_USER or not settings.ZENDESK_API_KEY:
            raise Exception("Zendesk enabled but not configured")

        custom_fields = None
        if settings.ZENDESK_CUSTOM_FIELDS:
            custom_field_context = _get_zendesk_custom_field_context(request)
            custom_fields = _format_zendesk_custom_fields(custom_field_context)

        success = _record_feedback_in_zendesk(
            context["realname"],
            context["email"],
            context["subject"],
            context["details"],
            context["tags"],
            context["additional_info"],
            support_email=context["support_email"],
            custom_fields=custom_fields
        )

    _record_feedback_in_datadog(context["tags"])

    return HttpResponse(status=(200 if success else 500))


def info(request):
    ''' Info page (link from main header) '''
    # pylint: disable=unused-argument
    return render_to_response("info.html", {})


# From http://djangosnippets.org/snippets/1042/
def parse_accept_header(accept):
    """Parse the Accept header *accept*, returning a list with pairs of
    (media_type, q_value), ordered by q values.
    """
    result = []
    for media_range in accept.split(","):
        parts = media_range.split(";")
        media_type = parts.pop(0)
        media_params = []
        q = 1.0
        for part in parts:
            (key, value) = part.lstrip().split("=", 1)
            if key == "q":
                q = float(value)
            else:
                media_params.append((key, value))
        result.append((media_type, tuple(media_params), q))
    result.sort(lambda x, y: -cmp(x[2], y[2]))
    return result


def accepts(request, media_type):
    """Return whether this request has an Accept header that matches type"""
    accept = parse_accept_header(request.META.get("HTTP_ACCEPT", ""))
    return media_type in [t for (t, p, q) in accept]


def add_p3p_header(view_func):
    """
    This decorator should only be used with views which may be displayed through the iframe.
    It adds additional headers to response and therefore gives IE browsers an ability to save cookies inside the iframe
    Details:
    http://blogs.msdn.com/b/ieinternals/archive/2013/09/17/simple-introduction-to-p3p-cookie-blocking-frame.aspx
    http://stackoverflow.com/questions/8048306/what-is-the-most-broad-p3p-header-that-will-work-with-ie
    """
    @wraps(view_func)
    def inner(request, *args, **kwargs):
        """
        Helper function
        """
        response = view_func(request, *args, **kwargs)
        response['P3P'] = settings.P3P_HEADER
        return response
    return inner
