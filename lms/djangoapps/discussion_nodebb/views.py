"""
Views handling read (GET) requests for the Discussion tab and inline discussions.
"""

import logging
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from lms.djangoapps.discussion_nodebb.models import DiscussionCommunity

log = logging.getLogger("edx.discussions_nodebb")


@login_required
def nodebb_form_discussion(request, course_id):
    """
    Redirect user to nodeBB forum page that is loaded into our template using iframe
    """
    # course_id = CourseKeyField()
    course_community = DiscussionCommunity.objects.filter(course_id="course-v1:edX+DemoX+Demo_Course").first()
    context = {
        "course_id": course_id,
        "course_community": course_community
    }

    return render(request, 'discussion_nodebb/discussion_board.html', context)
