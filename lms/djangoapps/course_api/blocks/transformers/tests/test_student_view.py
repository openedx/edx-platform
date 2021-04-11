"""
Tests for StudentViewTransformer.
"""


import ddt

# pylint: disable=protected-access
from openedx.core.djangoapps.content.block_structure.factory import BlockStructureFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import ToyCourseFactory

from ..student_view import StudentViewTransformer


@ddt.ddt
class TestStudentViewTransformer(ModuleStoreTestCase):
    """
    Test proper behavior for StudentViewTransformer
    """

    def setUp(self):
        super(TestStudentViewTransformer, self).setUp()
        self.course_key = ToyCourseFactory.create().id
        self.course_usage_key = self.store.make_course_usage_key(self.course_key)
        self.block_structure = BlockStructureFactory.create_from_modulestore(self.course_usage_key, self.store)

    @ddt.data(
        'video', 'html', ['video', 'html'], [],
    )
    def test_transform(self, requested_student_view_data):
        # collect phase
        StudentViewTransformer.collect(self.block_structure)
        self.block_structure._collect_requested_xblock_fields()

        # transform phase
        StudentViewTransformer(requested_student_view_data).transform(
            usage_info=None,
            block_structure=self.block_structure,
        )

        # verify video data returned iff requested
        video_block_key = self.course_key.make_usage_key('video', 'sample_video')
        self.assertEqual(
            self.block_structure.get_transformer_block_field(
                video_block_key, StudentViewTransformer, StudentViewTransformer.STUDENT_VIEW_DATA,
            ) is not None,
            'video' in requested_student_view_data
        )
        self.assertFalse(
            self.block_structure.get_transformer_block_field(
                video_block_key, StudentViewTransformer, StudentViewTransformer.STUDENT_VIEW_MULTI_DEVICE,
            )
        )

        # verify html data returned iff requested
        html_block_key = self.course_key.make_usage_key('html', 'toyhtml')
        self.assertEqual(
            self.block_structure.get_transformer_block_field(
                html_block_key, StudentViewTransformer, StudentViewTransformer.STUDENT_VIEW_DATA,
            ) is not None,
            'html' in requested_student_view_data
        )
        self.assertTrue(
            self.block_structure.get_transformer_block_field(
                html_block_key, StudentViewTransformer, StudentViewTransformer.STUDENT_VIEW_MULTI_DEVICE,
            )
        )
