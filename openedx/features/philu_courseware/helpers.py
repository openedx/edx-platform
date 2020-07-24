from logging import getLogger

from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from opaque_keys import InvalidKeyError
from opaque_keys.edx.django.models import UsageKey
from rest_framework.exceptions import ValidationError

from xmodule.modulestore.django import modulestore

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


def is_pre_assessment(section):
    return get_section_format(section) == constants.PRE_ASSESSMENT_FORMAT


def is_post_assessment(section):
    return get_section_format(section) == constants.POST_ASSESSMENT_FORMAT


def get_section_format(section):
    return section.format.lower() if section and section.format else ''


def validate_problem_id(problem_id):
    """
    Validate if problem_id is valid UsageKey or not
    """
    if not problem_id:
        raise ValidationError(_('Problem id is required'))
    try:
        return UsageKey.from_string(problem_id)
    except InvalidKeyError:
        raise ValidationError(_(constants.INVALID_PROBLEM_ID_MSG))
