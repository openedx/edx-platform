"""
Asynchronous tasks related to the Course Structure sub-application
"""
import json
import logging

from celery.task import task
from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.django import modulestore


log = logging.getLogger('edx.celery.task')


def _generate_course_structure(course_key):
    """
    Generates a course structure dictionary for the specified course.
    """
    with modulestore().bulk_operations(course_key):
        course = modulestore().get_course(course_key, depth=None)
        blocks_stack = [course]
        blocks_dict = {}
        discussions = {}
        while blocks_stack:
            curr_block = blocks_stack.pop()
            children = curr_block.get_children() if curr_block.has_children else []
            key = unicode(curr_block.scope_ids.usage_id)
            block = {
                "usage_key": key,
                "block_type": curr_block.category,
                "display_name": curr_block.display_name,
                "children": [unicode(child.scope_ids.usage_id) for child in children]
            }

            if (curr_block.category == 'discussion' and
                    hasattr(curr_block, 'discussion_id') and
                    curr_block.discussion_id):
                discussions[curr_block.discussion_id] = unicode(curr_block.scope_ids.usage_id)

            # Retrieve these attributes separately so that we can fail gracefully
            # if the block doesn't have the attribute.
            attrs = (('graded', False), ('format', None))
            for attr, default in attrs:
                if hasattr(curr_block, attr):
                    block[attr] = getattr(curr_block, attr, default)
                else:
                    log.warning('Failed to retrieve %s attribute of block %s. Defaulting to %s.', attr, key, default)
                    block[attr] = default

            blocks_dict[key] = block

            # Add this blocks children to the stack so that we can traverse them as well.
            blocks_stack.extend(children)
        return {
            'structure': {
                "root": unicode(course.scope_ids.usage_id),
                "blocks": blocks_dict
            },
            'discussion_id_map': discussions
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
        structure = _generate_course_structure(course_key)
    except Exception as ex:
        log.exception('An error occurred while generating course structure: %s', ex.message)
        raise

    structure_json = json.dumps(structure['structure'])
    discussion_id_map_json = json.dumps(structure['discussion_id_map'])

    structure_model, created = CourseStructure.objects.get_or_create(
        course_id=course_key,
        defaults={
            'structure_json': structure_json,
            'discussion_id_map_json': discussion_id_map_json
        }
    )

    if not created:
        structure_model.structure_json = structure_json
        structure_model.discussion_id_map_json = discussion_id_map_json
        structure_model.save()
