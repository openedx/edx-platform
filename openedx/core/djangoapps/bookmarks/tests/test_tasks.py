"""
Tests for tasks.
"""
import ddt
from nose.plugins.attrib import attr

from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.factories import check_mongo_calls, ItemFactory

from ..models import XBlockCache
from ..tasks import _calculate_course_xblocks_data, _update_xblocks_cache
from .test_models import BookmarksTestsBase


@attr('shard_2')
@ddt.ddt
class XBlockCacheTaskTests(BookmarksTestsBase):
    """
    Test the XBlockCache model.
    """
    def setUp(self):
        super(XBlockCacheTaskTests, self).setUp()

        self.course_expected_cache_data = {
            self.course.location: [
                [],
            ], self.chapter_1.location: [
                [
                    self.course.location,
                ],
            ], self.chapter_2.location: [
                [
                    self.course.location,
                ],
            ], self.sequential_1.location: [
                [
                    self.course.location,
                    self.chapter_1.location,
                ],
            ], self.sequential_2.location: [
                [
                    self.course.location,
                    self.chapter_1.location,
                ],
            ], self.vertical_1.location: [
                [
                    self.course.location,
                    self.chapter_1.location,
                    self.sequential_1.location,
                ],
            ], self.vertical_2.location: [
                [
                    self.course.location,
                    self.chapter_1.location,
                    self.sequential_2.location,
                ],
            ], self.vertical_3.location: [
                [
                    self.course.location,
                    self.chapter_1.location,
                    self.sequential_2.location,
                ],
            ],
        }

        self.other_course_expected_cache_data = {  # pylint: disable=invalid-name
            self.other_course.location: [
                [],
            ], self.other_chapter_1.location: [
                [
                    self.other_course.location,
                ],
            ], self.other_sequential_1.location: [
                [
                    self.other_course.location,
                    self.other_chapter_1.location,
                ],
            ], self.other_sequential_2.location: [
                [
                    self.other_course.location,
                    self.other_chapter_1.location,
                ],
            ], self.other_vertical_1.location: [
                [
                    self.other_course.location,
                    self.other_chapter_1.location,
                    self.other_sequential_1.location,
                ],
                [
                    self.other_course.location,
                    self.other_chapter_1.location,
                    self.other_sequential_2.location,
                ]
            ], self.other_vertical_2.location: [
                [
                    self.other_course.location,
                    self.other_chapter_1.location,
                    self.other_sequential_1.location,
                ],
            ],
        }

    @ddt.data(
        (ModuleStoreEnum.Type.mongo, 2, 2, 3),
        (ModuleStoreEnum.Type.mongo, 4, 2, 3),
        (ModuleStoreEnum.Type.mongo, 2, 3, 4),
        (ModuleStoreEnum.Type.mongo, 4, 3, 4),
        (ModuleStoreEnum.Type.mongo, 2, 4, 5),
        # (ModuleStoreEnum.Type.mongo, 4, 4, 6), Too slow.
        (ModuleStoreEnum.Type.split, 2, 2, 3),
        (ModuleStoreEnum.Type.split, 4, 2, 3),
        (ModuleStoreEnum.Type.split, 2, 3, 3),
        (ModuleStoreEnum.Type.split, 2, 4, 3),
    )
    @ddt.unpack
    def test_calculate_course_xblocks_data_queries(self, store_type, children_per_block, depth, expected_mongo_calls):

        course = self.create_course_with_blocks(children_per_block, depth, store_type)

        with check_mongo_calls(expected_mongo_calls):
            blocks_data = _calculate_course_xblocks_data(course.id)
            self.assertGreater(len(blocks_data), children_per_block ** depth)

    @ddt.data(
        ('course',),
        ('other_course',)
    )
    @ddt.unpack
    def test_calculate_course_xblocks_data(self, course_attr):
        """
        Test that the xblocks data is calculated correctly.
        """
        course = getattr(self, course_attr)
        blocks_data = _calculate_course_xblocks_data(course.id)

        expected_cache_data = getattr(self, course_attr + '_expected_cache_data')
        for usage_key, __ in expected_cache_data.items():
            for path_index, path in enumerate(blocks_data[unicode(usage_key)]['paths']):
                for path_item_index, path_item in enumerate(path):
                    self.assertEqual(
                        path_item['usage_key'], expected_cache_data[usage_key][path_index][path_item_index]
                    )

    @ddt.data(
        ('course', 47),
        ('other_course', 34)
    )
    @ddt.unpack
    def test_update_xblocks_cache(self, course_attr, expected_sql_queries):
        """
        Test that the xblocks data is persisted correctly.
        """
        course = getattr(self, course_attr)

        with self.assertNumQueries(expected_sql_queries):
            _update_xblocks_cache(course.id)

        expected_cache_data = getattr(self, course_attr + '_expected_cache_data')
        for usage_key, __ in expected_cache_data.items():
            xblock_cache = XBlockCache.objects.get(usage_key=usage_key)
            for path_index, path in enumerate(xblock_cache.paths):
                for path_item_index, path_item in enumerate(path):
                    self.assertEqual(
                        path_item.usage_key, expected_cache_data[usage_key][path_index][path_item_index + 1]
                    )

        with self.assertNumQueries(3):
            _update_xblocks_cache(course.id)

    def test_update_xblocks_cache_with_display_name_none(self):
        """
        Test that the xblocks data is persisted correctly with display_name=None.
        """
        block_with_display_name_none = ItemFactory.create(
            parent_location=self.sequential_2.location,
            category='vertical', display_name=None
        )

        _update_xblocks_cache(self.course.id)

        self.course_expected_cache_data.update(
            {
                block_with_display_name_none.location: [
                    [
                        self.course.location,
                        self.chapter_1.location,
                        self.sequential_2.location,
                    ]
                ]
            }
        )

        for usage_key, __ in self.course_expected_cache_data.items():
            xblock_cache = XBlockCache.objects.get(usage_key=usage_key)
            for path_index, path in enumerate(xblock_cache.paths):
                for path_item_index, path_item in enumerate(path):
                    self.assertEqual(
                        path_item.usage_key,
                        self.course_expected_cache_data[usage_key][path_index][path_item_index + 1]
                    )
