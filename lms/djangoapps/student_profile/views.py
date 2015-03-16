""" Views for a student's account information. """

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

from edxmako.shortcuts import render_to_response, render_to_string


@login_required
@require_http_methods(['GET'])
def learner_profile(request, username):
    """Render the students profile page.
    Args:
        request (HttpRequest)
    Returns:
        HttpResponse: 200 if the page was sent successfully
        HttpResponse: 302 if not logged in (redirect to login page)
        HttpResponse: 405 if using an unsupported HTTP method
    Example usage:
        GET /account/profile
    """

    context = {
        # TODO! Add data to be passed
        'profile_data': {}
    }
    return render_to_response('student_profile/learner_profile.html', context)
