"""
Tests for StudentViewTransformer.
"""

# pylint: disable=protected-access

from openedx.core.lib.block_cache.block_structure_factory import BlockStructureFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import ToyCourseFactory

from ..student_view import StudentViewTransformer


class TestStudentViewTransformer(ModuleStoreTestCase):
    """
    Test proper behavior for StudentViewTransformer
    """
    def setUp(self):
        super(TestStudentViewTransformer, self).setUp()
        self.course_key = ToyCourseFactory.create().id
        self.course_usage_key = self.store.make_course_usage_key(self.course_key)
        self.block_structure = BlockStructureFactory.create_from_modulestore(self.course_usage_key, self.store)

    def test_transform(self):
        # collect phase
        StudentViewTransformer.collect(self.block_structure)
        self.block_structure._collect_requested_xblock_fields()

        # transform phase
        StudentViewTransformer('video').transform(usage_info=None, block_structure=self.block_structure)

        # verify video data
        video_block_key = self.course_key.make_usage_key('video', 'sample_video')
        self.assertIsNotNone(
            self.block_structure.get_transformer_block_field(
                video_block_key, StudentViewTransformer, StudentViewTransformer.STUDENT_VIEW_DATA,
            )
        )
        self.assertFalse(
            self.block_structure.get_transformer_block_field(
                video_block_key, StudentViewTransformer, StudentViewTransformer.STUDENT_VIEW_MULTI_DEVICE,
            )
        )

        # verify html data
        html_block_key = self.course_key.make_usage_key('html', 'toyhtml')
        self.assertIsNone(
            self.block_structure.get_transformer_block_field(
                html_block_key, StudentViewTransformer, StudentViewTransformer.STUDENT_VIEW_DATA,
            )
        )
        self.assertTrue(
            self.block_structure.get_transformer_block_field(
                html_block_key, StudentViewTransformer, StudentViewTransformer.STUDENT_VIEW_MULTI_DEVICE,
            )
        )
