# pylint: disable=invalid-name
"""
Utility library for working with the edx-milestones app
"""

from django.conf import settings
from django.utils.translation import ugettext as _
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from courseware.models import StudentModule
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
from milestones.models import MilestoneRelationshipType
from milestones.exceptions import InvalidMilestoneRelationshipTypeException

NAMESPACE_CHOICES = {
    'ENTRANCE_EXAM': 'entrance_exams'
}


def add_prerequisite_course(course_key, prerequisite_course_key):
    """
    It would create a milestone, then it would set newly created
    milestones as requirement for course referred by `course_key`
    and it would set newly created milestone as fulfilment
    milestone for course referred by `prerequisite_course_key`.
    """
    if settings.FEATURES.get('MILESTONES_APP', False):
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
    It would remove pre-requisite course milestone for course
    referred by `course_key`.
    """
    if settings.FEATURES.get('MILESTONES_APP', False):
        remove_course_milestone(
            course_key,
            milestone,
        )


def set_prerequisite_courses(course_key, prerequisite_course_keys):
    """
    It would remove any existing requirement milestones for the given `course_key`
    and create new milestones for each pre-requisite course in `prerequisite_course_keys`.
    To only remove course milestones pass `course_key` and empty list or
    None as `prerequisite_course_keys` .
    """
    if settings.FEATURES.get('MILESTONES_APP', False):
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


def get_pre_requisite_courses_not_completed(user, enrolled_courses):
    """
    It would make dict of prerequisite courses not completed by user among courses
    user has enrolled in. It calls the fulfilment api of milestones app and
    iterates over all fulfilment milestones not achieved to make dict of
    prerequisite courses yet to be completed.
    """
    pre_requisite_courses = {}
    if settings.FEATURES.get('ENABLE_PREREQUISITE_COURSES'):
        for course_key in enrolled_courses:
            required_courses = []
            fulfilment_paths = get_course_milestones_fulfillment_paths(course_key, {'id': user.id})
            for milestone_key, milestone_value in fulfilment_paths.items():  # pylint: disable=unused-variable
                for key, value in milestone_value.items():
                    if key == 'courses' and value:
                        for required_course in value:
                            required_course_key = CourseKey.from_string(required_course)
                            required_course_descriptor = modulestore().get_course(required_course_key)
                            required_courses.append({
                                'key': required_course_key,
                                'display': get_course_display_name(required_course_descriptor)
                            })

            # if there are required courses add to dict
            if required_courses:
                pre_requisite_courses[course_key] = {'courses': required_courses}
    return pre_requisite_courses


def get_prerequisite_courses_display(course_descriptor):
    """
    It would retrieve pre-requisite courses, make display strings
    and return list of dictionary with course key as 'key' field
    and course display name as `display` field.
    """
    pre_requisite_courses = []
    if settings.FEATURES.get('ENABLE_PREREQUISITE_COURSES', False) and course_descriptor.pre_requisite_courses:
        for course_id in course_descriptor.pre_requisite_courses:
            course_key = CourseKey.from_string(course_id)
            required_course_descriptor = modulestore().get_course(course_key)
            prc = {
                'key': course_key,
                'display': get_course_display_name(required_course_descriptor)
            }
            pre_requisite_courses.append(prc)
    return pre_requisite_courses


def get_course_display_name(descriptor):
    """
    It would return display name from given course descriptor
    """
    return ' '.join([
        descriptor.display_org_with_default,
        descriptor.display_number_with_default
    ])


def fulfill_course_milestone(course_key, user):
    """
    Marks the course specified by the given course_key as complete for the given user.
    If any other courses require this course as a prerequisite, their milestones will be appropriately updated.
    """
    if settings.FEATURES.get('MILESTONES_APP', False):
        course_milestones = get_course_milestones(course_key=course_key, relationship="fulfills")
        for milestone in course_milestones:
            add_user_milestone({'id': user.id}, milestone)


def get_required_content(course, user):
    """
    Queries milestones subsystem to see if the specified course is gated on one or more milestones,
    and if those milestones can be fulfilled via completion of a particular course content module
    """
    required_content = []
    if settings.FEATURES.get('MILESTONES_APP', False):
        # Get all of the outstanding milestones for this course, for this user
        try:
            milestone_paths = get_course_milestones_fulfillment_paths(
                unicode(course.id),
                serialize_user(user)
            )
        except InvalidMilestoneRelationshipTypeException:
            return required_content

        # For each outstanding milestone, see if this content is one of its fulfillment paths
        for path_key in milestone_paths:
            milestone_path = milestone_paths[path_key]
            if milestone_path.get('content') and len(milestone_path['content']):
                for content in milestone_path['content']:
                    required_content.append(content)
    return required_content


def calculate_entrance_exam_score(user, course_descriptor, exam_modules):
    """
    Calculates the score (percent) of the entrance exam using the provided modules
    """
    exam_module_ids = [exam_module.location for exam_module in exam_modules]
    student_modules = StudentModule.objects.filter(
        student=user,
        course_id=course_descriptor.id,
        module_state_key__in=exam_module_ids,
    )
    exam_pct = 0
    if student_modules:
        module_pcts = []
        ignore_categories = ['course', 'chapter', 'sequential', 'vertical']
        for module in exam_modules:
            if module.graded and module.category not in ignore_categories:
                module_pct = 0
                try:
                    student_module = student_modules.get(module_state_key=module.location)
                    if student_module.max_grade:
                        module_pct = student_module.grade / student_module.max_grade
                    module_pcts.append(module_pct)
                except StudentModule.DoesNotExist:
                    pass
        if module_pcts:
            exam_pct = sum(module_pcts) / float(len(module_pcts))
    return exam_pct


def milestones_achieved_by_user(user, namespace):
    """
    It would fetch list of milestones completed by user
    """
    if settings.FEATURES.get('MILESTONES_APP', False):
        return get_user_milestones({'id': user.id}, namespace)


def is_valid_course_key(key):
    """
    validates course key. returns True if valid else False.
    """
    try:
        course_key = CourseKey.from_string(key)
    except InvalidKeyError:
        course_key = key
    return isinstance(course_key, CourseKey)


def seed_milestone_relationship_types():
    """
    Helper method to pre-populate MRTs so the tests can run
    """
    if settings.FEATURES.get('MILESTONES_APP', False):
        MilestoneRelationshipType.objects.create(name='requires')
        MilestoneRelationshipType.objects.create(name='fulfills')


def generate_milestone_namespace(namespace, course_key=None):
    """
    Returns a specifically-formatted namespace string for the specified type
    """
    if namespace in NAMESPACE_CHOICES.values():
        if namespace == 'entrance_exams':
            return '{}.{}'.format(unicode(course_key), NAMESPACE_CHOICES['ENTRANCE_EXAM'])


def serialize_user(user):
    """
    Returns a milestones-friendly representation of a user object
    """
    return {
        'id': user.id,
    }
