# pylint: disable=invalid-name
"""
Utility library for working with the edx-milestones app
"""

from django.conf import settings
from django.utils.translation import ugettext as _

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from milestones import api as milestones_api
from milestones.exceptions import InvalidMilestoneRelationshipTypeException
from milestones.models import MilestoneRelationshipType
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from xmodule.modulestore.django import modulestore
import request_cache

NAMESPACE_CHOICES = {
    'ENTRANCE_EXAM': 'entrance_exams'
}

REQUEST_CACHE_NAME = "milestones"


def get_namespace_choices():
    """
    Return the enum to the caller
    """
    return NAMESPACE_CHOICES


def is_entrance_exams_enabled():
    """
    Checks to see if the Entrance Exams feature is enabled
    Use this operation instead of checking the feature flag all over the place
    """
    return settings.FEATURES.get('ENTRANCE_EXAMS')


def is_prerequisite_courses_enabled():
    """
    Returns boolean indicating prerequisite courses enabled system wide or not.
    """
    return settings.FEATURES.get('ENABLE_PREREQUISITE_COURSES') and settings.FEATURES.get('MILESTONES_APP')


def add_prerequisite_course(course_key, prerequisite_course_key):
    """
    It would create a milestone, then it would set newly created
    milestones as requirement for course referred by `course_key`
    and it would set newly created milestone as fulfillment
    milestone for course referred by `prerequisite_course_key`.
    """
    if not is_prerequisite_courses_enabled():
        return None
    milestone_name = _('Course {course_id} requires {prerequisite_course_id}').format(
        course_id=unicode(course_key),
        prerequisite_course_id=unicode(prerequisite_course_key)
    )
    milestone = milestones_api.add_milestone({
        'name': milestone_name,
        'namespace': unicode(prerequisite_course_key),
        'description': _('System defined milestone'),
    })
    # add requirement course milestone
    milestones_api.add_course_milestone(course_key, 'requires', milestone)

    # add fulfillment course milestone
    milestones_api.add_course_milestone(prerequisite_course_key, 'fulfills', milestone)


