""" Views for a student's profile information. """

from edxmako.shortcuts import render_to_response


def index(request):
    """
    Render the profile info page.

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
