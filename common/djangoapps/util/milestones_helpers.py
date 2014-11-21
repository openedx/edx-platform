"""
Helper methods for milestones api calls.
"""

from collections import defaultdict
from opaque_keys.edx.keys import CourseKey
from milestones.api import (
    get_course_milestones,
    get_courses_milestones,
    get_user_milestones,
    add_milestone,
    add_course_milestone,
    remove_course_milestone,
    get_course_milestones_fulfillment_paths,
)
from django.conf import settings


def get_prerequisite_course_key(course_key):
    """
    Retrieves pre_requisite_course_key for a course from milestones app
    """
    pre_requisite_course_key = None
    course_milestones = get_course_milestones(course_key=course_key, relationship="requires")
    if course_milestones:
        #TODO check if it is valid course key set as namespace
        pre_requisite_course_key = course_milestones[0]['namespace']
    return pre_requisite_course_key


def add_prerequisite_course(course_key, prerequisite_course_key):
    """
    adds pre-requisite course milestone to a course
    """
    # create a milestone
    milestone = add_milestone({
        'name': 'Course {} requires {}'.format(unicode(course_key), unicode(prerequisite_course_key)),
        'namespace': unicode(prerequisite_course_key),
        'description': '',
    })
    # add requirement course milestone
    add_course_milestone(course_key, 'requires', milestone)

    # add fulfillment course milestone
    add_course_milestone(prerequisite_course_key, 'fulfills', milestone)


def remove_prerequisite_course(course_key, milestone):
    """
    remove pre-requisite course milestone for a course
    """

    remove_course_milestone(
        course_key,
        milestone,
    )


def set_prerequisite_course(course_key, prerequisite_course_key_string):
    """
    add or update pre-requisite course milestone for a course
    """
    #remove any existing requirement milestones with this pre-requisite course as requirement
    course_milestones = get_course_milestones(course_key=course_key, relationship="requires")
    if course_milestones:
        for milestone in course_milestones:
            remove_prerequisite_course(course_key, milestone)

    # add milestones if pre-requisite course is selected
    if prerequisite_course_key_string:
        prerequisite_course_key = CourseKey.from_string(prerequisite_course_key_string)
        add_prerequisite_course(course_key, prerequisite_course_key)


def get_pre_requisite_courses(course_ids):
    """
    It would fetch pre-requisite courses for a list of courses

    Returns a dict with keys are set to course id and values are set to pre-requisite course keys .i.e.
    {
        "org/DemoX/2014_T2": {"milestone_id": "1", "prc_id": "org/cs23/2014_T2"}
    }
    """
    courses_dict = defaultdict(dict)
    milestones = get_courses_milestones(course_ids, relationship="requires")
    for milestone in milestones:
        pre_requisite_course_id = milestone['namespace']
        #TODO check if it is valid course key set as namespace
        if pre_requisite_course_id:
            pre_requisite_course_key = CourseKey.from_string(pre_requisite_course_id)
            course_id = CourseKey.from_string(milestone['course_id'])
            courses_dict[course_id] = {
                "milestone_id": milestone['id'],
                "prc_id": pre_requisite_course_key
            }
    return courses_dict


def milestones_achieved_by_user(user):
    """
    It would fetch list of milestones completed by user
    """
    return get_user_milestones(user)


def get_prc_not_completed(user, enrolled_courses):
    """
    It would fetch list of prerequisite courses not completed by user
    """
    pre_requisite_courses = {}
    if settings.FEATURES.get('MILESTONES_APP') and settings.FEATURES.get('ENABLE_PREREQUISITE_COURSES'):
        for course_id in enrolled_courses:
            ful_fillment_paths = get_course_milestones_fulfillment_paths(course_id, {'id': user.id})
            required_courses = []
            for milestone_key, milestone_value in ful_fillment_paths.items():  # pylint: disable=unused-variable
                for key, value in milestone_value.items():
                    if key == 'courses' and value:
                        courses_list = [CourseKey.from_string(course['course_id']) for course in value]
                        required_courses = required_courses + courses_list
            # if there are required course then grab first one since a course can have only single pre-requisite course
            if required_courses:
                pre_requisite_courses[course_id] = {'prc_id': required_courses[0]}
    return pre_requisite_courses


def get_prerequisite_course_display(course_descriptor):
    """
    Retrieves pre-requisite course and makes a display string
    """
    pre_requisite_course_display = ''
    if settings.FEATURES.get('MILESTONES_APP', False) \
            and settings.FEATURES.get('ENABLE_PREREQUISITE_COURSES', False) \
            and course_descriptor.pre_requisite_course:
        pre_requisite_course_key = CourseKey.from_string(course_descriptor.pre_requisite_course)
        pre_requisite_course_display = ' '.join([pre_requisite_course_key.org, pre_requisite_course_key.course])
    return pre_requisite_course_display
