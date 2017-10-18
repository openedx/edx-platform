"""
Views handling read (GET) requests for the Discussion tab and inline discussions.
"""

import logging
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from opaque_keys.edx.keys import CourseKey

from nodebb.models import DiscussionCommunity

log = logging.getLogger("edx.discussions_nodebb")


@login_required
def nodebb_forum_discussion(request, course_id):
    """
    Redirect user to nodeBB forum page that is loaded into our template using iframe
    """
    course = CourseKey.from_string(course_id)
    course_community = DiscussionCommunity.objects.filter(course_id=course).first()
    context = {
        "course_id": course_id,
        "course_name": course.run,
        "community_url": course_community.community_url
    }

    return render(request, 'discussion_nodebb/discussion_board.html', context)
