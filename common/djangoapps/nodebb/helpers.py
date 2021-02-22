"""
Helpers for Nodebb app
"""
import collections
from logging import getLogger

from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse

from courseware.tabs import get_course_tab_list
from lms.djangoapps.grades.course_grade_factory import CourseGradeFactory
from nodebb.models import DiscussionCommunity, TeamGroupChat
from nodebb.tasks import (
    task_activate_user_on_nodebb,
    task_archive_community_on_nodebb,
    task_update_onboarding_surveys_status
)
from openedx.core.djangoapps.xmodule_django.models import CourseKeyField

log = getLogger(__name__)


def get_course_related_tabs(request, course):
    """
        Return list of tabs data as dictionary
    """

    course_tabs = get_course_tab_list(request, course)

    tabs_dict = collections.OrderedDict()
    for idx, tab in enumerate(course_tabs): # pylint: disable=unused-variable
        tab_name = tab.name.lower()
        tab_link = tab.link_func(course, reverse)

        if tab_name == "discussion":
            tab_link = tab_link.replace("forum", "nodebb")

        tabs_dict[tab.name] = {'link': tab_link, 'name': tab.name, 'type': tab.type}

    return tabs_dict


def get_all_course_progress(student, course):
    """
        Return course overall progress percentage for a student
    """

    course_grade = CourseGradeFactory().read(student, course)
    courseware_summary = course_grade.chapter_grades.values()

    total_score = 0
    earned_score = 0

    for week in courseware_summary:
        sections = week.get('sections', [])

        for section in sections:
            total_score += section.all_total.possible
            earned_score += section.all_total.earned

    if total_score:
        average = earned_score / total_score
        percentage = average * 100
    else:
        percentage = 0

    return int(percentage)


def get_community_url(course_id):
    """
    Get community url(if exists) based on the course id
    """
    discussion_community = DiscussionCommunity.objects.filter(course_id=course_id).first()
    if discussion_community:
        return discussion_community.community_url


def get_community_id(course_id):
    discussion_community = DiscussionCommunity.objects.filter(course_id=course_id).first()
    if discussion_community:
        return discussion_community.community_url.split('/')[0]


def get_course_id_by_community_id(community_id):
    """
        Get `course_id` based on the given `community_id`
        using the `community_url` field from the model

        Parameters
        ----------
        community_id : str
                       community ID of a discussion group

        Returns
        -------
        CourseKeyField
            CourseKey Model object that specifies a course or is empty
    """
    try:
        discussion_community = DiscussionCommunity.objects.get(community_url__startswith=(community_id + '/'))
        return discussion_community.course_id
    except ObjectDoesNotExist:
        return CourseKeyField.Empty


def get_room_id(user_info):
    """
    Get room_id for MyTeam of a user
    """
    room_info = {}

    for team in user_info['teams']['results']:
        team = dict(team)
        if team['membership']:
            team_group = TeamGroupChat.objects.filter(team__team_id=team['id']).first()
            if team_group:
                room_info.update({team['id']: team_group.room_id})

    return room_info


def update_nodebb_for_user_status(username):
    """
    Call nodebb client to update NodeBB for survey status update
    """
    task_update_onboarding_surveys_status.delay(username=username)


def set_user_activation_status_on_nodebb(username, is_active):
    """
    Call nodebb client to update NodeBB for user's activation status
    """
    task_activate_user_on_nodebb.delay(username=username, active=is_active)


def archive_course_community(course_id):
    """
    Marks the community of a course as archived or simply returns if community does not exist

    Arguments:
        course_id: id of the course of which the community is to be archived

    Returns:
        None
    """
    community = DiscussionCommunity.objects.filter(course_id=course_id).first()

    if not community or not community.community_url:
        return

    category_id = community.community_url.split('/')[0]

    task_archive_community_on_nodebb.delay(category_id=category_id)
