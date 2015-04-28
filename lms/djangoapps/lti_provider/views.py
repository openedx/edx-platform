"""
LTI Provider view functions
"""

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.core.urlresolvers import reverse
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt

from courseware.access import has_access
from courseware.courses import get_course_with_access
from courseware.module_render import get_module_by_usage_id
from edxmako.shortcuts import render_to_response
from lti_provider.signature_validator import SignatureValidator
from opaque_keys.edx.keys import CourseKey

# LTI launch parameters that must be present for a successful launch
REQUIRED_PARAMETERS = [
    'roles', 'context_id', 'oauth_version', 'oauth_consumer_key',
    'oauth_signature', 'oauth_signature_method', 'oauth_timestamp',
    'oauth_nonce'
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
    if not SignatureValidator().verify(request):
        return HttpResponseForbidden()

    params = get_required_parameters(request.POST)
    if not params:
        return HttpResponseBadRequest()
    # Store the course, and usage ID in the session to prevent privilege
    # escalation if a staff member in one course tries to access material in
    # another.
    params['course_id'] = course_id
    params['usage_id'] = usage_id
    request.session[LTI_SESSION_KEY] = params

    if not request.user.is_authenticated():
        run_url = reverse('lti_provider.views.lti_run')
        return redirect_to_login(run_url, settings.LOGIN_URL)

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

    return render_courseware(request, params)


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
    additional_params = ['course_id', 'usage_id']
    return get_required_parameters(session_params, additional_params)


def render_courseware(request, lti_params):
    """
    Render the content requested for the LTI launch.
    TODO: This method depends on the current refactoring work on the
    courseware/courseware.html template. It's signature may change depending on
    the requirements for that template once the refactoring is complete.

    :return: an HttpResponse object that contains the template and necessary
    context to render the courseware.
    """
    usage_id = lti_params['usage_id']
    course_id = lti_params['course_id']
    course_key = CourseKey.from_string(course_id)
    user = request.user
    course = get_course_with_access(user, 'load', course_key)
    staff = has_access(request.user, 'staff', course)
    instance, _ = get_module_by_usage_id(request, course_id, usage_id)

    fragment = instance.render('student_view', context=request.GET)

    context = {
        'fragment': fragment,
        'course': course,
        'disable_accordion': True,
        'allow_iframing': True,
        'disable_header': True,
        'disable_footer': True,
        'disable_tabs': True,
        'staff_access': staff,
        'xqa_server': settings.FEATURES.get('XQA_SERVER', 'http://your_xqa_server.com'),
    }

    return render_to_response('courseware/courseware.html', context)
