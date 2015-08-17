"""
This file contains all entrance exam related utils/logic.
"""
from django.conf import settings

from courseware.access import has_access
from courseware.model_data import FieldDataCache
from courseware.models import StudentModule
from opaque_keys.edx.keys import UsageKey
from student.models import EntranceExamConfiguration
from util.milestones_helpers import get_required_content
from util.module_utils import yield_dynamic_descriptor_descendants
from xmodule.modulestore.django import modulestore


def feature_is_enabled():
    """
    Checks to see if the Entrance Exams feature is enabled
    Use this operation instead of checking the feature flag all over the place
    """
    return settings.FEATURES.get('ENTRANCE_EXAMS', False)


def course_has_entrance_exam(course):
    """
    Checks to see if a course is properly configured for an entrance exam
    """
    if not feature_is_enabled():
        return False
    if not course.entrance_exam_enabled:
        return False
    if not course.entrance_exam_id:
        return False
    return True


def user_can_skip_entrance_exam(request, user, course):
    """
    Checks all of the various override conditions for a user to skip an entrance exam
    Begin by short-circuiting if the course does not have an entrance exam
    """
    if not course_has_entrance_exam(course):
        return True
    if not user.is_authenticated():
        return False
    if has_access(user, 'staff', course):
        return True
    if EntranceExamConfiguration.user_can_skip_entrance_exam(user, course.id):
        return True
    if not get_entrance_exam_content(request, course):
        return True
    return False


def user_has_passed_entrance_exam(request, course):
    """
    Checks to see if the user has attained a sufficient score to pass the exam
    Begin by short-circuiting if the course does not have an entrance exam
    """
    if not course_has_entrance_exam(course):
        return True
    if not request.user.is_authenticated():
        return False
    entrance_exam_score = get_entrance_exam_score(request, course)
    if entrance_exam_score >= course.entrance_exam_minimum_score_pct:
        return True
    return False


# pylint: disable=invalid-name
def user_must_complete_entrance_exam(request, user, course):
    """
    Some courses can be gated on an Entrance Exam, which is a specially-configured chapter module which
    presents users with a problem set which they must complete.  This particular workflow determines
    whether or not the user is allowed to clear the Entrance Exam gate and access the rest of the course.
    """
    # First, let's see if the user is allowed to skip
    if user_can_skip_entrance_exam(request, user, course):
        return False
    # If they can't actually skip the exam, we'll need to see if they've already passed it
    if user_has_passed_entrance_exam(request, course):
        return False
    # Can't skip, haven't passed, must take the exam
    return True


def _calculate_entrance_exam_score(user, course_descriptor, exam_modules):
    """
    Calculates the score (percent) of the entrance exam using the provided modules
    """
    # All of the exam module ids
    exam_module_ids = [exam_module.location for exam_module in exam_modules]

    # All of the corresponding student module records
    student_modules = StudentModule.objects.filter(
        student=user,
        course_id=course_descriptor.id,
        module_state_key__in=exam_module_ids,
    )
    student_module_dict = {}
    for student_module in student_modules:
        student_module_dict[unicode(student_module.module_state_key)] = {
            'grade': student_module.grade,
            'max_grade': student_module.max_grade
        }
    exam_percentage = 0
    module_percentages = []
    ignore_categories = ['course', 'chapter', 'sequential', 'vertical']

    for module in exam_modules:
        if module.graded and module.category not in ignore_categories:
            module_percentage = 0
            module_location = unicode(module.location)
            if module_location in student_module_dict and student_module_dict[module_location]['max_grade']:
                student_module = student_module_dict[module_location]
                module_percentage = student_module['grade'] / student_module['max_grade']

            module_percentages.append(module_percentage)
    if module_percentages:
        exam_percentage = sum(module_percentages) / float(len(module_percentages))
    return exam_percentage


def get_entrance_exam_score(request, course):
    """
    Gather the set of modules which comprise the entrance exam
    Note that 'request' may not actually be a genuine request, due to the
    circular nature of module_render calling entrance_exams and get_module_for_descriptor
    being used here.  In some use cases, the caller is actually mocking a request, although
    in these scenarios the 'user' child object can be trusted and used as expected.
    It's a much larger refactoring job to break this legacy mess apart, unfortunately.
    """
    exam_key = UsageKey.from_string(course.entrance_exam_id)
    exam_descriptor = modulestore().get_item(exam_key)

    def inner_get_module(descriptor):
        """
        Delegate to get_module_for_descriptor (imported here to avoid circular reference)
        """
        from courseware.module_render import get_module_for_descriptor
        field_data_cache = FieldDataCache([descriptor], course.id, request.user)
        return get_module_for_descriptor(
            request.user,
            request,
            descriptor,
            field_data_cache,
            course.id,
            course=course
        )

    exam_module_generators = yield_dynamic_descriptor_descendants(
        exam_descriptor,
        request.user.id,
        inner_get_module
    )
    exam_modules = [module for module in exam_module_generators]
    return _calculate_entrance_exam_score(request.user, course, exam_modules)


def get_entrance_exam_content(request, course):
    """
    Get the entrance exam content information (ie, chapter module)
    """
    required_content = get_required_content(course, request.user)

    exam_module = None
    for content in required_content:
        usage_key = course.id.make_usage_key_from_deprecated_string(content)
        module_item = modulestore().get_item(usage_key)
        if not module_item.hide_from_toc and module_item.is_entrance_exam:
            exam_module = module_item
            break
    return exam_module
