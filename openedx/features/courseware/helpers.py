from logging import getLogger

from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from rest_framework.exceptions import NotFound

from courseware.courses import get_course_with_access
from opaque_keys.edx.keys import CourseKey
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


def get_pre_post_assessments_score(user, course_id, chapter_id):
    """
    Return pre and post assessment score of user in chapter of specified course

    :param user: user
    :param course_id: the identifier for the course.
    :param chapter_id: chapter url_name.
    :return: assessments score dictionary
    :raises:
        NotFound: if chapter, pre or post assessment not found
    """
    course_key = CourseKey.from_string(course_id)
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
    pre_assessment_attempted = False
    for section in chapter['sections']:
        if not section.format:
            continue

        section_format = section.format.lower()
        if section_format == constants.PRE_ASSESSMENT_FORMAT:
            pre_assessment_score = section.all_total.earned
            pre_assessment_attempted = bool(section.all_total.first_attempted)
        elif section_format == constants.POST_ASSESSMENT_FORMAT:
            post_assessment_score = section.all_total.earned

    if pre_assessment_score is None or post_assessment_score is None:
        raise NotFound(_('Pre or post assessment not found'))

    return {
        'pre_assessment_score': pre_assessment_score,
        'post_assessment_score': post_assessment_score,
        'pre_assessment_attempted': pre_assessment_attempted,
    }
