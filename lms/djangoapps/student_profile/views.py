""" Views for a student's profile information. """

from django.http import HttpResponse, QueryDict
from django_future.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from edxmako.shortcuts import render_to_response
from user_api.api import profile as profile_api
from third_party_auth import pipeline


@login_required
@require_http_methods(['GET'])
def index(request):
    """Render the profile info page.

    Args:
        request (HttpRequest)

    Returns:
        HttpResponse: 200 if successful
        HttpResponse: 302 if not logged in (redirect to login page)
        HttpResponse: 405 if using an unsupported HTTP method

    Example usage:

        GET /profile

    """
    user = request.user

    return render_to_response(
        'student_profile/index.html', {
            'disable_courseware_js': True,
            'provider_user_states': pipeline.get_provider_user_states(user),
        }
    )


@login_required
@require_http_methods(['PUT'])
@ensure_csrf_cookie
def name_change_handler(request):
    """Change the user's name.

    Args:
        request (HttpRequest)

    Returns:
        HttpResponse: 204 if successful
        HttpResponse: 302 if not logged in (redirect to login page)
        HttpResponse: 405 if using an unsupported HTTP method

    Example usage:

        PUT /profile/name_change

    """
    put = QueryDict(request.body)

    username = request.user.username
    new_name = put.get('new_name')

    profile_api.update_profile(username, full_name=new_name)

    # A 204 is intended to allow input for actions to take place
    # without causing a change to the user agent's active document view.
    return HttpResponse(status=204)
