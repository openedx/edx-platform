"""
API for the gating djangoapp
"""
import logging

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from lms.djangoapps.courseware.access import _has_access_to_course
from lms.djangoapps.course_blocks.api import get_course_blocks
from lms.djangoapps.grades.subsection_grade_factory import SubsectionGradeFactory
from milestones import api as milestones_api
from opaque_keys.edx.keys import UsageKey
from opaque_keys.edx.locator import BlockUsageLocator
from openedx.core.lib.gating.exceptions import GatingValidationError
from xmodule.modulestore.django import modulestore

log = logging.getLogger(__name__)

# This is used to namespace gating-specific milestones
GATING_NAMESPACE_QUALIFIER = '.gating'


def _get_prerequisite_milestone(prereq_content_key):
    """
    Get gating milestone associated with the given content usage key.

    Arguments:
        prereq_content_key (str|UsageKey): The content usage key

    Returns:
        dict: Milestone dict
    """
    milestones = milestones_api.get_milestones("{usage_key}{qualifier}".format(
        usage_key=prereq_content_key,
        qualifier=GATING_NAMESPACE_QUALIFIER
    ))

    if not milestones:
        log.warning("Could not find gating milestone for prereq UsageKey %s", prereq_content_key)
        return None

    if len(milestones) > 1:
        # We should only ever have one gating milestone per UsageKey
        # Log a warning here and pick the first one
        log.warning("Multiple gating milestones found for prereq UsageKey %s", prereq_content_key)

    return milestones[0]


def _validate_min_score(min_score):
    """
    Validates the minimum score entered by the Studio user.

    Arguments:
        min_score (str|int): The minimum score to validate

    Returns:
        None

    Raises:
        GatingValidationError: If the minimum score is not valid
    """
    if min_score:
        message = _("%(min_score)s is not a valid grade percentage") % {'min_score': min_score}
        try:
            min_score = int(min_score)
        except ValueError:
            raise GatingValidationError(message)

        if min_score < 0 or min_score > 100:
            raise GatingValidationError(message)


def gating_enabled(default=None):
    """
    Decorator that checks the enable_subsection_gating course flag to
    see if the subsection gating feature is active for a given course.
    If not, calls to the decorated function return the specified default value.

    Arguments:
        default (ANY): The value to return if the enable_subsection_gating course flag is False

    Returns:
        ANY: The specified default value if the gating feature is off,
        otherwise the result of the decorated function
    """
    def wrap(f):  # pylint: disable=missing-docstring
        def function_wrapper(course, *args):  # pylint: disable=missing-docstring
            if not course.enable_subsection_gating:
                return default
            return f(course, *args)
        return function_wrapper
    return wrap


def find_gating_milestones(course_key, content_key=None, relationship=None, user=None):
    """
    Finds gating milestone dicts related to the given supplied parameters.

    Arguments:
        course_key (str|CourseKey): The course key
        content_key (str|UsageKey): The content usage key
        relationship (str): The relationship type (e.g. 'requires')
        user (dict): The user dict (e.g. {'id': 4})

    Returns:
        list: A list of milestone dicts
    """
    return [
        m for m in milestones_api.get_course_content_milestones(course_key, content_key, relationship, user)
        if GATING_NAMESPACE_QUALIFIER in m.get('namespace')
    ]


def get_gating_milestone(course_key, content_key, relationship):
    """
    Gets a single gating milestone dict related to the given supplied parameters.

    Arguments:
        course_key (str|CourseKey): The course key
        content_key (str|UsageKey): The content usage key
        relationship (str): The relationship type (e.g. 'requires')

    Returns:
        dict or None: The gating milestone dict or None
    """
    try:
        return find_gating_milestones(course_key, content_key, relationship)[0]
    except IndexError:
        return None


def get_prerequisites(course_key):
    """
    Find all the gating milestones associated with a course and the
    XBlock info associated with those gating milestones.

    Arguments:
        course_key (str|CourseKey): The course key

    Returns:
        list: A list of dicts containing the milestone and associated XBlock info
    """
    course_content_milestones = find_gating_milestones(course_key)

    milestones_by_block_id = {}
    block_ids = []
    for milestone in course_content_milestones:
        prereq_content_key = milestone['namespace'].replace(GATING_NAMESPACE_QUALIFIER, '')
        block_id = UsageKey.from_string(prereq_content_key).block_id
        block_ids.append(block_id)
        milestones_by_block_id[block_id] = milestone

    result = []
    for block in modulestore().get_items(course_key, qualifiers={'name': block_ids}):
        milestone = milestones_by_block_id.get(block.location.block_id)
        if milestone:
            milestone['block_display_name'] = block.display_name
            milestone['block_usage_key'] = unicode(block.location)
            result.append(milestone)

    return result


