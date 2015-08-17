"""
LTI Provider view functions
"""

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.core.urlresolvers import reverse
from django.http import HttpResponseBadRequest, HttpResponseForbidden, Http404
from django.views.decorators.csrf import csrf_exempt
import logging

from lti_provider.outcomes import store_outcome_parameters
from lti_provider.models import LtiConsumer
from lti_provider.signature_validator import SignatureValidator
from lti_provider.users import authenticate_lti_user
from lms_xblock.runtime import unquote_slashes
from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys import InvalidKeyError

log = logging.getLogger("edx.lti_provider")


# LTI launch parameters that must be present for a successful launch
REQUIRED_PARAMETERS = [
    'roles', 'context_id', 'oauth_version', 'oauth_consumer_key',
    'oauth_signature', 'oauth_signature_method', 'oauth_timestamp',
    'oauth_nonce', 'user_id'
]

OPTIONAL_PARAMETERS = [
    'lis_result_sourcedid', 'lis_outcome_service_url',
    'tool_consumer_instance_guid'
]

LTI_SESSION_KEY = 'lti_provider_parameters'


@csrf_exempt
def lti_launch(request, course_id, usage_id):
    """
    Endpoint for all requests to embed edX content via the LTI protocol. This
    endpoint will be called by a POST message that contains the parameters for
    an LTI launch (we support version 1.2 of the LTI specification):
        http://www.imsglobal.org/lti/ltiv1p2/ltiIMGv1p2.html

    An LTI launch is successful if:
        - The launch contains all the required parameters
        - The launch data is correctly signed using a known client key/secret
          pair
        - The user is logged into the edX instance

    Authentication in this view is a little tricky, since clients use a POST
    with parameters to fetch it. We can't just use @login_required since in the
    case where a user is not logged in it will redirect back after login using a
    GET request, which would lose all of our LTI parameters.

    Instead, we verify the LTI launch in this view before checking if the user
    is logged in, and store the required LTI parameters in the session. Then we
    do the authentication check, and if login is required we redirect back to
    the lti_run view. If the user is already logged in, we just call that view
    directly.
    """

    if not settings.FEATURES['ENABLE_LTI_PROVIDER']:
        return HttpResponseForbidden()

    # Check the OAuth signature on the message
    try:
        if not SignatureValidator().verify(request):
            return HttpResponseForbidden()
    except LtiConsumer.DoesNotExist:
        return HttpResponseForbidden()

    params = get_required_parameters(request.POST)
    if not params:
        return HttpResponseBadRequest()
    params.update(get_optional_parameters(request.POST))

    # Store the course, and usage ID in the session to prevent privilege
    # escalation if a staff member in one course tries to access material in
    # another.
    try:
        course_key, usage_key = parse_course_and_usage_keys(course_id, usage_id)
    except InvalidKeyError:
        log.error(
            'Invalid course key %s or usage key %s from request %s',
            course_id,
            usage_id,
            request
        )
        raise Http404()
    params['course_key'] = course_key
    params['usage_key'] = usage_key

    try:
        lti_consumer = LtiConsumer.get_or_supplement(
            params.get('tool_consumer_instance_guid', None),
            params['oauth_consumer_key']
        )
    except LtiConsumer.DoesNotExist:
        return HttpResponseForbidden()

    # Create an edX account if the user identifed by the LTI launch doesn't have
    # one already, and log the edX account into the platform.
    authenticate_lti_user(request, params['user_id'], lti_consumer)

    request.session[LTI_SESSION_KEY] = params

    return lti_run(request)


@login_required
def lti_run(request):
    """
    This method can be reached in two ways, and must always follow a POST to
    lti_launch:
     - The user was logged in, so this method was called by lti_launch
     - The user was not logged in, so the login process redirected them back here.

    In either case, the session was populated by lti_launch, so all the required
    LTI parameters will be stored there. Note that the request passed here may
    or may not contain the LTI parameters (depending on how the user got here),
    and so we should only use LTI parameters from the session.

    Users should never call this view directly; if a user attempts to call it
    without having first gone through lti_launch (and had the LTI parameters
    stored in the session) they will get a 403 response.
    """

    # Check the parameters to make sure that the session is associated with a
    # valid LTI launch
    params = restore_params_from_session(request)
    if not params:
        # This view has been called without first setting the session
        return HttpResponseForbidden()
    # Remove the parameters from the session to prevent replay
    del request.session[LTI_SESSION_KEY]

    # Store any parameters required by the outcome service in order to report
    # scores back later. We know that the consumer exists, since the record was
    # used earlier to verify the oauth signature.
    lti_consumer = LtiConsumer.get_or_supplement(
        params.get('tool_consumer_instance_guid', None),
        params['oauth_consumer_key']
    )
    store_outcome_parameters(params, request.user, lti_consumer)

    return render_courseware(request, params['usage_key'])


def get_required_parameters(dictionary, additional_params=None):
    """
    Extract all required LTI parameters from a dictionary and verify that none
    are missing.

    :param dictionary: The dictionary that should contain all required parameters
    :param additional_params: Any expected parameters, beyond those required for
        the LTI launch.

    :return: A new dictionary containing all the required parameters from the
        original dictionary and additional parameters, or None if any expected
        parameters are missing.
    """
    params = {}
    additional_params = additional_params or []
    for key in REQUIRED_PARAMETERS + additional_params:
        if key not in dictionary:
            return None
        params[key] = dictionary[key]
    return params


def get_optional_parameters(dictionary):
    """
    Extract all optional LTI parameters from a dictionary. This method does not
    fail if any parameters are missing.

    :param dictionary: A dictionary containing zero or more optional parameters.
    :return: A new dictionary containing all optional parameters from the
        original dictionary, or an empty dictionary if no optional parameters
        were present.
    """
    return {key: dictionary[key] for key in OPTIONAL_PARAMETERS if key in dictionary}


def restore_params_from_session(request):
    """
    Fetch the parameters that were stored in the session by an LTI launch, and
    verify that all required parameters are present. Missing parameters could
    indicate that a user has directly called the lti_run endpoint, rather than
    going through the LTI launch.

    :return: A dictionary of all LTI parameters from the session, or None if
             any parameters are missing.
    """
    if LTI_SESSION_KEY not in request.session:
        return None
    session_params = request.session[LTI_SESSION_KEY]
    additional_params = ['course_key', 'usage_key']
    for key in REQUIRED_PARAMETERS + additional_params:
        if key not in session_params:
            return None
    return session_params


def render_courseware(request, usage_key):
    """
    Render the content requested for the LTI launch.
    TODO: This method depends on the current refactoring work on the
    courseware/courseware.html template. It's signature may change depending on
    the requirements for that template once the refactoring is complete.

    Return an HttpResponse object that contains the template and necessary
    context to render the courseware.
    """
    # return an HttpResponse object that contains the template and necessary context to render the courseware.
    from courseware.views import render_xblock
    return render_xblock(request, unicode(usage_key), check_if_enrolled=False)


def parse_course_and_usage_keys(course_id, usage_id):
    """
    Convert course and usage ID strings into key objects. Return a tuple of
    (course_key, usage_key), or throw an InvalidKeyError if the translation
    fails.
    """
    course_key = CourseKey.from_string(course_id)
    usage_id = unquote_slashes(usage_id)
    usage_key = UsageKey.from_string(usage_id).map_into_course(course_key)
    return course_key, usage_key
