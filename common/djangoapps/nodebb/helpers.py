import collections

from django.core.urlresolvers import reverse

from courseware.tabs import get_course_tab_list
from lms.djangoapps.grades.new.course_grade import CourseGradeFactory
from nodebb.models import DiscussionCommunity

from lms.djangoapps.onboarding.models import UserExtendedProfile


def get_fields_to_sync_with_nodebb():
    """
        Return list of fields to sync with NodeBB profile
    """
    field_to_sync_with_nodebb = ["id", "email",  "date_joined", "first_name", "last_name", "city", "country",
                                 "year_of_birth", "language", "country_of_employment", "city_of_employment",
                                 "organization"]

    field_to_sync_with_nodebb += [interest_field for interest_field, label in
                                  UserExtendedProfile.INTERESTS_LABELS.items()]
    field_to_sync_with_nodebb += [function_field for function_field, label in
                                  UserExtendedProfile.FUNCTIONS_LABELS.items()]

    return field_to_sync_with_nodebb

from lms.djangoapps.onboarding.models import UserExtendedProfile


def get_fields_to_sync_with_nodebb():
    """
        Return list of fields to sync with NodeBB profile
    """
    field_to_sync_with_nodebb = ["id", "email",  "date_joined", "first_name", "last_name", "city", "country",
                                 "year_of_birth", "language", "country_of_employment", "city_of_employment",
                                 "organization"]

    field_to_sync_with_nodebb += [interest_field for interest_field, label in
                                  UserExtendedProfile.INTERESTS_LABELS.items()]
    field_to_sync_with_nodebb += [function_field for function_field, label in
                                  UserExtendedProfile.FUNCTIONS_LABELS.items()]

    return field_to_sync_with_nodebb


def get_course_related_tabs(request, course):
    """
        Return list of tabs data as dictionary
    """

    course_tabs = get_course_tab_list(request, course)

    tabs_dict = collections.OrderedDict()
    for idx, tab in enumerate(course_tabs):
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

    course_grade = CourseGradeFactory().create(student, course)
    courseware_summary = course_grade.chapter_grades

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
