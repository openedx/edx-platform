from logging import getLogger

from django.conf import settings
from django.core.urlresolvers import reverse

from courseware.models import StudentModule
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import BlockUsageLocator
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from xmodule.modulestore.django import modulestore
from philu_commands.helpers import generate_course_structure

from . import constants

log = getLogger(__name__)


def get_nth_chapter_link(course, chapter_index=0):
    course_chapters = modulestore().get_items(
        course.id,
        qualifiers={'category': 'course'}
    )
    if not course_chapters:
        log.info("%s Course dont have any chapters", course.display_name)


    try:
        chapter = course_chapters[0].children[chapter_index]
    except IndexError:
        return ""

    subsection = modulestore().get_item(chapter).children[0]

    course_target = reverse(
        'courseware_section',
        args=[course.id.to_deprecated_string(),
              chapter.block_id,
              subsection.block_id]
    )

    base_url = settings.LMS_ROOT_URL

    return base_url + course_target


def get_competency_assessments_score(user, course_id, chapter_id, section_id, is_pre):
    """
    Return competency assessments scores of user in chapter of specified course

    :param user: user
    :param course_id: the identifier for the course.
    :param chapter_id: chapter url_name.
    :param section_id: section url_name.
    :param is_pre: Boolean to check if the assessment is pre or post.
    :return: assessments score dictionary
    :raises:
        NotFound: if chapter, pre or post assessment not found
    """

    course_key = CourseKey.from_string(course_id)
    course_block = get_course_block_key(course_key)
    course_struct = generate_course_structure(course_key)['structure']

    pre_assessment_score = post_assessment_score = None
    pre_assessment_attempted = all_pre_assessment_attempted = all_post_assessment_attempted = None

    if is_pre == 'True':
        pre_block = BlockUsageLocator.from_string(get_complete_block_key(course_block, section_id, 'sequential'))
        pre_assessment_score, pre_assessment_attempted, all_pre_assessment_attempted = get_assessment_score(
            user, pre_block)

    else:
        post_block = BlockUsageLocator.from_string(get_complete_block_key(course_block, section_id, 'sequential'))
        post_assessment_score, post_assessment_attempted, all_post_assessment_attempted = get_assessment_score(
            user, post_block)

        chapter_block_key = get_complete_block_key(course_block, chapter_id, 'chapter')
        chapter_children = course_struct['blocks'][chapter_block_key]['children']

        for child in chapter_children:
            if course_struct['blocks'][child]['format'].lower() == constants.PRE_ASSESSMENT_FORMAT:
                pre_block = BlockUsageLocator.from_string(child)
                break

        if pre_block:
            pre_assessment_score, pre_assessment_attempted, all_pre_assessment_attempted = get_assessment_score(
                user, pre_block)

    return {
        'pre_assessment_score': pre_assessment_score,
        'post_assessment_score': post_assessment_score,
        'pre_assessment_attempted': pre_assessment_attempted,
        'all_pre_assessment_attempted': all_pre_assessment_attempted,
        'all_post_assessment_attempted': all_post_assessment_attempted,
    }


def is_all_attempted(section):
    attempted_problem_scores = [score for score in section.problem_scores.values()
                                    if score.first_attempted] \
                                    if section and section.problem_scores else []
    problems_count = configuration_helpers.get_value("COMPETENCY_ASSESSMENT_PROBLEMS_COUNT",
                        constants.COMPETENCY_ASSESSMENT_DEFAULT_PROBLEMS_COUNT)
    return len(attempted_problem_scores) == problems_count


def is_pre_assessment(section):
    return get_section_format(section) == constants.PRE_ASSESSMENT_FORMAT


def is_post_assessment(section):
    return get_section_format(section) == constants.POST_ASSESSMENT_FORMAT


def get_section_format(section):
    return section.format.lower() if section and section.format else ''


def get_complete_block_key(course_id, block_id, block_type):
    return constants.BLOCK_KEY_FORMATTER.format(course_id=course_id, block_type=block_type, block_id=block_id)
    # return 'block-v1:'+course_id+'+type@'+block_type+'+block@'+block_id


def get_course_block_key(course_key):
    return constants.COURSE_KEY_FORMATTER.format(org=course_key.org, course_name=course_key.course, run=course_key.run)


def get_assessment_score(user, assessment_block_key):
    sequential = modulestore().get_item(assessment_block_key)
    pre_problems = modulestore().get_item(sequential.children[0]).children

    assessment_score = 0
    problem_attempted = 0
    assessment_attempted = False
    all_problem_attempted = False

    for problem in pre_problems:
        try:
            problem_submission = StudentModule.objects.get(student=user, module_state_key=problem)
            if problem_submission.grade is not None:
                assessment_attempted = True
                problem_attempted += 1
            assessment_score = assessment_score + int(problem_submission.grade if problem_submission.grade is not None else 0)
        except StudentModule.DoesNotExist:
            pass
    if problem_attempted == constants.COMPETENCY_ASSESSMENT_DEFAULT_PROBLEMS_COUNT:
        all_problem_attempted = True
    return assessment_score, assessment_attempted, all_problem_attempted