def add_prerequisite(course_key, prereq_content_key):
    """
    Creates a new Milestone and CourseContentMilestone indicating that
    the given course content fulfills a prerequisite for gating

    Arguments:
        course_key (str|CourseKey): The course key
        prereq_content_key (str|UsageKey): The prerequisite content usage key

    Returns:
        None
    """
    milestone = milestones_api.add_milestone(
        {
            'name': _('Gating milestone for {usage_key}').format(usage_key=unicode(prereq_content_key)),
            'namespace': "{usage_key}{qualifier}".format(
                usage_key=prereq_content_key,
                qualifier=GATING_NAMESPACE_QUALIFIER
            ),
            'description': _('System defined milestone'),
        },
        propagate=False
    )
    milestones_api.add_course_content_milestone(course_key, prereq_content_key, 'fulfills', milestone)


def remove_prerequisite(prereq_content_key):
    """
    Removes the Milestone and CourseContentMilestones related to the gating
    prerequisite which the given course content fulfills

    Arguments:
        prereq_content_key (str|UsageKey): The prerequisite content usage key

    Returns:
        None
    """
    milestones = milestones_api.get_milestones("{usage_key}{qualifier}".format(
        usage_key=prereq_content_key,
        qualifier=GATING_NAMESPACE_QUALIFIER
    ))
    for milestone in milestones:
        milestones_api.remove_milestone(milestone.get('id'))


def is_prerequisite(course_key, prereq_content_key):
    """
    Returns True if there is at least one CourseContentMilestone
    which the given course content fulfills

    Arguments:
        course_key (str|CourseKey): The course key
        prereq_content_key (str|UsageKey): The prerequisite content usage key

    Returns:
        bool: True if the course content fulfills a CourseContentMilestone, otherwise False
    """
    return get_gating_milestone(
        course_key,
        prereq_content_key,
        'fulfills'
    ) is not None


def set_required_content(course_key, gated_content_key, prereq_content_key, min_score):
    """
    Adds a `requires` milestone relationship for the given gated_content_key if a prerequisite
    prereq_content_key is provided. If prereq_content_key is None, removes the `requires`
    milestone relationship.

    Arguments:
        course_key (str|CourseKey): The course key
        gated_content_key (str|UsageKey): The gated content usage key
        prereq_content_key (str|UsageKey): The prerequisite content usage key
        min_score (str|int): The minimum score

    Returns:
        None
    """
    milestone = None
    for gating_milestone in find_gating_milestones(course_key, gated_content_key, 'requires'):
        if not prereq_content_key or prereq_content_key not in gating_milestone.get('namespace'):
            milestones_api.remove_course_content_milestone(course_key, gated_content_key, gating_milestone)
        else:
            milestone = gating_milestone

    if prereq_content_key:
        _validate_min_score(min_score)
        requirements = {'min_score': min_score}
        if not milestone:
            milestone = _get_prerequisite_milestone(prereq_content_key)
        milestones_api.add_course_content_milestone(course_key, gated_content_key, 'requires', milestone, requirements)


def get_required_content(course_key, gated_content_key):
    """
    Returns the prerequisite content usage key and minimum score needed for fulfillment
    of that prerequisite for the given gated_content_key.

    Args:
        course_key (str|CourseKey): The course key
        gated_content_key (str|UsageKey): The gated content usage key

    Returns:
        tuple: The prerequisite content usage key and minimum score, (None, None) if the content is not gated
    """
    milestone = get_gating_milestone(course_key, gated_content_key, 'requires')
    if milestone:
        return (
            milestone.get('namespace', '').replace(GATING_NAMESPACE_QUALIFIER, ''),
            milestone.get('requirements', {}).get('min_score')
        )
    else:
        return None, None


