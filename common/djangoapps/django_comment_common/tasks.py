from celery import task
from celery_utils.logged_task import LoggedTask
from opaque_keys.edx.keys import CourseKey
from django_comment_common.utils import (
    get_discussion_xblocks_by_course_id, set_course_discussion_settings
)


@task(base=LoggedTask)
def update_discussions_map(context):
    """
    Updates the mapping between discussion_id to discussion block usage key
    for all discussion blocks in the given course.

    context is a dict that contains:
        course_id (string): identifier of the course
    """
    course_key = CourseKey.from_string(context['course_id'])
    discussion_blocks = get_discussion_xblocks_by_course_id(course_key)
    discussions_id_map = {
        discussion_block.discussion_id: unicode(discussion_block.location)
        for discussion_block in discussion_blocks
    }
    set_course_discussion_settings(course_key, discussions_id_map=discussions_id_map)
