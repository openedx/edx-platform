"""
LTI Provider view functions
"""

from django.conf import settings
from django.http import HttpResponseBadRequest, HttpResponseForbidden, Http404
from django.views.decorators.csrf import csrf_exempt
import logging

from lti_provider.outcomes import store_outcome_parameters
from lti_provider.models import LtiConsumer
from lti_provider.signature_validator import SignatureValidator
from lti_provider.users import authenticate_lti_user
from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys import InvalidKeyError
from openedx.core.lib.url_utils import unquote_slashes
from util.views import add_p3p_header

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


@csrf_exempt
@add_p3p_header
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
    """
    if not settings.FEATURES['ENABLE_LTI_PROVIDER']:
        return HttpResponseForbidden()

    # Check the LTI parameters, and return 400 if any required parameters are
    # missing
    params = get_required_parameters(request.POST)
    if not params:
        return HttpResponseBadRequest()
    params.update(get_optional_parameters(request.POST))

    # Get the consumer information from either the instance GUID or the consumer
    # key
    try:
        lti_consumer = LtiConsumer.get_or_supplement(
            params.get('tool_consumer_instance_guid', None),
            params['oauth_consumer_key']
        )
    except LtiConsumer.DoesNotExist:
        return HttpResponseForbidden()

    # Check the OAuth signature on the message
    if not SignatureValidator(lti_consumer).verify(request):
        return HttpResponseForbidden()

    # Add the course and usage keys to the parameters array
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

    # Create an edX account if the user identifed by the LTI launch doesn't have
    # one already, and log the edX account into the platform.
    authenticate_lti_user(request, params['user_id'], lti_consumer)

    # Store any parameters required by the outcome service in order to report
    # scores back later. We know that the consumer exists, since the record was
    # used earlier to verify the oauth signature.
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
    from courseware.views.views import render_xblock
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
