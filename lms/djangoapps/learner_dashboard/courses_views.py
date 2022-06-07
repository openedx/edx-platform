"""
Views for the learner dashboard.
"""
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET

@login_required
@require_GET
def course_listing(request):  #pylint: disable=unused-argument
    """ List of courses a user is enrolled in or entitled to """
    return []
