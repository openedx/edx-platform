import logging

from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django_future.csrf import ensure_csrf_cookie

from courseware.courses import get_course_with_access, \
                               registered_for_course
from jabber.utils import get_bosh_url, get_room_name_for_course,\
                         get_or_create_password_for_user
from edxmako.shortcuts import render_to_response

# TODO: should this be standardized somewhere?
log = logging.getLogger("mitx.courseware")

@login_required
@ensure_csrf_cookie
def chat(request, course_id):
    """
    Displays a Jabber chat widget.

    Arguments:

     - request    : HTTP request
     - course_id  : course id (str: ORG/course/URL_NAME)
    """
    user = request.user
    course = get_course_with_access(user, course_id, 'load', depth=2)

    # This route should not exist if chat is disabled by the settings
    if not settings.FEATURES.get('ENABLE_CHAT'):
        log.debug("""
            User %s tried to enter course %s chat, but chat is not
            enabled in the settings
        """, user, course.location.url())
        return redirect(reverse('about_course', args=[course.id]))

    # Don't show chat if course doesn't have it enabled
    if not course.show_chat:
        log.debug("""
            User %s tried to enter course %s chat, but chat is not
            enabled for that course
        """, user, course.location.url())
        return redirect(reverse('about_course', args=[course.id]))

    # Ensure that the user is registered before showing chat
    registered = registered_for_course(course, user)
    if not registered:
        # TODO (vshnayder): do course instructors need to be registered to see course?
        log.debug("""
            User %s tried to enter course %s chat but is not enrolled
        """, user, course.location.url())
        return redirect(reverse('about_course', args=[course.id]))

    # Set up all of the chat context necessary to render
    context = {
        'bosh_url': get_bosh_url(),
        'course_room': get_room_name_for_course(course.id),
        'username': "%s@%s" % (user.username, settings.JABBER.get('HOST')),
        'password': get_or_create_password_for_user(user.username)
    }

    return render_to_response("chat.html", context)

