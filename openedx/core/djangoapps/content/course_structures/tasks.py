import json
import logging

from celery.task import task
from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.django import modulestore


log = logging.getLogger(__name__)


def generate_course_structure(course_key):
    """
    Generates a course structure dictionary for the specified course.
    """
    course = modulestore().get_course(course_key, depth=None)
    blocks_stack = [course]
    blocks_dict = {}
    while blocks_stack:
        curr_block = blocks_stack.pop()
        children = curr_block.get_children() if curr_block.has_children else []
        blocks_dict[unicode(curr_block.scope_ids.usage_id)] = {
            "usage_key": unicode(curr_block.scope_ids.usage_id),
            "block_type": curr_block.category,
            "display_name": curr_block.display_name,
            "graded": curr_block.graded,
            "format": curr_block.format,
            "children": [unicode(child.scope_ids.usage_id) for child in children]
        }
        blocks_stack.extend(children)
    return {
        "root": unicode(course.scope_ids.usage_id),
        "blocks": blocks_dict
    }


@task(name=u'openedx.core.djangoapps.content.course_structures.tasks.update_course_structure')
def update_course_structure(course_key):
    """
    Regenerates and updates the course structure (in the database) for the specified course.
    """
    # Import here to avoid circular import.
    from .models import CourseStructure

    # Ideally we'd like to accept a CourseLocator; however, CourseLocator is not JSON-serializable (by default) so
    # Celery's delayed tasks fail to start. For this reason, callers should pass the course key as a Unicode string.
    if not isinstance(course_key, basestring):
        raise ValueError('course_key must be a string. {} is not acceptable.'.format(type(course_key)))

    course_key = CourseKey.from_string(course_key)

    try:
        structure = generate_course_structure(course_key)
    except Exception as ex:
        log.exception('An error occurred while generating course structure: %s', ex.message)
        raise

    structure_json = json.dumps(structure)

    cs, created = CourseStructure.objects.get_or_create(
        course_id=course_key,
        defaults={'structure_json': structure_json}
    )

    if not created:
        cs.structure_json = structure_json
        cs.save()
