""" Views for a student's account information. """

from edxmako.shortcuts import render_to_response


def index(request):
    """
    Render the account info page.

    Args:
        request (HttpRequest)

    Returns:
        HttpResponse

    Example usage:

        GET /account

    """
    return render_to_response(
        'student_account/index.html', {
            'disable_courseware_js': True,
        }
    )
