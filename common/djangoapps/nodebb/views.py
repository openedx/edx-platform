"""
Views handling read (GET) requests for the Discussion tab and inline discussions.
"""

import logging
from django.http import HttpResponseRedirect
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.core.urlresolvers import reverse
from openedx.features.course_card.helpers import get_related_card_id
from opaque_keys.edx.keys import CourseKey

from nodebb.models import DiscussionCommunity
from common.djangoapps.nodebb.helpers import get_course_related_tabs, get_all_course_progress
from nodebb.models import DiscussionCommunity

log = logging.getLogger("edx.nodebb")


@login_required
def nodebb_forum_discussion(request, course_id):
    """
    Redirect user to nodeBB forum page that is loaded into our template using iframe
    """
    # To avoid circuler dependencies
    from xmodule.modulestore.django import modulestore
    modulestore = modulestore()
    is_community_topic_link = False

    course_key = CourseKey.from_string(course_id)
    course_community = DiscussionCommunity.objects.filter(course_id=course_key).order_by("-created").first()
    current_course = modulestore.get_course(course_key)
    course_tabs = get_course_related_tabs(request, current_course)
    custom_community_link = request.GET.get('topic_url')
    if custom_community_link:
        if "topic/" in custom_community_link:
            is_community_topic_link = True
            custom_community_link = custom_community_link.split("topic/")[1]
        else:
            custom_community_link = custom_community_link.split("category/")[1]

    progress = get_all_course_progress(request.user, current_course)

    course_link = reverse('about_course', args=[get_related_card_id(course_key)])

    context = {
        "provider": current_course.org,
        "nodebb_endpoint": settings.NODEBB_ENDPOINT,
        "course_link": course_link,
        "progress": progress,
        "course_display_name": current_course.display_name,
        "course_tabs": course_tabs,
        "course_id": course_id,
        "community_url": course_community.community_url if course_community else "",
        "custom_community_link": custom_community_link,
        "is_community_topic_link": is_community_topic_link
    }

    return render(request, 'discussion_nodebb/discussion_board.html', context)

@login_required
def nodebb_embedded_topic(request):
    """
    Redirect user to nodeBB forum page that is loaded into our template using iframe with proper course ID
    """
    topic_url = 'topic/' + request.GET.get('topic_url')
    category_slug = request.GET.get('category_slug')

    course_id = DiscussionCommunity.objects.filter(community_url=category_slug).first().course_id

    return HttpResponseRedirect('/courses/{}/discussion/nodebb?topic_url={}'.format(course_id, topic_url))
