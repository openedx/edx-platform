"""
Views for the credit Django app.
"""
import json
import datetime
import logging

from django.conf import settings
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    Http404
)
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
import pytz
from rest_framework import viewsets, mixins, permissions
from rest_framework.authentication import SessionAuthentication
from rest_framework_oauth.authentication import OAuth2Authentication
from util.json_request import JsonResponse
from util.date_utils import from_timestamp
from openedx.core.djangoapps.credit import api
from openedx.core.djangoapps.credit.exceptions import CreditApiBadRequest, CreditRequestNotFound
from openedx.core.djangoapps.credit.models import CreditCourse
from openedx.core.djangoapps.credit.serializers import CreditCourseSerializer
from openedx.core.djangoapps.credit.signature import signature, get_shared_secret_key

log = logging.getLogger(__name__)


@require_GET
def get_providers_detail(request):
    """

    **User Cases**

        Returns details of the credit providers filtered by provided query parameters.

    **Parameters:**

        * provider_id (list of provider ids separated with ","): The identifiers for the providers for which
        user requested

    **Example Usage:**

        GET /api/credit/v1/providers?provider_id=asu,hogwarts
        "response": [
            "id": "hogwarts",
            "display_name": "Hogwarts School of Witchcraft and Wizardry",
            "url": "https://credit.example.com/",
            "status_url": "https://credit.example.com/status/",
            "description": "A new model for the Witchcraft and Wizardry School System.",
            "enable_integration": false,
            "fulfillment_instructions": "
            <p>In order to fulfill credit, Hogwarts School of Witchcraft and Wizardry requires learners to:</p>
            <ul>
            <li>Sample instruction abc</li>
            <li>Sample instruction xyz</li>
            </ul>",
        },
        ...
        ]

    **Responses:**

        * 200 OK: The request was created successfully. Returned content
            is a JSON-encoded dictionary describing what the client should
            send to the credit provider.

        * 404 Not Found: The provider does not exist.

    """
    provider_id = request.GET.get("provider_id", None)
    providers_list = provider_id.split(",") if provider_id else None
    providers = api.get_credit_providers(providers_list)
    return JsonResponse(providers)


@require_POST
def create_credit_request(request, provider_id):
    """
    Initiate a request for credit in a course.

    This end-point will get-or-create a record in the database to track
    the request.  It will then calculate the parameters to send to
    the credit provider and digitally sign the parameters, using a secret
    key shared with the credit provider.

    The user's browser is responsible for POSTing these parameters
    directly to the credit provider.

    **Example Usage:**

        POST /api/credit/v1/providers/hogwarts/request/
        {
            "username": "ron",
            "course_key": "edX/DemoX/Demo_Course"
        }

        Response: 200 OK
        Content-Type: application/json
        {
            "url": "http://example.com/request-credit",
            "method": "POST",
            "parameters": {
                request_uuid: "557168d0f7664fe59097106c67c3f847"
                timestamp: 1434631630,
                course_org: "ASUx"
                course_num: "DemoX"
                course_run: "1T2015"
                final_grade: 0.95,
                user_username: "john",
                user_email: "john@example.com"
                user_full_name: "John Smith"
                user_mailing_address: "",
                user_country: "US",
                signature: "cRCNjkE4IzY+erIjRwOQCpRILgOvXx4q2qvx141BCqI="
            }
        }

    **Parameters:**

        * username (unicode): The username of the user requesting credit.

        * course_key (unicode): The identifier for the course for which the user
            is requesting credit.

    **Responses:**

        * 200 OK: The request was created successfully.  Returned content
            is a JSON-encoded dictionary describing what the client should
            send to the credit provider.

        * 400 Bad Request:
            - The provided course key did not correspond to a valid credit course.
            - The user already has a completed credit request for this course and provider.

        * 403 Not Authorized:
            - The username does not match the name of the logged in user.
            - The user is not eligible for credit in the course.

        * 404 Not Found:
            - The provider does not exist.

    """
    response, parameters = _validate_json_parameters(request.body, ["username", "course_key"])
    if response is not None:
        return response

    try:
        course_key = CourseKey.from_string(parameters["course_key"])
    except InvalidKeyError:
        return HttpResponseBadRequest(
            u'Could not parse "{course_key}" as a course key'.format(
                course_key=parameters["course_key"]
            )
        )

    # Check user authorization
    if not (request.user and request.user.username == parameters["username"]):
        log.warning(
            u'User with ID %s attempted to initiate a credit request for user with username "%s"',
            request.user.id if request.user else "[Anonymous]",
            parameters["username"]
        )
        return HttpResponseForbidden("Users are not allowed to initiate credit requests for other users.")

    # Initiate the request
    try:
        credit_request = api.create_credit_request(course_key, provider_id, parameters["username"])
    except CreditApiBadRequest as ex:
        return HttpResponseBadRequest(ex)
    else:
        return JsonResponse(credit_request)


