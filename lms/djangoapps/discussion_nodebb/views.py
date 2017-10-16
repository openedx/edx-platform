"""
Views handling read (GET) requests for the Discussion tab and inline discussions.
"""

import logging
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response

log = logging.getLogger("edx.discussions_nodebb")


@login_required
def nodebb_form_discussion(request, course_id):
    """
    Redirect user to nodeBB forum page that is loaded into our template using iframe
    """
    context = {"course_id": course_id}
    return render_to_response('discussion_nodebb/discussion_board.html', context)
