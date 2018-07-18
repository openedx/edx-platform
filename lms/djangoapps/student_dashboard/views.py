"""
Student Custom Dashboard View
"""
from datetime import datetime

import pytz
from course_action_state.models import CourseRerunState
from django.core.exceptions import ObjectDoesNotExist

from common.lib.nodebb_client.client import NodeBBClient
from courseware.courses import get_courses
from custom_settings.models import CustomSettings
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.features.course_card.helpers import get_course_cards_list, get_related_card
from xmodule.modulestore.django import modulestore
from student.models import CourseEnrollment


def get_recommended_courses(user):
    """
    Helper function to get recommended courses for a user based on his interests
    """
    recommended_courses = []
    all_courses = get_courses(user)
    try:
        user_interests = user.extended_profile.get_user_selected_interests()
        for course in all_courses:
            try:
                tags = CustomSettings.objects.filter(id=course.id).first().tags
                tags = tags.split('|')
                tags = [tag.strip() for tag in tags]
                if set(user_interests) & set(tags) and not CourseEnrollment.is_enrolled(user, course.id):
                    recommended_courses.append(course)
            except AttributeError:
                pass
    except ObjectDoesNotExist:
        pass
    return recommended_courses


def get_enrolled_past_courses(course_enrollments):
    """
    Helper function to separate past courses from all enrolled courses
    """
    # TODO move this function out of core code
    enrolled, past = [], []

    card_list = get_course_cards_list()
    for course in course_enrollments:
        course_card = get_related_card(course.course_overview)
        if course_card in card_list:
            if course.course_overview.has_ended():
                past.append(course)
            else:
                enrolled.append(course)

    return enrolled, past


def get_recommended_xmodule_courses(request, _from='onboarding'):
    """
    Helper function to get recommended courses based on the user interests and add details from xmodule to
    the recommended courses
    """
    user = request.user
    recommended_courses = []
    all_courses = []

    utc = pytz.UTC
    courses_list = get_course_cards_list()
    course_list_ids = []

    current_time = datetime.utcnow().replace(tzinfo=utc)

    for course in courses_list:
        course_rerun_states = [crs.course_key for crs in CourseRerunState.objects.filter(
            source_course_key=course.id, action="rerun", state="succeeded")] + [course.id]
        course_rerun_object = CourseOverview.objects.select_related('image_set').filter(
            id__in=course_rerun_states, enrollment_start__lte=current_time, enrollment_end__gte=current_time
        ).order_by('start').first()

        if course_rerun_object:
            course_list_ids.append(course.id)
            _settings = CustomSettings.objects.filter(id=course_rerun_object.id).first()
            course.settings_attrs = _settings
            course.start = course_rerun_object.start
            all_courses.append(course)

    user_interests = user.extended_profile.get_user_selected_interests()
    if not user_interests:
        return []

    for course in all_courses:
        _settings = course.settings_attrs
        if not _settings:
            continue

        tags = _settings.tags
        if not tags:
            continue

        tags = tags.split('|')
        tags = [tag.strip() for tag in tags]
        matched_interests = set(user_interests) & set(tags)
        if matched_interests and not CourseEnrollment.is_enrolled(user, course.id):
            if _from == 'onboarding':
                start_date = course.start
                detailed_course = modulestore().get_course(course.id)
                detailed_course.start = start_date
                detailed_course.short_description = course.short_description
                detailed_course.interests = '/ '.join(list(matched_interests))
                recommended_courses.append(detailed_course)
            else:
                recommended_courses.append(course)

    return recommended_courses


def get_recommended_communities(user):
    """
    Helper function to get recommended communities from NodeBB API
    """
    status, categories = NodeBBClient().categories.recommended(user)
    return categories if status == 200 else []


def get_joined_communities(user):
    """
    Helper function to get joined communities from NodeBB API
    """
    status, categories = NodeBBClient().categories.joined(user)
    return categories if status == 200 else []
