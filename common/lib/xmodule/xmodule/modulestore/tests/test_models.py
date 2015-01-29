from unittest import TestCase

from xmodule.modulestore.models import Block, CourseStructure


BLOCK_DATA = {
    'id': 'i4x://edx/DemoX/1234',
    'block_type': 'sequential',
    'display_name': 'Some Block',
    'format': 'Exam',
    'graded': True,
    'children': ['i4x://edx/DemoX/abcd']
}


class BlockTests(TestCase):
    def test_init(self):
        """
        Verify that the constructor instantiates a Block object with the correct attributes.
        """
        data = BLOCK_DATA
        _id = data['id']
        _type = data['block_type']

        # Test the default parameters
        block = Block(_id, _type)
        self.assertEqual(block.id, _id)
        self.assertEqual(block.type, _type)
        self.assertIsNone(block.display_name)
        self.assertIsNone(block.format)
        self.assertFalse(block.graded)
        self.assertListEqual(block.children, [])

        # Test that values are copied to the model
        display_name = data['display_name']
        _format = data['format']
        graded = data['graded']
        children = data['children']

        block = Block(_id, _type, display_name, _format, graded, children)
        self.assertEqual(block.id, _id)
        self.assertEqual(block.type, _type)
        self.assertEqual(block.display_name, display_name)
        self.assertEqual(block.format, _format)
        self.assertEqual(block.graded, graded)
        self.assertListEqual(block.children, children)

    def test_equality(self):
        """
        Verify the eq and neq methods behave as expected.
        """
        data = BLOCK_DATA
        block = Block.from_dict(data)

        self.assertNotEqual(block, None)
        self.assertNotEqual(block, Block('abc', '123'))

        other = Block(data['id'], data['block_type'], data['display_name'], data['format'], data['graded'],
                      data['children'])
        self.assertEqual(block, block)
        self.assertEqual(block, other)

    def test_from_dict(self):
        """
        Verify that the method properly converts a dictionary to a Block object.
        """
        data = BLOCK_DATA
        block = Block.from_dict(data)

        self.assertEqual(block.id, data['id'])
        self.assertEqual(block.type, data['block_type'])
        self.assertEqual(block.display_name, data['display_name'])
        self.assertEqual(block.format, data['format'])
        self.assertEqual(block.graded, data['graded'])
        self.assertListEqual(block.children, data['children'])

    def test_unicode(self):
        data = BLOCK_DATA
        block = Block.from_dict(data)
        self.assertEqual(unicode(block), block.display_name)


class CourseStructureTests(TestCase):
    def test_init(self):
        """
        Verify that the constructor instantiates a CourseStructure object with the correct attributes.
        """
        root = BLOCK_DATA['id']
        blocks = {
            root: Block.from_dict(BLOCK_DATA)
        }

        cs = CourseStructure(root, blocks)

        self.assertEqual(cs.root, root)
        self.assertEqual(cs.blocks, blocks)
        self.assertIsNone(cs.version)

        version = 'abcd'
        cs = CourseStructure(root, blocks, version=version)
        self.assertEqual(cs.version, version)

    def test_equality(self):
        """
        Verify the eq and neq methods behave as expected.
        """
        root = BLOCK_DATA['id']
        blocks = {
            root: Block.from_dict(BLOCK_DATA)
        }
        cs = CourseStructure(root, blocks)

        self.assertNotEqual(cs, None)
        self.assertNotEqual(cs, Block('abc', '123'))
        self.assertNotEqual(cs, CourseStructure('abc', {}))

        self.assertEqual(cs, cs)
        self.assertEqual(cs, CourseStructure(root, blocks))

    def test_from_dict(self):
        """
        Verify that the method properly converts a dictionary to a CourseStructure object.
        """
        root = BLOCK_DATA['id']
        data = {
            'root': root,
            'blocks': {
                root: BLOCK_DATA
            }
        }
        cs = CourseStructure.from_dict(data)

        self.assertEqual(cs.root, root)
        blocks = {root: Block.from_dict(BLOCK_DATA)}
        self.assertDictEqual(cs.blocks, blocks)