@require_POST
@csrf_exempt
def credit_provider_callback(request, provider_id):
    """
    Callback end-point used by credit providers to approve or reject
    a request for credit.

    **Example Usage:**

        POST /api/credit/v1/providers/{provider-id}/callback
        {
            "request_uuid": "557168d0f7664fe59097106c67c3f847",
            "status": "approved",
            "timestamp": 1434631630,
            "signature": "cRCNjkE4IzY+erIjRwOQCpRILgOvXx4q2qvx141BCqI="
        }

        Response: 200 OK

    **Parameters:**

        * request_uuid (string): The UUID of the request.

        * status (string): Either "approved" or "rejected".

        * timestamp (int or string): The datetime at which the POST request was made, represented
            as the number of seconds since January 1, 1970 00:00:00 UTC.
            If the timestamp is a string, it will be converted to an integer.

        * signature (string): A digital signature of the request parameters,
            created using a secret key shared with the credit provider.

    **Responses:**

        * 200 OK: The user's status was updated successfully.

        * 400 Bad request: The provided parameters were not valid.
            Response content will be a JSON-encoded string describing the error.

        * 403 Forbidden: Signature was invalid or timestamp was too far in the past.

        * 404 Not Found: Could not find a request with the specified UUID associated with this provider.

    """
    response, parameters = _validate_json_parameters(request.body, [
        "request_uuid", "status", "timestamp", "signature"
    ])
    if response is not None:
        return response

    # Validate the digital signature of the request.
    # This ensures that the message came from the credit provider
    # and hasn't been tampered with.
    response = _validate_signature(parameters, provider_id)
    if response is not None:
        return response

    # Validate the timestamp to ensure that the request is timely.
    response = _validate_timestamp(parameters["timestamp"], provider_id)
    if response is not None:
        return response

    # Update the credit request status
    try:
        api.update_credit_request_status(parameters["request_uuid"], provider_id, parameters["status"])
    except CreditRequestNotFound:
        raise Http404
    except CreditApiBadRequest as ex:
        return HttpResponseBadRequest(ex)
    else:
        return HttpResponse()


@require_GET
def get_eligibility_for_user(request):
    """

    **User Cases**

        Retrieve user eligibility against course.

    **Parameters:**

        * course_key (unicode): Identifier of course.
        * username (unicode): Username of current User.

    **Example Usage:**

        GET /api/credit/v1/eligibility?username=user&course_key=edX/Demo_101/Fall
        "response": {
                "course_key": "edX/Demo_101/Fall",
                "deadline": "2015-10-23"
            }

    **Responses:**

        * 200 OK: The request was created successfully.

        * 404 Not Found: The provider does not exist.

    """
    course_key = request.GET.get("course_key", None)
    username = request.GET.get("username", None)
    return JsonResponse(api.get_eligibilities_for_user(username=username, course_key=course_key))


