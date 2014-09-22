""" Views for a student's profile information. """

from django.http import HttpResponse, QueryDict
from django_future.csrf import ensure_csrf_cookie
from edxmako.shortcuts import render_to_response
from user_api.api import profile as profile_api


def index(request):
    """Render the profile info page.

    Args:
        request (HttpRequest)

    Returns:
        HttpResponse

    Example usage:

        GET /profile

    """
    return render_to_response(
        'student_profile/index.html', {
            'disable_courseware_js': True,
        }
    )


@ensure_csrf_cookie
def name_change_handler(request):
    """Change the user's name.

    Args:
        request (HttpRequest)

    Returns:

    Example usage:

        PUT /profile/name_change

    """
    put = QueryDict(request.body)
    username = request.user.username
    proposed_name = put.get('proposed_name')
    profile_api.update_profile(username, full_name=proposed_name)

    # A 204 is intended to allow input for actions to take place
    # without causing a change to the user agent's active document view.
    return HttpResponse(status=204)
