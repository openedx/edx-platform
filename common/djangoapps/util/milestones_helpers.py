"""
Helper methods for milestones api calls.
"""

from django.utils.translation import ugettext as _
from opaque_keys import InvalidKeyError
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.django import modulestore
from milestones.api import (
    get_course_milestones,
    add_milestone,
    add_course_milestone,
    remove_course_milestone,
    get_course_milestones_fulfillment_paths,
    add_user_milestone,
    get_user_milestones,
)
from django.conf import settings


def add_prerequisite_course(course_key, prerequisite_course_key):
    """
    It would create a milestone for given course and set it as
    requirement milestone for given course and set it a fulfilment
    milestone for pre-requisite course.
    """
    # create a milestone
    milestone = add_milestone({
        'name': _('Course {} requires {}'.format(unicode(course_key), unicode(prerequisite_course_key))),
        'namespace': unicode(prerequisite_course_key),
        'description': _('System defined milestone'),
    })
    # add requirement course milestone
    add_course_milestone(course_key, 'requires', milestone)

    # add fulfillment course milestone
    add_course_milestone(prerequisite_course_key, 'fulfills', milestone)


def remove_prerequisite_course(course_key, milestone):
    """
    It would remove pre-requisite course milestone for a course
    """

    remove_course_milestone(
        course_key,
        milestone,
    )


def set_prerequisite_courses(course_key, prerequisite_course_keys):
    """
    It would remove any existing requirement milestones for the given `course_key`
    and create new milestones for each pre requisite course in `prerequisite_course_keys`.
    To only remove course milestones pass `course_key` and empty list or
    None as `prerequisite_course_keys` .
    """
    #remove any existing requirement milestones with this pre-requisite course as requirement
    course_milestones = get_course_milestones(course_key=course_key, relationship="requires")
    if course_milestones:
        for milestone in course_milestones:
            remove_prerequisite_course(course_key, milestone)

    # add milestones if pre-requisite course is selected
    if prerequisite_course_keys:
        for prerequisite_course_key_string in prerequisite_course_keys:
            prerequisite_course_key = CourseKey.from_string(prerequisite_course_key_string)
            add_prerequisite_course(course_key, prerequisite_course_key)


def get_pre_requisite_courses_not_completed(user, enrolled_courses):  # pylint: disable=invalid-name
    """
    It would make dict of prerequisite courses not completed by user among courses
    user has enrolled in. It calls the fulfilment api of milestones app and
    iterates over all fulfillments of user not achieved to make dict of
    prerequisites yet to be completed.
    """
    pre_requisite_courses = {}
    if settings.FEATURES.get('ENABLE_PREREQUISITE_COURSES'):
        for course, __ in enrolled_courses:
            required_courses = []
            # if course has pre-requisites then fetch fulfilment path
            if course.pre_requisite_courses:
                fulfilment_paths = get_course_milestones_fulfillment_paths(course.id, {'id': user.id})
                for milestone_key, milestone_value in fulfilment_paths.items():  # pylint: disable=unused-variable
                    for key, value in milestone_value.items():
                        if key == 'courses' and value:
                            for required_course in value:
                                required_course_key = CourseKey.from_string(required_course['course_id'])
                                required_course_descriptor = modulestore().get_course(required_course_key)
                                required_courses.append({
                                    'key': required_course_key,
                                    'display': ' '.join([
                                        required_course_descriptor.display_org_with_default,
                                        required_course_descriptor.display_number_with_default
                                    ])
                                })

                # if there are required courses add to dict
            if required_courses:
                pre_requisite_courses[course.id] = {'courses': required_courses}
    return pre_requisite_courses


def get_prerequisite_courses_display(course_descriptor):  # pylint: disable=invalid-name
    """
    It would retrieve pre-requisite courses, make display strings
    and return them as list
    """
    pre_requisite_courses = []
    if settings.FEATURES.get('ENABLE_PREREQUISITE_COURSES', False) and course_descriptor.pre_requisite_courses:
        for course_id in course_descriptor.pre_requisite_courses:
            course_key = CourseKey.from_string(course_id)
            required_course_descriptor = modulestore().get_course(course_key)
            pre_requisite_courses.append(' '.join([
                required_course_descriptor.display_org_with_default,
                required_course_descriptor.display_number_with_default
            ]))
    return pre_requisite_courses


def fulfill_course_milestone(course_key, user):
    """
    It would save course milestone collected by user.
    """
    course_milestones = get_course_milestones(course_key=course_key, relationship="fulfills")
    for milestone in course_milestones:
        add_user_milestone({'id': user.id}, milestone)


def milestones_achieved_by_user(user):
    """
    It would fetch list of milestones completed by user
    """
    return get_user_milestones({'id': user.id})


def is_valid_course_key(key):
    """
    validates course key. returns True if valid else False.
    """
    try:
        course_key = CourseKey.from_string(key)
    except InvalidKeyError:
        try:
            course_key = SlashSeparatedCourseKey.from_deprecated_string(key)
        except InvalidKeyError:
            course_key = key

    return isinstance(course_key, CourseKey)
