"""
Views to support bulk email functionalities like opt-out.
"""


import logging

from six import text_type

from django.contrib.auth.models import User
from django.http import Http404

from lms.djangoapps.bulk_email.models import Optout
from lms.djangoapps.courseware.courses import get_course_by_id
from common.djangoapps.edxmako.shortcuts import render_to_response
from lms.djangoapps.discussion.notification_prefs.views import (
    UsernameCipher,
    UsernameDecryptionException,
)

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey


log = logging.getLogger(__name__)


def opt_out_email_updates(request, token, course_id):
    """
    A view that let users opt out of any email updates.

    This meant is meant to be the target of an opt-out link or button.
    The `token` parameter must decrypt to a valid username.
    The `course_id` is the string course key of any course.

    Raises a 404 if there are any errors parsing the input.
    """
    try:
        username = UsernameCipher().decrypt(token).decode("utf-8")
        user = User.objects.get(username=username)
        course_key = CourseKey.from_string(course_id)
        course = get_course_by_id(course_key, depth=0)
    except UnicodeDecodeError:
        raise Http404("base64url")
    except UsernameDecryptionException as exn:
        raise Http404(text_type(exn))
    except User.DoesNotExist:
        raise Http404("username")
    except InvalidKeyError:
        raise Http404("course")

    unsub_check = request.POST.get('unsubscribe', False)
    context = {
        'course': course,
        'unsubscribe': unsub_check
    }

    if request.method == 'GET':
        return render_to_response('bulk_email/confirm_unsubscribe.html', context)

    if request.method == 'POST' and unsub_check:
        Optout.objects.get_or_create(user=user, course_id=course_key)
        log.info(
            u"User %s (%s) opted out of receiving emails from course %s",
            user.username,
            user.email,
            course_id,
        )

    return render_to_response('bulk_email/unsubscribe_success.html', context)
