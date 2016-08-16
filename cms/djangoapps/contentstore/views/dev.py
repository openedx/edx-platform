"""
Views that are only activated when the project is running in development mode.
These views will NOT be shown on production: trying to access them will result
in a 404 error.
"""
# pylint: disable=unused-argument
from edxmako.shortcuts import render_to_response


def dev_mode(request):
    "Sample static view"
    return render_to_response("dev/dev_mode.html")
