"""
Functionality for module-level grades.
"""
# TODO The score computation in this file is not accurate
# since it is summing percentages instead of computing a
# final percentage of the individual sums.
# Regardless, this file and its code should be removed soon
# as part of TNL-5062.

from django.test.client import RequestFactory
from courseware.model_data import FieldDataCache, ScoresClient
from courseware.module_render import get_module_for_descriptor
from opaque_keys.edx.locator import BlockUsageLocator
from util.module_utils import yield_dynamic_descriptor_descendants


def _get_mock_request(student):
    """
    Make a fake request because grading code expects to be able to look at
    the request. We have to attach the correct user to the request before
    grading that student.
    """
    request = RequestFactory().get('/')
    request.user = student
    return request


def _calculate_score_for_modules(user_id, course, modules):
    """
    Calculates the cumulative score (percent) of the given modules
    """

    # removing branch and version from exam modules locator
    # otherwise student module would not return scores since module usage keys would not match
    modules = [m for m in modules]
    locations = [
        BlockUsageLocator(
            course_key=course.id,
            block_type=module.location.block_type,
            block_id=module.location.block_id
        )
        if isinstance(module.location, BlockUsageLocator) and module.location.version
        else module.location
        for module in modules
    ]

    scores_client = ScoresClient(course.id, user_id)
    scores_client.fetch_scores(locations)

    # Iterate over all of the exam modules to get score percentage of user for each of them
    module_percentages = []
    ignore_categories = ['course', 'chapter', 'sequential', 'vertical', 'randomize', 'library_content']
    for index, module in enumerate(modules):
        if module.category not in ignore_categories and (module.graded or module.has_score):
            module_score = scores_client.get(locations[index])
            if module_score:
                correct = module_score.correct or 0
                total = module_score.total or 1
                module_percentages.append(correct / total)

    return sum(module_percentages) / float(len(module_percentages)) if module_percentages else 0


def get_module_score(user, course, module):
    """
    Collects all children of the given module and calculates the cumulative
    score for this set of modules for the given user.

    Arguments:
        user (User): The user
        course (CourseModule): The course
        module (XBlock): The module

    Returns:
        float: The cumulative score
    """
    def inner_get_module(descriptor):
        """
        Delegate to get_module_for_descriptor
        """
        field_data_cache = FieldDataCache([descriptor], course.id, user)
        return get_module_for_descriptor(
            user,
            _get_mock_request(user),
            descriptor,
            field_data_cache,
            course.id,
            course=course
        )

    modules = yield_dynamic_descriptor_descendants(
        module,
        user.id,
        inner_get_module
    )
    return _calculate_score_for_modules(user.id, course, modules)
