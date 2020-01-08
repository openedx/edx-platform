from logging import getLogger

from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from rest_framework.exceptions import NotFound

from courseware.courses import get_course_with_access
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from xmodule.modulestore.django import modulestore

from lms.djangoapps.grades.course_grade_factory import CourseGradeFactory

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


def get_competency_assessments_score(user, course_id, chapter_id):
    """
    Return competency assessments scores of user in chapter of specified course

    :param user: user
    :param course_id: the identifier for the course.
    :param chapter_id: chapter url_name.
    :return: assessments score dictionary
    :raises:
        NotFound: if chapter, pre or post assessment not found
    """

    # course_chapters = modulestore().get_items(
    #     course_key,
    #     qualifiers={'category': 'course'}
    # )

    from courseware.models import StudentModule
    from opaque_keys.edx.locator import BlockUsageLocator
    from philu_commands.helpers import generate_course_structure

    # pre_block = BlockUsageLocator.from_string('block-v1:Arbisoft+CSAPI_101+2020_01+type@sequential+block@f90e748bbf9f4d97bdcc0934e5d16a61')     #  Local Server
    pre_block = BlockUsageLocator.from_string('block-v1:Collins+CE101+4_2.44_20200301_20200330+type@sequential+block@636647b14ddd4f7e96aa7a6b82b47d20')
    pre_sequential = modulestore().get_item(pre_block)
    pre_problems = modulestore().get_item(pre_sequential.children[0]).children

    student_pre_assessment_score = 0
    total_pre_assessment_score = len(pre_problems)

    for problem in pre_problems:
        sm = StudentModule.objects.get(student=user, module_state_key=problem)
        student_pre_assessment_score = student_pre_assessment_score + int(sm.grade if sm.grade is not None else 0)

    course_key = CourseKey.from_string(course_id)
    course_struct = generate_course_structure(course_key)['structure']

    # chapter_children = course_struct['blocks']['block-v1:Arbisoft+CSAPI_101+2020_01+type@chapter+block@f5e6f0a629134ac893c883d96d1e2e86']['children']  # Local Server
    chapter_children = course_struct['blocks']['block-v1:Collins+CE101+4_2.44_20200301_20200330+type@chapter+block@e58cf0e176204ec5b5628e508caa1047']['children']

    for child in chapter_children:
        if course_struct['blocks'][child]['format'] == 'Post Assessment':
            post_block = BlockUsageLocator.from_string(child)
            break

    student_post_assessment_score = 0
    if post_block:
        post_sequential = modulestore().get_item(post_block)
        post_problems = modulestore().get_item(post_sequential.children[0]).children

        total_post_assessment_score = len(post_problems)

        for problem in post_problems:
            try:
                sm = StudentModule.objects.get(student=user, module_state_key=problem)
                student_post_assessment_score = student_post_assessment_score + int(sm.grade if sm.grade is not None else 0)
            except StudentModule.DoesNotExist:
                pass

    course = get_course_with_access(user, 'load', course_key,
                                    check_if_enrolled=True)
    course_grade = CourseGradeFactory().read(user, course)
    chapter_grade = course_grade.chapter_grades.values()
    try:
        chapter = next(chapter for chapter in chapter_grade
                       if chapter['url_name'] == chapter_id)
    except StopIteration:
        raise NotFound(_('Chapter not found'))

    pre_assessment_score = post_assessment_score = None
    pre_assessment_attempted = all_pre_assessment_attempted = all_post_assessment_attempted = False
    for section in chapter['sections']:
        if is_pre_assessment(section):
            pre_assessment_score = section.all_total.earned
            pre_assessment_attempted = bool(section.all_total.first_attempted)
            all_pre_assessment_attempted = is_all_attempted(section)
        elif is_post_assessment(section):
            post_assessment_score = section.all_total.earned
            all_post_assessment_attempted = is_all_attempted(section)

    if pre_assessment_score is None or post_assessment_score is None:
        raise NotFound(_('Pre or post assessment not found'))

    return {
        'pre_assessment_score': student_pre_assessment_score,
        'post_assessment_score': student_post_assessment_score,
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