def remove_prerequisite_course(course_key, milestone):
    """
    It would remove pre-requisite course milestone for course
    referred by `course_key`.
    """
    if not is_prerequisite_courses_enabled():
        return None
    milestones_api.remove_course_milestone(
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
    if not is_prerequisite_courses_enabled():
        return None
    #remove any existing requirement milestones with this pre-requisite course as requirement
    course_milestones = milestones_api.get_course_milestones(course_key=course_key, relationship="requires")
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
    Makes a dict mapping courses to their unfulfilled milestones using the
    fulfillment API of the milestones app.

    Arguments:
        user (User): the user for whom we are checking prerequisites.
        enrolled_courses (CourseKey): a list of keys for the courses to be
            checked. The given user must be enrolled in all of these courses.

    Returns:
        dict[CourseKey: dict[
            'courses': list[dict['key': CourseKey, 'display': str]]
        ]]
        If a course has no incomplete prerequisites, it will be excluded from the
        dictionary.
    """
    if not is_prerequisite_courses_enabled():
        return {}

    pre_requisite_courses = {}

    for course_key in enrolled_courses:
        required_courses = []
        fulfillment_paths = milestones_api.get_course_milestones_fulfillment_paths(course_key, {'id': user.id})
        for __, milestone_value in fulfillment_paths.items():
            for key, value in milestone_value.items():
                if key == 'courses' and value:
                    for required_course in value:
                        required_course_key = CourseKey.from_string(required_course)
                        required_course_overview = CourseOverview.get_from_id(required_course_key)
                        required_courses.append({
                            'key': required_course_key,
                            'display': get_course_display_string(required_course_overview)
                        })
        # If there are required courses, add them to the result dict.
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
    if is_prerequisite_courses_enabled() and course_descriptor.pre_requisite_courses:
        for course_id in course_descriptor.pre_requisite_courses:
            course_key = CourseKey.from_string(course_id)
            required_course_descriptor = modulestore().get_course(course_key)
            prc = {
                'key': course_key,
                'display': get_course_display_string(required_course_descriptor)
            }
            pre_requisite_courses.append(prc)
    return pre_requisite_courses


def get_course_display_string(descriptor):
    """
    Returns a string to display for a course or course overview.

    Arguments:
        descriptor (CourseDescriptor|CourseOverview): a course or course overview.
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
    if not settings.FEATURES.get('MILESTONES_APP'):
        return None
    try:
        course_milestones = milestones_api.get_course_milestones(course_key=course_key, relationship="fulfills")
    except InvalidMilestoneRelationshipTypeException:
        # we have not seeded milestone relationship types
        seed_milestone_relationship_types()
        course_milestones = milestones_api.get_course_milestones(course_key=course_key, relationship="fulfills")
    for milestone in course_milestones:
        milestones_api.add_user_milestone({'id': user.id}, milestone)


def remove_course_milestones(course_key, user, relationship):
    """
    Remove all user milestones for the course specified by course_key.
    """
    if not settings.FEATURES.get('MILESTONES_APP'):
        return None
    course_milestones = milestones_api.get_course_milestones(course_key=course_key, relationship=relationship)
    for milestone in course_milestones:
        milestones_api.remove_user_milestone({'id': user.id}, milestone)


def get_required_content(course, user):
    """
    Queries milestones subsystem to see if the specified course is gated on one or more milestones,
    and if those milestones can be fulfilled via completion of a particular course content module
    """
    required_content = []
    if settings.FEATURES.get('MILESTONES_APP'):
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


def milestones_achieved_by_user(user, namespace):
    """
    It would fetch list of milestones completed by user
    """
    if not settings.FEATURES.get('MILESTONES_APP'):
        return None
    return milestones_api.get_user_milestones({'id': user.id}, namespace)


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
    if not settings.FEATURES.get('MILESTONES_APP'):
        return None
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


def add_milestone(milestone_data):
    """
    Client API operation adapter/wrapper
    """
    if not settings.FEATURES.get('MILESTONES_APP'):
        return None
    return milestones_api.add_milestone(milestone_data)


def get_milestones(namespace):
    """
    Client API operation adapter/wrapper
    """
    if not settings.FEATURES.get('MILESTONES_APP'):
        return []
    return milestones_api.get_milestones(namespace)


def get_milestone_relationship_types():
    """
    Client API operation adapter/wrapper
    """
    if not settings.FEATURES.get('MILESTONES_APP'):
        return {}
    return milestones_api.get_milestone_relationship_types()


def add_course_milestone(course_id, relationship, milestone):
    """
    Client API operation adapter/wrapper
    """
    if not settings.FEATURES.get('MILESTONES_APP'):
        return None
    return milestones_api.add_course_milestone(course_id, relationship, milestone)


def get_course_milestones(course_id):
    """
    Client API operation adapter/wrapper
    """
    if not settings.FEATURES.get('MILESTONES_APP'):
        return []
    return milestones_api.get_course_milestones(course_id)


def add_course_content_milestone(course_id, content_id, relationship, milestone):
    """
    Client API operation adapter/wrapper
    """
    if not settings.FEATURES.get('MILESTONES_APP'):
        return None
    return milestones_api.add_course_content_milestone(course_id, content_id, relationship, milestone)


def get_course_content_milestones(course_id, content_id, relationship, user_id=None):
    """
    Client API operation adapter/wrapper
    Uses the request cache to store all of a user's
    milestones
    """
    if not settings.FEATURES.get('MILESTONES_APP'):
        return []

    if user_id is None:
        return milestones_api.get_course_content_milestones(course_id, content_id, relationship)

    request_cache_dict = request_cache.get_cache(REQUEST_CACHE_NAME)
    if user_id not in request_cache_dict:
        request_cache_dict[user_id] = {}

    if relationship not in request_cache_dict[user_id]:
        request_cache_dict[user_id][relationship] = milestones_api.get_course_content_milestones(
            course_key=course_id,
            relationship=relationship,
            user={"id": user_id}
        )

    return [m for m in request_cache_dict[user_id][relationship] if m['content_id'] == content_id]


def remove_course_content_user_milestones(course_key, content_key, user, relationship):
    """
    Removes the specified User-Milestone link from the system for the specified course content module.
    """
    if not settings.FEATURES.get('MILESTONES_APP'):
        return []

    course_content_milestones = milestones_api.get_course_content_milestones(course_key, content_key, relationship)
    for milestone in course_content_milestones:
        milestones_api.remove_user_milestone({'id': user.id}, milestone)


def remove_content_references(content_id):
    """
    Client API operation adapter/wrapper
    """
    if not settings.FEATURES.get('MILESTONES_APP'):
        return None
    return milestones_api.remove_content_references(content_id)


def any_unfulfilled_milestones(course_id, user_id):
    """ Returns a boolean if user has any unfulfilled milestones """
    if not settings.FEATURES.get('MILESTONES_APP'):
        return False
    return bool(
        get_course_milestones_fulfillment_paths(course_id, {"id": user_id})
    )


def get_course_milestones_fulfillment_paths(course_id, user_id):
    """
    Client API operation adapter/wrapper
    """
    if not settings.FEATURES.get('MILESTONES_APP'):
        return None
    return milestones_api.get_course_milestones_fulfillment_paths(
        course_id,
        user_id
    )


def add_user_milestone(user, milestone):
    """
    Client API operation adapter/wrapper
    """
    if not settings.FEATURES.get('MILESTONES_APP'):
        return None
    return milestones_api.add_user_milestone(user, milestone)


def remove_user_milestone(user, milestone):
    """
    Client API operation adapter/wrapper
    """
    if not settings.FEATURES.get('MILESTONES_APP'):
        return None
    return milestones_api.remove_user_milestone(user, milestone)
