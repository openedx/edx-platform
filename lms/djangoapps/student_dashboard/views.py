"""
Student Custom Dashboard View
"""
from datetime import datetime

import pytz
from course_action_state.models import CourseRerunState
from custom_settings.models import CustomSettings
from student.models import CourseEnrollment
from student.views.dashboard import get_course_enrollments
from xmodule.modulestore.django import modulestore

from common.lib.nodebb_client.client import NodeBBClient
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.features.course_card.helpers import get_course_cards_list, get_related_card, get_course_open_date


def get_enrolled_past_courses(request, course_enrollments):
    """
    Helper function to separate past courses from all enrolled courses
    """
    # TODO move this function out of core code
    enrolled, past = [], []
    past_course_cards = {}

    card_list = get_course_cards_list(request)

    for course in course_enrollments:
        course_card = get_related_card(course.course_overview)
        course.course_overview.course_open_date = get_course_open_date(course.course_overview)
        if course_card in card_list:
            if course.course_overview.has_ended():
                if course_card.id not in past_course_cards:
                    past_course_cards[course_card.id] = []

                past_course_cards[course_card.id].append(course)
            else:
                enrolled.append(course)

    for card, courses in past_course_cards.items():
        sorted_courses = sorted(courses, key=lambda co: co.course_overview.start)
        past.append(sorted_courses[-1])

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
    courses_list = get_course_cards_list(request)
    course_list_ids = []

    current_time = datetime.utcnow().replace(tzinfo=utc)

    user_enrolled_courses = [enrollment.course_overview.id for enrollment in
                             list(get_course_enrollments(user, None, []))]

    for course in courses_list:

        course_rerun_states = [crs.course_key for crs in CourseRerunState.objects.filter(
            source_course_key=course.id, action="rerun", state="succeeded")] + [course.id]

        course_rerun_object = CourseOverview.objects.select_related('image_set').filter(
            id__in=course_rerun_states, enrollment_start__lte=current_time, enrollment_end__gte=current_time
        ).exclude(id__in=user_enrolled_courses).order_by('start').first()

        if course_rerun_object:
            course_list_ids.append(course.id)
            _settings = CustomSettings.objects.filter(id=course_rerun_object.id).first()
            course.settings_attrs = _settings
            course.course_open_date = get_course_open_date(course_rerun_object)
            course.target_course_id = course_rerun_object.id
            course.self_paced = course_rerun_object.self_paced
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
        if matched_interests and not CourseEnrollment.is_enrolled(user, course.target_course_id):
            if _from == 'onboarding':
                start_date = get_course_open_date(course)
                detailed_course = modulestore().get_course(course.id)
                detailed_course.start = start_date
                detailed_course.short_description = course.short_description
                detailed_course.interests = '/ '.join(list(matched_interests))
                recommended_courses.append(detailed_course)
            else:
                recommended_courses.append(course)

    return recommended_courses


def get_joined_communities(user):
    """
    Helper function to get joined communities from NodeBB API
    """
    status, categories = NodeBBClient().categories.joined(user)
    return categories if status == 200 else []
