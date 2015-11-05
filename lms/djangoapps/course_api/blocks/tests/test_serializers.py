"""
Tests for Course Blocks serializers
"""
from mock import MagicMock

from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import ToyCourseFactory
from lms.djangoapps.course_blocks.api import get_course_blocks, COURSE_BLOCK_ACCESS_TRANSFORMERS

from ..transformers.blocks_api import BlocksAPITransformer
from ..serializers import BlockSerializer, BlockDictSerializer
from .test_utils import deserialize_usage_key


class TestBlockSerializerBase(SharedModuleStoreTestCase):
    """
    Base class for testing BlockSerializer and BlockDictSerializer
    """
    @classmethod
    def setUpClass(cls):
        super(TestBlockSerializerBase, cls).setUpClass()

        cls.course = ToyCourseFactory.create()

    def setUp(self):
        super(TestBlockSerializerBase, self).setUp()

        self.user = UserFactory.create()
        blocks_api_transformer = BlocksAPITransformer(
            block_types_to_count=['video'],
            requested_student_view_data=['video'],
        )
        self.block_structure = get_course_blocks(
            self.user,
            root_block_usage_key=self.course.location,
            transformers=COURSE_BLOCK_ACCESS_TRANSFORMERS + [blocks_api_transformer],
        )
        self.serializer_context = {
            'request': MagicMock(),
            'block_structure': self.block_structure,
            'requested_fields': ['type'],
        }

    def assert_basic_block(self, block_key_string, serialized_block):
        """
        Verifies the given serialized_block when basic fields are requested.
        """
        block_key = deserialize_usage_key(block_key_string, self.course.id)
        self.assertEquals(
            self.block_structure.get_xblock_field(block_key, 'category'),
            serialized_block['type'],
        )
        self.assertEquals(
            set(serialized_block.iterkeys()),
            {'id', 'type', 'lms_web_url', 'student_view_url'},
        )

    def add_additional_requested_fields(self):
        """
        Adds additional fields to the requested_fields context for the serializer.
        """
        self.serializer_context['requested_fields'].extend([
            'children',
            'display_name',
            'graded',
            'format',
            'block_counts',
            'student_view_data',
            'student_view_multi_device',
        ])

    def assert_extended_block(self, serialized_block):
        """
        Verifies the given serialized_block when additional fields are requested.
        """
        self.assertLessEqual(
            {
                'id', 'type', 'lms_web_url', 'student_view_url',
                'display_name', 'graded',
                'block_counts', 'student_view_multi_device',
            },
            set(serialized_block.iterkeys()),
        )

        # video blocks should have student_view_data
        if serialized_block['type'] == 'video':
            self.assertIn('student_view_data', serialized_block)

        # html blocks should have student_view_multi_device set to True
        if serialized_block['type'] == 'html':
            self.assertIn('student_view_multi_device', serialized_block)
            self.assertTrue(serialized_block['student_view_multi_device'])


class TestBlockSerializer(TestBlockSerializerBase):
    """
    Tests the BlockSerializer class, which returns a list of blocks.
    """

    def create_serializer(self):
        """
        creates a BlockSerializer
        """
        return BlockSerializer(
            self.block_structure, many=True, context=self.serializer_context,
        )

    def test_basic(self):
        serializer = self.create_serializer()
        for serialized_block in serializer.data:
            self.assert_basic_block(serialized_block['id'], serialized_block)

    def test_additional_requested_fields(self):
        self.add_additional_requested_fields()
        serializer = self.create_serializer()
        for serialized_block in serializer.data:
            self.assert_extended_block(serialized_block)


class TestBlockDictSerializer(TestBlockSerializerBase):
    """
    Tests the BlockDictSerializer class, which returns a dict of blocks key-ed by its block_key.
    """

    def create_serializer(self):
        """
        creates a BlockDictSerializer
        """
        return BlockDictSerializer(
            self.block_structure, many=False, context=self.serializer_context,
        )

    def test_basic(self):
        serializer = self.create_serializer()

        # verify root
        self.assertEquals(serializer.data['root'], unicode(self.block_structure.root_block_usage_key))

        # verify blocks
        for block_key_string, serialized_block in serializer.data['blocks'].iteritems():
            self.assertEquals(serialized_block['id'], block_key_string)
            self.assert_basic_block(block_key_string, serialized_block)

    def test_additional_requested_fields(self):
        self.add_additional_requested_fields()
        serializer = self.create_serializer()
        for serialized_block in serializer.data['blocks'].itervalues():
            self.assert_extended_block(serialized_block)
