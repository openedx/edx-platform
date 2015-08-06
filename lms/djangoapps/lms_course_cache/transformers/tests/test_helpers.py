"""
...
"""

from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

class CourseStructureTestCase(ModuleStoreTestCase):
    """
    Helper for test cases that need to build course structures.
    """

    def build_course(self, course_hierarchy):
        """
        Build a hierarchy of XBlocks.

        Arguments:
            course_hierarchy (BlockStructureDict): Definition of course hierarchy.

            where a BlockStructureDict is a dict in the form {
                'key1': 'value1',
                ...
                'keyN': 'valueN',
                '#type': block_type,
                '#ref': short_string_for_referencing_block,
                '#children': list[BlockStructureDict]
            }

            Special keys start with '#'; the rest just get passed as kwargs to
            Factory.create.

        Returns:
            dict[str: XBlock]: Mapping from '#ref' values to their XBlocks.
        """
        block_map = {}

        def build_xblock(block_hierarchy, parent):
            """
            Build an XBlock, add it to result_dict, and call build_xblock on the
            children defined in block_dict.

            Arguments:
                block_hierarchy (BlockStructureDict): Definition of hierarchy,
                    from this block down.
                is_root (bool): Whether this is the course's root XBlock.
            """
            block_type = block_hierarchy['#type']
            block_ref = block_hierarchy['#ref']
            factory = (CourseFactory if block_type == 'course' else ItemFactory)
            kwargs = {key: value for key, value in block_hierarchy.iteritems() if key[0] != '#'}

            if block_type != 'course':
                kwargs['category'] = block_type
            if parent:
                kwargs['parent'] = parent

            xblock = factory.create(
                display_name='{} {}'.format(block_type, block_ref),
                publish_item=True,
                **kwargs
            )
            block_map[block_ref] = xblock

            for child_hierarchy in block_hierarchy.get('#children', []):
                build_xblock(child_hierarchy, xblock)

        if '#type' not in course_hierarchy:
            course_hierarchy['#type'] = 'course'
        build_xblock(course_hierarchy, None)

        return block_map


