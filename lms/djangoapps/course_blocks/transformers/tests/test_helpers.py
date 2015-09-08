"""
...
"""

from student.tests.factories import CourseEnrollmentFactory, UserFactory
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from courseware.access import has_access

from course_blocks.api import get_course_blocks


class CourseStructureTestCase(ModuleStoreTestCase):
    """
    Helper for test cases that need to build course structures.
    """
    blocks = []

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

    def get_block_key_set(self, *refs):
        """
        Gets the set of usage keys that correspond to the list of
        #ref values as defined on self.blocks.

        Returns: set[UsageKey]
        """
        xblocks = (self.blocks[ref] for ref in refs)
        return set([xblock.location for xblock in xblocks])


class BlockParentsMapTestCase(ModuleStoreTestCase):
    # Tree formed by parent_map:
    #        0
    #     /     \
    #    1       2
    #   / \     / \
    #  3   4   /   5
    #       \ /
    #        6
    # Note the parents must always have lower indices than their children.
    parents_map = [[], [0], [0], [1], [1], [2], [2, 4]]

    # TODO change this to setupClass style
    def setUp(self, **kwargs):
        super(BlockParentsMapTestCase, self).setUp()

        self.course = CourseFactory.create()
        self.xblock_keys = [self.course.location]

        for i, parents_index in enumerate(self.parents_map):
            if i == 0:
                continue  # course already created

            self.xblock_keys.append(
                ItemFactory.create(
                    parent=self.get_block(parents_index[0]),
                    category="vertical",
                ).location
            )

            # add additional parents
            if len(parents_index) > 1:
                for index in range(1, len(parents_index)):
                    parent_index = parents_index[index]
                    parent_block = self.get_block(parent_index)
                    parent_block.children.append(self.xblock_keys[i])
                    self.update_block(parent_block)

        self.password = 'test'
        self.student = UserFactory.create(is_staff=False, password=self.password)
        self.staff = UserFactory.create(is_staff=True, password=self.password)
        CourseEnrollmentFactory.create(is_active=True, mode='honor', user=self.student, course_id=self.course.id)

    def check_transformer_results(
        self, expected_student_accessible_blocks, blocks_with_differing_student_access, transformers=None
    ):
        def check_results(user, expected_accessible_blocks, blocks_with_differing_access):
            self.client.login(username=user.username, password=self.password)
            block_structure = get_course_blocks(
                user, self.course.id, self.course.location, transformers=transformers
            )
            for i, xblock_key in enumerate(self.xblock_keys):
                block_structure_result = block_structure.has_block(xblock_key)
                has_access_result = bool(has_access(user, 'load', self.get_block(i)))

                self.assertEquals(
                    block_structure_result,
                    i in expected_accessible_blocks,
                    "block_structure return value {0} not equal to expected value for block {1}".format(
                        block_structure_result, i
                    )
                )

                if i in blocks_with_differing_access:
                    self.assertNotEqual(
                        block_structure_result,
                        has_access_result,
                        "block structure and has_access results are equal for block {0}".format(i)
                    )
                else:
                    self.assertEquals(
                        block_structure_result,
                        has_access_result,
                        "block structure and has_access results are not equal for block {0}".format(i)
                    )
            self.client.logout()

        check_results(self.student, expected_student_accessible_blocks, blocks_with_differing_student_access)
        check_results(self.staff, {0, 1, 2, 3, 4, 5, 6}, {})

    def get_block(self, i):
        return modulestore().get_item(self.xblock_keys[i])

    def update_block(self, block):
        return modulestore().update_item(block, 'test_user')