@gating_enabled(default=[])
def get_gated_content(course, user):
    """
    Returns the unfulfilled gated content usage keys in the given course.

    Arguments:
        course (CourseDescriptor): The course
        user (User): The user

    Returns:
        list: The list of gated content usage keys for the given course
    """
    if _has_access_to_course(user, 'staff', course.id):
        return []
    else:
        # Get the unfulfilled gating milestones for this course, for this user
        return [
            m['content_id'] for m in find_gating_milestones(
                course.id,
                None,
                'requires',
                {'id': user.id}
            )
        ]

def _get_block_id(milestone):
    """
    Get the block id for the given milestone
    """
    prereq_content_key = milestone['namespace'].replace(GATING_NAMESPACE_QUALIFIER, '')
    block_id = UsageKey.from_string(prereq_content_key).block_id
    return block_id

def _get_minimum_required_percentage(milestone):
    """
    Returns the minimum percentage requirement for the given milestone.
    """
    # Default minimum score to 100
    min_score = 100
    requirements = milestone.get('requirements')
    if requirements:
        try:
            min_score = int(requirements.get('min_score'))
        except (ValueError, TypeError):
            log.warning(
                u'Gating: Failed to find minimum score for gating milestone %s, defaulting to 100',
            )
    return min_score


def _get_subsection_percentage(subsection_grade):
    """
    Returns the percentage value of the given subsection_grade.
    """
    return _calculate_ratio(subsection_grade.graded_total.earned, subsection_grade.graded_total.possible) * 100.0

def _calculate_ratio(earned, possible):
    """
    Returns the percentage of the given earned and possible values.
    """
    return float(earned) / float(possible) if possible else 0.0

def get_gating_milestone_meta_info(course_id, milestone):
    """
    Returns dict containing meta information about given milestone

    Arguments:
        course_id: The id of the course
        milestone (Milestone): The gating milestone

    Returns:
        dict of {'url': gating_milestone_url, 'display_name': gating_milestone_display_name}
    """
    prereq_content_key = milestone['namespace'].replace(GATING_NAMESPACE_QUALIFIER, '')
    gating_milestone_url = reverse('jump_to', kwargs={'course_id': course_id, 'location': prereq_content_key})
    block_id = UsageKey.from_string(prereq_content_key).block_id
    blocks = modulestore().get_items(course_id, qualifiers={'name': [block_id]})
    if blocks:
        gating_milestone_display_name = blocks[0].display_name
    return {'url': gating_milestone_url, 'display_name': gating_milestone_display_name}


def is_prereq_met(course_id, content_id, user_id, recalc_on_unmet=False):
    """
    Returns true if the prequiste has been met for a given milestone

    Arguments:
        course_id (CourseLocator): CourseLocator object for the course
        content_id (BlockUsageLocator): BlockUsageLocator for the content
        user_id: The id of the user
        recalc_on_unmet: Recalculate the grade if prereq has not yet been met
    """
    # first check source of truth.. the database
    #prereq_met = milestones_api.user_has_milestone({'id': user_id}, milestone)
    unfulfilled_milestones = milestones_api.get_course_content_milestones(course_id, content_id, 'requires', {'id': user_id})
    prereq_met = not unfulfilled_milestones


    if prereq_met or not recalc_on_unmet:
        return prereq_met

    student = User.objects.get(id=user_id)
    store = modulestore()

    with store.bulk_operations(course_id):
        course_structure = get_course_blocks(student, store.make_course_usage_key(course_id))
        course = store.get_course(course_id, depth=0)
        subsection_grade_factory = SubsectionGradeFactory(student, course, course_structure)
        subsection_usage_key = BlockUsageLocator(course_id, 'sequential', _get_block_id(unfulfilled_milestones[0]))
        if subsection_usage_key in course_structure:
            subsection_grade = subsection_grade_factory.update(
                course_structure[subsection_usage_key]
            )
            min_percentage = _get_minimum_required_percentage(unfulfilled_milestones[0])
            subsection_percentage = _get_subsection_percentage(subsection_grade)
            if subsection_percentage >= min_percentage:
                prereq_met = True
                #milestones_helpers.add_user_milestone({'id': user.id}, prereq_milestone)
            else:
                prereq_met = False
                #milestones_helpers.remove_user_milestone({'id': user.id}, prereq_milestone)

    return prereq_met
