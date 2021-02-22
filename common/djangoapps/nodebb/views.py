"""
Views handling read (GET) requests for the Discussion tab and inline discussions.
"""

import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from opaque_keys.edx.keys import CourseKey
from w3lib.url import add_or_replace_parameter

from nodebb.constants import COMMUNITY_ID_SPLIT_INDEX, COMMUNITY_URL_SPLIT_CHAR, CONVERSATIONALIST_ENTRY_INDEX
from nodebb.helpers import get_all_course_progress, get_course_related_tabs
from nodebb.models import DiscussionCommunity, TeamGroupChat
from openedx.features.badging.constants import CONVERSATIONALIST
from openedx.features.badging.models import Badge
from openedx.features.course_card.helpers import get_related_card_id

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
    browse_teams_link = reverse('teams_dashboard', args=[course_id])
    courseware_link = reverse('courseware', args=[course_id])

    room_id = course_community.community_url.split(COMMUNITY_URL_SPLIT_CHAR)[COMMUNITY_ID_SPLIT_INDEX]

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
        "is_community_topic_link": is_community_topic_link,
        "browse_teams_link": browse_teams_link,
        "course_has_ended": current_course.has_ended(),
        "courses_page_link": reverse("courses"),
        "courseware_link": courseware_link,
        "community_id": room_id,
        "badges": Badge.objects.get_badges_json(badge_type=CONVERSATIONALIST[CONVERSATIONALIST_ENTRY_INDEX]),
    }

    return render(request, 'discussion_nodebb/discussion_board.html', context)


@login_required
def nodebb_embedded_topic(request):
    """
    Redirect user to nodeBB forum page that is loaded into our template using iframe with proper course ID
    """
    topic_url = 'topic/' + request.GET.get('topic_url')
    category_slug = request.GET.get('category_slug')
    if "teamview" in request.GET:
        redirect_url = get_course_team_discussion_url(category_slug, topic_url)
    else:
        redirect_url = get_course_discussion_url(category_slug, topic_url)

    return HttpResponseRedirect(redirect_url)


def get_course_team_discussion_url(community_url, topic_url):

    team_chat_group = TeamGroupChat.objects.get(slug=community_url)
    if team_chat_group:
        course_id = team_chat_group.team.course_id.to_deprecated_string()

        url = reverse("my_team", args=[course_id])
        if topic_url:
            url = add_or_replace_parameter(url, "topic_url", topic_url)
        return url


def get_course_discussion_url(category_slug, topic_url):
    course_id = DiscussionCommunity.objects.filter(community_url=category_slug).first().course_id
    redirect_url = '/courses/{}/discussion/nodebb?topic_url={}'.format(course_id, topic_url)
    return redirect_url
