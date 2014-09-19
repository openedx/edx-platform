""" Centralized access to LMS courseware app """
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone

from courseware import courses, module_render
from courseware.model_data import FieldDataCache
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey, Location
from xmodule.modulestore import InvalidLocationError
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError


def _anonymous_known_flag(user):
    if isinstance(user, AnonymousUser):
        user.known = False

def get_modulestore():
    return modulestore()


def get_course(request, user, course_id, depth=0, load_content=False):
    """
    Utility method to obtain course components
    """
    _anonymous_known_flag(user)
    course_descriptor = None
    course_content = None
    course_key = get_course_key(course_id)
    if course_key:
        course_descriptor = get_course_descriptor(course_key, depth)
        if course_descriptor and load_content:
            course_content = get_course_content(request, user, course_key, course_descriptor)
    return course_descriptor, course_key, course_content


def get_course_child(request, user, course_key, content_id, load_content=False):
    """
    Return a course xmodule/xblock to the caller
    """
    _anonymous_known_flag(user)
    child_descriptor = None
    child_content = None
    child_key = get_course_child_key(content_id)
    if child_key:
        child_descriptor = get_course_child_descriptor(child_key)
        if child_descriptor and load_content:
            child_content = get_course_child_content(request, user, course_key, child_descriptor)
    return child_descriptor, child_key, child_content


def get_course_total_score(course_summary):
    """
    Traverse course summary to calculate max possible score for a course
    """
    score = 0
    for chapter in course_summary:  # accumulate score of each chapter
        for section in chapter['sections']:
            if section['section_total']:
                score += section['section_total'][1]
    return score


def get_course_leaf_nodes(course_key, detached_categories):
    """
    Get count of the leaf nodes with ability to exclude some categories
    """
    nodes = []
    verticals = get_modulestore().get_items(course_key, category='vertical')
    for vertical in verticals:
        nodes.extend([unit for unit in vertical.children
                      if getattr(unit, 'category') not in detached_categories])
    return nodes


def get_course_key(course_id, slashseparated=False):
    try:
        course_key = CourseKey.from_string(course_id)
    except InvalidKeyError:
        try:
            course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
        except InvalidKeyError:
            course_key = None
    if slashseparated:
        try:
            course_key = course_key.to_deprecated_string()
        except:
            course_key = course_id
    return course_key


def get_course_descriptor(course_key, depth):
    try:
        course_descriptor = courses.get_course(course_key, depth)
    except ValueError:
        course_descriptor = None
    return course_descriptor


def get_course_content(request, user, course_key, course_descriptor):
    field_data_cache = FieldDataCache([course_descriptor], course_key, user)
    course_content = module_render.get_module_for_descriptor(
        user,
        request,
        course_descriptor,
        field_data_cache,
        course_key)
    return course_content


def course_exists(request, user, course_id):
    course_key = get_course_key(course_id)
    if not course_key:
        return False
    if not get_modulestore().has_course(course_key):
        return False
    return True


def get_course_child_key(content_id):
    try:
        content_key = UsageKey.from_string(content_id)
    except InvalidKeyError:
        try:
            content_key = Location.from_deprecated_string(content_id)
        except (InvalidLocationError, InvalidKeyError):
            content_key = None
    return content_key


def get_course_child_descriptor(child_key):
    try:
        content_descriptor = get_modulestore().get_item(child_key)
    except ItemNotFoundError:
        content_descriptor = None
    return content_descriptor


def get_course_child_content(request, user, course_key, child_descriptor):
    field_data_cache = FieldDataCache([child_descriptor], course_key, user)
    child_content = module_render.get_module_for_descriptor(
        user,
        request,
        child_descriptor,
        field_data_cache,
        course_key)
    return child_content


def calculate_proforma_grade(grade_summary, grading_policy):
    """
    Calculates a projected (proforma) final grade based on the current state
    of grades using the provided grading policy.  Categories equate to grading policy
    'types' and have values such as 'Homework', 'Lab', 'MidtermExam', and 'FinalExam'

    We invert the concepts here and use the category weights as the possible scores by
    assuming that the weights total 100 percent.  So, if a Homework category is worth 15
    percent of your overall grade, and you have currently scored 70 percent for that
    category, the normalized score for the Homework category is 0.105.  Note that
    we do not take into account dropped assignments/scores, such as lowest-two homeworks.

    After all scored categories are processed we apply the average category score to any
    unscored categories using the value as a projection of the user's performance in each category.

    Example:
        - Scored Category: Homework,    Weight: 15%, Totaled Score: 70%,  Normalized Score: 0.105
        - Scored Category: MidtermExam, Weight: 30%, Totaled Score: 80%,  Normalized Score: 0.240
        - Scored Category: Final Exam,  Weight: 40%, Totaled Score: 95%,  Normalized Score: 0.380
        - Average Category Score: (70 + 80 + 95) / 3 = 81.7
        - Unscored Category: Lab,       Weight: 15%, Totaled Score: 81.7%, Normalized Score: 0.123
        - Proforma Grade = 0.105 + 0.240 + 0.380 + 0.123 = 0.8475  (84.8%)
    """
    grade_breakdown = grade_summary['grade_breakdown']
    proforma_grade = 0.00
    totaled_scores = grade_summary['totaled_scores']
    category_averages = []
    categories_to_estimate = []
    for grade_category in grade_breakdown:
        category = grade_category['category']
        item_scores = totaled_scores.get(category)
        if item_scores is not None and len(item_scores):
            total_item_score = 0.00
            items_considered = 0
            for item_score in item_scores:
                if item_score.earned or (item_score.due and item_score.due < timezone.now()):
                    normalized_item_score = item_score.earned / item_score.possible
                    total_item_score += normalized_item_score
                    items_considered += 1
            if total_item_score:
                category_average_score = total_item_score / items_considered
                category_averages.append(category_average_score)
                category_policy = next((policy for policy in grading_policy['GRADER'] if policy['type'] == category), None)
                category_weight = category_policy['weight']
                category_grade = category_average_score * category_weight
                proforma_grade += category_grade
            else:
                categories_to_estimate.append(category)
        else:
            categories_to_estimate.append(category)
    assumed_category_average = sum(category_averages) / len(category_averages)
    for category in categories_to_estimate:
        category_policy = next((policy for policy in grading_policy['GRADER'] if policy['type'] == category), None)
        category_weight = category_policy['weight']
        category_grade = assumed_category_average * category_weight
        proforma_grade += category_grade
    return proforma_grade
