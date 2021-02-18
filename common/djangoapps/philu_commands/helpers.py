from logging import getLogger
from xmodule.modulestore.django import modulestore

log = getLogger(__name__)


def generate_course_structure(course_key):
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

            if curr_block.category == 'discussion' and getattr(curr_block, 'discussion_id', None):
                discussions[curr_block.discussion_id] = unicode(curr_block.scope_ids.usage_id)

            # Retrieve these attributes separately so that we can fail gracefully
            # if the block doesn't have the attribute.
            attrs = (('graded', False), ('format', None))
            for attr, default in attrs:
                if hasattr(curr_block, attr):
                    block[attr] = getattr(curr_block, attr, default)
                else:
                    log.warning('Failed to retrieve %s attribute of block %s. Defaulting to %s.', attr, key,
                                default)
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


def has_active_certificate(course):
    has_activated_certificate = False
    certificates = course.certificates

    if certificates:
        has_activated_certificate = any([certificate['is_active'] for certificate in certificates['certificates']])

    return has_activated_certificate
