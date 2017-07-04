""" Labster CCXInvite view. """
import logging
import json

from django.http import HttpResponseBadRequest
from django.http import Http404
from django.http.request import RawPostDataException
from django.views.decorators.cache import cache_control
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication, SessionAuthentication as OriginalSessionAuthentication
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from ccx_keys.locator import CCXLocator
from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.ccx.views import _ccx_students_enrrolling_center
from lms.djangoapps.ccx.models import CustomCourseForEdX
from instructor.views.api import _split_input_list
from instructor.enrollment import get_email_params


log = logging.getLogger(__name__)


class SessionAuthentication(OriginalSessionAuthentication):
    """
    Disable csrf verification.
    """
    def enforce_csrf(self, request):
        return


@api_view(['POST'])
@authentication_classes((SessionAuthentication, TokenAuthentication))
@permission_classes((IsAdminUser,))
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def ccx_invite(request, course_id):
    """
    Enroll or unenroll students to CCX by email.
    Requires staff access.

    **Request example**:
        POST /labster/api/course/course-v1:labster+LABX+2015_T1/enroll/
        {
            "action": "enroll",
            "auto_enroll": true,
            "email_students": false,
            "identifiers": ["honor@example.com", "staff@example.com"]
        }
    Query Parameters:
        - action in ['enroll', 'unenroll']
        - identifiers is string containing a list of emails and/or usernames separated by anything
          split_input_list can handle.
        - auto_enroll is a boolean (defaults to true)
            If auto_enroll is false, students will be allowed to enroll.
            If auto_enroll is true, students will be enrolled as soon as they register.
        - email_students is a boolean (defaults to false)
            If email_students is true, students will be sent email notification
            If email_students is false, students will not be sent email notification
    """
    course_key = CourseKey.from_string(course_id)
    ccx = None
    if isinstance(course_key, CCXLocator):
        ccx_id = course_key.ccx
        ccx = CustomCourseForEdX.objects.get(pk=ccx_id)
        course_key = ccx.course_id

    if not ccx:
        raise Http404

    try:
        data = json.loads(request.body)
    except ValueError:
        return HttpResponseBadRequest()
    except RawPostDataException:
        data = request.data.dict()

    action = data.get('action')
    identifiers_raw = data.get('identifiers')
    if isinstance(identifiers_raw, (str, unicode)):
        identifiers = _split_input_list(identifiers_raw)
    elif isinstance(identifiers_raw, list):
        identifiers = identifiers_raw
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    auto_enroll = _get_boolean_param(data, 'auto_enroll', deafult=True)
    email_students = _get_boolean_param(data, 'email_students')

    course_key = CCXLocator.from_course_locator(course_key, ccx.id)
    email_params = get_email_params(
        ccx.course,
        course_key=course_key,
        auto_enroll=auto_enroll,
        display_name=ccx.display_name,
    )

    if action:
        _ccx_students_enrrolling_center(action.capitalize(), identifiers, email_students, course_key, email_params)
        log.info(
            "User: %s;\nAction: %s;\nIdentifiers: %s;\nSend email: %s;\nCourse: %s;\nEmail parameters: %s.",
            request.user, action, identifiers, email_students, course_key, email_params
        )
        return Response(status=status.HTTP_200_OK)
    else:
        return Response("No action was provided.", status=status.HTTP_400_BAD_REQUEST)


def _get_boolean_param(data, param_name, deafult=False):
    """
    Returns the value of the boolean parameter with the given
    name in the POST request. Handles translation from string
    values to boolean values.
    """
    return data.get(param_name, deafult) in ['true', 'True', True]
