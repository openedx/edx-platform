from logging import getLogger

from django.conf import settings
from django.core.urlresolvers import reverse

from xmodule.modulestore.django import modulestore

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
