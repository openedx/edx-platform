"""
Student Custom Dashboard View
"""

from django.core.exceptions import ObjectDoesNotExist

from common.lib.nodebb_client.client import NodeBBClient
from courseware.courses import get_courses
from custom_settings.models import CustomSettings
from lms.djangoapps.onboarding_survey.models import InterestsSurvey
from xmodule.modulestore.django import modulestore


def get_recommended_courses(user):
    recommended_courses = []
    all_courses = get_courses(user)
    try:
        user_interests = InterestsSurvey.objects.get(user=user).capacity_areas.all().values_list('label', flat=True)
        for course in all_courses:
            try:
                tags = CustomSettings.objects.filter(id=course.id).first().tags
                tags = tags.split('|')
                if set(user_interests) & set(tags):
                    recommended_courses.append(course)
            except AttributeError:
                pass
    except ObjectDoesNotExist:
        pass
    return recommended_courses


def get_enrolled_past_courses(course_enrollments):
    enrolled, past = [], []

    for course in course_enrollments:
        if course.course_overview.has_ended():
            past.append(course)
        else:
            enrolled.append(course)

    return enrolled, past


def get_recommended_xmodule_courses(user):
    recommended_courses = []
    all_courses = get_courses(user)
    try:
        user_interests = InterestsSurvey.objects.get(user=user).capacity_areas.all().values_list('label', flat=True)
        for course in all_courses:
            try:
                tags = CustomSettings.objects.filter(id=course.id).first().tags
                tags = tags.split('|')
                matched_interests = set(user_interests) & set(tags)
                if matched_interests:
                    detailed_course = modulestore().get_course(course.id)
                    detailed_course.short_description = course.short_description
                    detailed_course.interests = ', '.join(list(matched_interests))
                    recommended_courses.append(detailed_course)
            except AttributeError:
                pass
    except ObjectDoesNotExist:
        pass
    return recommended_courses


def get_recommended_communities(user):
    status, categories = NodeBBClient().categories.recommended(user)
    return categories if status == 200 else []