def _validate_json_parameters(params_string, expected_parameters):
    """
    Load the request parameters as a JSON dictionary and check that
    all required paramters are present.

    Arguments:
        params_string (unicode): The JSON-encoded parameter dictionary.
        expected_parameters (list): Required keys of the parameters dictionary.

    Returns: tuple of (HttpResponse, dict)

    """
    try:
        parameters = json.loads(params_string)
    except (TypeError, ValueError):
        return HttpResponseBadRequest("Could not parse the request body as JSON."), None

    if not isinstance(parameters, dict):
        return HttpResponseBadRequest("Request parameters must be a JSON-encoded dictionary."), None

    missing_params = set(expected_parameters) - set(parameters.keys())
    if missing_params:
        msg = u"Required parameters are missing: {missing}".format(missing=u", ".join(missing_params))
        return HttpResponseBadRequest(msg), None

    return None, parameters


def _validate_signature(parameters, provider_id):
    """
    Check that the signature from the credit provider is valid.

    Arguments:
        parameters (dict): Parameters received from the credit provider.
        provider_id (unicode): Identifier for the credit provider.

    Returns:
        HttpResponseForbidden or None

    """
    secret_key = get_shared_secret_key(provider_id)
    if secret_key is None:
        log.error(
            (
                u'Could not retrieve secret key for credit provider with ID "%s".  '
                u'Since no key has been configured, we cannot validate requests from the credit provider.'
            ), provider_id
        )
        return HttpResponseForbidden("Credit provider credentials have not been configured.")

    if signature(parameters, secret_key) != parameters["signature"]:
        log.warning(u'Request from credit provider with ID "%s" had an invalid signature', parameters["signature"])
        return HttpResponseForbidden("Invalid signature.")


def _validate_timestamp(timestamp_value, provider_id):
    """
    Check that the timestamp of the request is recent.

    Arguments:
        timestamp (int or string): Number of seconds since Jan. 1, 1970 UTC.
            If specified as a string, it will be converted to an integer.
        provider_id (unicode): Identifier for the credit provider.

    Returns:
        HttpResponse or None

    """
    timestamp = from_timestamp(timestamp_value)
    if timestamp is None:
        msg = u'"{timestamp}" is not a valid timestamp'.format(timestamp=timestamp_value)
        log.warning(msg)
        return HttpResponseBadRequest(msg)

    # Check that the timestamp is recent
    elapsed_seconds = (datetime.datetime.now(pytz.UTC) - timestamp).total_seconds()
    if elapsed_seconds > settings.CREDIT_PROVIDER_TIMESTAMP_EXPIRATION:
        log.warning(
            (
                u'Timestamp %s is too far in the past (%s seconds), '
                u'so we are rejecting the notification from the credit provider "%s".'
            ),
            timestamp_value, elapsed_seconds, provider_id,
        )
        return HttpResponseForbidden(u"Timestamp is too far in the past.")


class CreditCourseViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.ReadOnlyModelViewSet):
    """ CreditCourse endpoints. """

    lookup_field = 'course_key'
    lookup_value_regex = settings.COURSE_KEY_REGEX
    queryset = CreditCourse.objects.all()
    serializer_class = CreditCourseSerializer
    authentication_classes = (OAuth2Authentication, SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated, permissions.IsAdminUser)

    # In Django Rest Framework v3, there is a default pagination
    # class that transmutes the response data into a dictionary
    # with pagination information.  The original response data (a list)
    # is stored in a "results" value of the dictionary.
    # For backwards compatibility with the existing API, we disable
    # the default behavior by setting the pagination_class to None.
    pagination_class = None

    # This CSRF exemption only applies when authenticating without SessionAuthentication.
    # SessionAuthentication will enforce CSRF protection.
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(CreditCourseViewSet, self).dispatch(request, *args, **kwargs)

    def get_object(self):
        # Convert the serialized course key into a CourseKey instance
        # so we can look up the object.
        course_key = self.kwargs.get(self.lookup_field)
        if course_key is not None:
            self.kwargs[self.lookup_field] = CourseKey.from_string(course_key)

        return super(CreditCourseViewSet, self).get_object()
