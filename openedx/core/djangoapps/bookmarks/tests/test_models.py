"""
Tests for Bookmarks models.
"""
from contextlib import contextmanager
import datetime
import ddt
from freezegun import freeze_time
import mock
from nose.plugins.attrib import attr
import pytz

from opaque_keys.edx.keys import UsageKey
from opaque_keys.edx.locator import CourseLocator, BlockUsageLocator
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.factories import check_mongo_calls, CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from openedx.core.djangolib.testing.utils import skip_unless_lms
from student.tests.factories import AdminFactory, UserFactory

from .. import DEFAULT_FIELDS, OPTIONAL_FIELDS, PathItem
from ..models import Bookmark, XBlockCache, parse_path_data
from .factories import BookmarkFactory

EXAMPLE_USAGE_KEY_1 = u'i4x://org.15/course_15/chapter/Week_1'
EXAMPLE_USAGE_KEY_2 = u'i4x://org.15/course_15/chapter/Week_2'


noop_contextmanager = contextmanager(lambda x: (yield))  # pylint: disable=invalid-name


class BookmarksTestsBase(ModuleStoreTestCase):
    """
    Test the Bookmark model.
    """
    ALL_FIELDS = DEFAULT_FIELDS + OPTIONAL_FIELDS
    STORE_TYPE = ModuleStoreEnum.Type.mongo
    TEST_PASSWORD = 'test'

    ENABLED_CACHES = ['default', 'mongo_metadata_inheritance', 'loc_cache']

    def setUp(self):
        super(BookmarksTestsBase, self).setUp()

        self.admin = AdminFactory()
        self.user = UserFactory.create(password=self.TEST_PASSWORD)
        self.other_user = UserFactory.create(password=self.TEST_PASSWORD)
        self.setup_data(self.STORE_TYPE)

    def setup_data(self, store_type=ModuleStoreEnum.Type.mongo):
        """ Create courses and add some test blocks. """

        with self.store.default_store(store_type):

            self.course = CourseFactory.create(display_name='An Introduction to API Testing')
            self.course_id = unicode(self.course.id)

            with self.store.bulk_operations(self.course.id):

                self.chapter_1 = ItemFactory.create(
                    parent_location=self.course.location, category='chapter', display_name='Week 1'
                )
                self.chapter_2 = ItemFactory.create(
                    parent_location=self.course.location, category='chapter', display_name='Week 2'
                )

                self.sequential_1 = ItemFactory.create(
                    parent_location=self.chapter_1.location, category='sequential', display_name='Lesson 1'
                )
                self.sequential_2 = ItemFactory.create(
                    parent_location=self.chapter_1.location, category='sequential', display_name='Lesson 2'
                )

                self.vertical_1 = ItemFactory.create(
                    parent_location=self.sequential_1.location, category='vertical', display_name='Subsection 1'
                )
                self.vertical_2 = ItemFactory.create(
                    parent_location=self.sequential_2.location, category='vertical', display_name='Subsection 2'
                )
                self.vertical_3 = ItemFactory.create(
                    parent_location=self.sequential_2.location, category='vertical', display_name='Subsection 3'
                )

                self.html_1 = ItemFactory.create(
                    parent_location=self.vertical_2.location, category='html', display_name='Details 1'
                )

        self.path = [
            PathItem(self.chapter_1.location, self.chapter_1.display_name),
            PathItem(self.sequential_2.location, self.sequential_2.display_name),
        ]

        self.bookmark_1 = BookmarkFactory.create(
            user=self.user,
            course_key=self.course_id,
            usage_key=self.sequential_1.location,
            xblock_cache=XBlockCache.create({
                'display_name': self.sequential_1.display_name,
                'usage_key': self.sequential_1.location,
            }),
        )
        self.bookmark_2 = BookmarkFactory.create(
            user=self.user,
            course_key=self.course_id,
            usage_key=self.sequential_2.location,
            xblock_cache=XBlockCache.create({
                'display_name': self.sequential_2.display_name,
                'usage_key': self.sequential_2.location,
            }),
        )

        self.other_course = CourseFactory.create(display_name='An Introduction to API Testing 2')

        with self.store.bulk_operations(self.other_course.id):

            self.other_chapter_1 = ItemFactory.create(
                parent_location=self.other_course.location, category='chapter', display_name='Other Week 1'
            )
            self.other_sequential_1 = ItemFactory.create(
                parent_location=self.other_chapter_1.location, category='sequential', display_name='Other Lesson 1'
            )
            self.other_sequential_2 = ItemFactory.create(
                parent_location=self.other_chapter_1.location, category='sequential', display_name='Other Lesson 2'
            )
            self.other_vertical_1 = ItemFactory.create(
                parent_location=self.other_sequential_1.location, category='vertical', display_name='Other Subsection 1'
            )
            self.other_vertical_2 = ItemFactory.create(
                parent_location=self.other_sequential_1.location, category='vertical', display_name='Other Subsection 2'
            )

            # self.other_vertical_1 has two parents
            self.other_sequential_2.children.append(self.other_vertical_1.location)
            modulestore().update_item(self.other_sequential_2, self.admin.id)  # pylint: disable=no-member

        self.other_bookmark_1 = BookmarkFactory.create(
            user=self.user,
            course_key=unicode(self.other_course.id),
            usage_key=self.other_vertical_1.location,
            xblock_cache=XBlockCache.create({
                'display_name': self.other_vertical_1.display_name,
                'usage_key': self.other_vertical_1.location,
            }),
        )

    def create_course_with_blocks(self, children_per_block=1, depth=1, store_type=ModuleStoreEnum.Type.mongo):
        """
        Create a course and add blocks.
        """
        with self.store.default_store(store_type):

            course = CourseFactory.create()
            display_name = 0

            with self.store.bulk_operations(course.id):
                blocks_at_next_level = [course]

                for __ in range(depth):
                    blocks_at_current_level = blocks_at_next_level
                    blocks_at_next_level = []

                    for block in blocks_at_current_level:
                        for __ in range(children_per_block):
                            blocks_at_next_level += [ItemFactory.create(
                                parent_location=block.scope_ids.usage_id, display_name=unicode(display_name)
                            )]
                            display_name += 1

        return course

    def create_course_with_bookmarks_count(self, count, store_type=ModuleStoreEnum.Type.mongo):
        """
        Create a course, add some content and add bookmarks.
        """
        with self.store.default_store(store_type):

            course = CourseFactory.create()

            with self.store.bulk_operations(course.id):
                blocks = [ItemFactory.create(
                    parent_location=course.location, category='chapter', display_name=unicode(index)
                ) for index in range(count)]

            bookmarks = [BookmarkFactory.create(
                user=self.user,
                course_key=course.id,
                usage_key=block.location,
                xblock_cache=XBlockCache.create({
                    'display_name': block.display_name,
                    'usage_key': block.location,
                }),
            ) for block in blocks]

        return course, blocks, bookmarks

    def assert_bookmark_model_is_valid(self, bookmark, bookmark_data):
        """
        Assert that the attributes of the bookmark model were set correctly.
        """
        self.assertEqual(bookmark.user, bookmark_data['user'])
        self.assertEqual(bookmark.course_key, bookmark_data['course_key'])
        self.assertEqual(unicode(bookmark.usage_key), unicode(bookmark_data['usage_key']))
        self.assertEqual(bookmark.resource_id, u"{},{}".format(bookmark_data['user'], bookmark_data['usage_key']))
        self.assertEqual(bookmark.display_name, bookmark_data['display_name'])
        self.assertEqual(bookmark.path, self.path)
        self.assertIsNotNone(bookmark.created)

        self.assertEqual(bookmark.xblock_cache.course_key, bookmark_data['course_key'])
        self.assertEqual(bookmark.xblock_cache.display_name, bookmark_data['display_name'])

    def assert_bookmark_data_is_valid(self, bookmark, bookmark_data, check_optional_fields=False):
        """
        Assert that the bookmark data matches the data in the model.
        """
        self.assertEqual(bookmark_data['id'], bookmark.resource_id)
        self.assertEqual(bookmark_data['course_id'], unicode(bookmark.course_key))
        self.assertEqual(bookmark_data['usage_id'], unicode(bookmark.usage_key))
        self.assertEqual(bookmark_data['block_type'], unicode(bookmark.usage_key.block_type))
        self.assertIsNotNone(bookmark_data['created'])

        if check_optional_fields:
            self.assertEqual(bookmark_data['display_name'], bookmark.display_name)
            self.assertEqual(bookmark_data['path'], bookmark.path)


@attr(shard=2)
@ddt.ddt
@skip_unless_lms
class BookmarkModelTests(BookmarksTestsBase):
    """
    Test the Bookmark model.
    """
    def setUp(self):
        super(BookmarkModelTests, self).setUp()

        self.vertical_4 = ItemFactory.create(
            parent_location=self.sequential_2.location,
            category='vertical',
            display_name=None
        )

    def get_bookmark_data(self, block, user=None):
        """
        Returns bookmark data for testing.
        """
        return {
            'user': user or self.user,
            'usage_key': block.location,
            'course_key': block.location.course_key,
            'display_name': block.display_name,
        }

    @ddt.data(
        (ModuleStoreEnum.Type.mongo, 'course', [], 3),
        (ModuleStoreEnum.Type.mongo, 'chapter_1', [], 4),
        (ModuleStoreEnum.Type.mongo, 'sequential_1', ['chapter_1'], 6),
        (ModuleStoreEnum.Type.mongo, 'vertical_1', ['chapter_1', 'sequential_1'], 8),
        (ModuleStoreEnum.Type.mongo, 'html_1', ['chapter_1', 'sequential_2', 'vertical_2'], 10),
        (ModuleStoreEnum.Type.split, 'course', [], 3),
        (ModuleStoreEnum.Type.split, 'chapter_1', [], 2),
        (ModuleStoreEnum.Type.split, 'sequential_1', ['chapter_1'], 2),
        (ModuleStoreEnum.Type.split, 'vertical_1', ['chapter_1', 'sequential_1'], 2),
        (ModuleStoreEnum.Type.split, 'html_1', ['chapter_1', 'sequential_2', 'vertical_2'], 2),
    )
    @ddt.unpack
    def test_path_and_queries_on_create(self, store_type, block_to_bookmark, ancestors_attrs, expected_mongo_calls):
        """
        In case of mongo, 1 query is used to fetch the block, and 2
        by path_to_location(), and then 1 query per parent in path
        is needed to fetch the parent blocks.
        """

        self.setup_data(store_type)
        user = UserFactory.create()

        expected_path = [PathItem(
            usage_key=getattr(self, ancestor_attr).location, display_name=getattr(self, ancestor_attr).display_name
        ) for ancestor_attr in ancestors_attrs]

        bookmark_data = self.get_bookmark_data(getattr(self, block_to_bookmark), user=user)

        with check_mongo_calls(expected_mongo_calls):
            bookmark, __ = Bookmark.create(bookmark_data)

        self.assertEqual(bookmark.path, expected_path)
        self.assertIsNotNone(bookmark.xblock_cache)
        self.assertEqual(bookmark.xblock_cache.paths, [])

    def test_create_bookmark_success(self):
        """
        Tests creation of bookmark.
        """
        bookmark_data = self.get_bookmark_data(self.vertical_2)
        bookmark, __ = Bookmark.create(bookmark_data)
        self.assert_bookmark_model_is_valid(bookmark, bookmark_data)

        bookmark_data_different_values = self.get_bookmark_data(self.vertical_2)
        bookmark_data_different_values['display_name'] = 'Introduction Video'
        bookmark2, __ = Bookmark.create(bookmark_data_different_values)
        # The bookmark object already created should have been returned without modifications.
        self.assertEqual(bookmark, bookmark2)
        self.assertEqual(bookmark.xblock_cache, bookmark2.xblock_cache)
        self.assert_bookmark_model_is_valid(bookmark2, bookmark_data)

        bookmark_data_different_user = self.get_bookmark_data(self.vertical_2)
        bookmark_data_different_user['user'] = UserFactory.create()
        bookmark3, __ = Bookmark.create(bookmark_data_different_user)
        self.assertNotEqual(bookmark, bookmark3)
        self.assert_bookmark_model_is_valid(bookmark3, bookmark_data_different_user)

    def test_create_bookmark_successfully_with_display_name_none(self):
        """
        Tests creation of bookmark with display_name None.
        """
        bookmark_data = self.get_bookmark_data(self.vertical_4)
        bookmark, __ = Bookmark.create(bookmark_data)
        bookmark_data['display_name'] = self.vertical_4.display_name_with_default
        self.assert_bookmark_model_is_valid(bookmark, bookmark_data)

    @ddt.data(
        (-30, [[PathItem(EXAMPLE_USAGE_KEY_1, '1')]], 1),
        (30, None, 2),
        (30, [], 2),
        (30, [[PathItem(EXAMPLE_USAGE_KEY_1, '1')]], 1),
        (30, [[PathItem(EXAMPLE_USAGE_KEY_1, '1')], [PathItem(EXAMPLE_USAGE_KEY_2, '2')]], 2),
    )
    @ddt.unpack
    @mock.patch('openedx.core.djangoapps.bookmarks.models.Bookmark.get_path')
    def test_path(self, seconds_delta, paths, get_path_call_count, mock_get_path):

        block_path = [PathItem(UsageKey.from_string(EXAMPLE_USAGE_KEY_1), '1')]
        mock_get_path.return_value = block_path

        html = ItemFactory.create(
            parent_location=self.other_chapter_1.location, category='html', display_name='Other Lesson 1'
        )

        bookmark_data = self.get_bookmark_data(html)
        bookmark, __ = Bookmark.create(bookmark_data)
        self.assertIsNotNone(bookmark.xblock_cache)

        modification_datetime = datetime.datetime.now(pytz.utc) + datetime.timedelta(seconds=seconds_delta)
        with freeze_time(modification_datetime):
            bookmark.xblock_cache.paths = paths
            bookmark.xblock_cache.save()

        self.assertEqual(bookmark.path, block_path)
        self.assertEqual(mock_get_path.call_count, get_path_call_count)

    @ddt.data(
        (ModuleStoreEnum.Type.mongo, 2, 2, 2),
        (ModuleStoreEnum.Type.mongo, 4, 2, 2),
        (ModuleStoreEnum.Type.mongo, 6, 2, 2),
        (ModuleStoreEnum.Type.mongo, 2, 3, 3),
        (ModuleStoreEnum.Type.mongo, 4, 3, 3),
        # (ModuleStoreEnum.Type.mongo, 6, 3, 3), Too slow.
        (ModuleStoreEnum.Type.mongo, 2, 4, 4),
        # (ModuleStoreEnum.Type.mongo, 4, 4, 4),
        (ModuleStoreEnum.Type.split, 2, 2, 2),
        (ModuleStoreEnum.Type.split, 4, 2, 2),
        (ModuleStoreEnum.Type.split, 2, 3, 2),
        # (ModuleStoreEnum.Type.split, 4, 3, 2),
        (ModuleStoreEnum.Type.split, 2, 4, 2),
    )
    @ddt.unpack
    def test_get_path_queries(self, store_type, children_per_block, depth, expected_mongo_calls):
        """
        In case of mongo, 2 queries are used by path_to_location(), and then
        1 query per parent in path is needed to fetch the parent blocks.
        """

        course = self.create_course_with_blocks(children_per_block, depth, store_type)

        # Find a leaf block.
        block = modulestore().get_course(course.id, depth=None)
        for __ in range(depth - 1):
            children = block.get_children()
            block = children[-1]

        with check_mongo_calls(expected_mongo_calls):
            path = Bookmark.get_path(block.location)
            self.assertEqual(len(path), depth - 2)

    def test_get_path_in_case_of_exceptions(self):

        user = UserFactory.create()

        # Block does not exist
        usage_key = UsageKey.from_string('i4x://edX/apis/html/interactive')
        usage_key.replace(course_key=self.course.id)
        self.assertEqual(Bookmark.get_path(usage_key), [])

        # Block is an orphan
        self.other_sequential_1.children = []
        modulestore().update_item(self.other_sequential_1, self.admin.id)  # pylint: disable=no-member

        bookmark_data = self.get_bookmark_data(self.other_vertical_2, user=user)
        bookmark, __ = Bookmark.create(bookmark_data)

        self.assertEqual(bookmark.path, [])
        self.assertIsNotNone(bookmark.xblock_cache)
        self.assertEqual(bookmark.xblock_cache.paths, [])

        # Parent block could not be retrieved
        with mock.patch('openedx.core.djangoapps.bookmarks.models.search.path_to_location') as mock_path_to_location:
            mock_path_to_location.return_value = [usage_key]
            bookmark_data = self.get_bookmark_data(self.other_sequential_1, user=user)
            bookmark, __ = Bookmark.create(bookmark_data)
            self.assertEqual(bookmark.path, [])


@attr(shard=2)
@ddt.ddt
class XBlockCacheModelTest(ModuleStoreTestCase):
    """
    Test the XBlockCache model.
    """

    COURSE_KEY = CourseLocator(org='test', course='test', run='test')
    CHAPTER1_USAGE_KEY = BlockUsageLocator(COURSE_KEY, block_type='chapter', block_id='chapter1')
    SECTION1_USAGE_KEY = BlockUsageLocator(COURSE_KEY, block_type='section', block_id='section1')
    SECTION2_USAGE_KEY = BlockUsageLocator(COURSE_KEY, block_type='section', block_id='section1')
    VERTICAL1_USAGE_KEY = BlockUsageLocator(COURSE_KEY, block_type='vertical', block_id='sequential1')
    PATH1 = [
        [unicode(CHAPTER1_USAGE_KEY), 'Chapter 1'],
        [unicode(SECTION1_USAGE_KEY), 'Section 1'],
    ]
    PATH2 = [
        [unicode(CHAPTER1_USAGE_KEY), 'Chapter 1'],
        [unicode(SECTION2_USAGE_KEY), 'Section 2'],
    ]

    def setUp(self):
        super(XBlockCacheModelTest, self).setUp()

    def assert_xblock_cache_data(self, xblock_cache, data):
        """
        Assert that the XBlockCache object values match.
        """
        self.assertEqual(xblock_cache.usage_key, data['usage_key'])
        self.assertEqual(xblock_cache.course_key, data['usage_key'].course_key)
        self.assertEqual(xblock_cache.display_name, data['display_name'])
        self.assertEqual(xblock_cache._paths, data['_paths'])  # pylint: disable=protected-access
        self.assertEqual(xblock_cache.paths, [parse_path_data(path) for path in data['_paths']])

    @ddt.data(
        (
            [
                {'usage_key': VERTICAL1_USAGE_KEY, },
                {'display_name': '', '_paths': [], },
            ],
            [
                {'usage_key': VERTICAL1_USAGE_KEY, 'display_name': 'Vertical 5', '_paths': [PATH2]},
                {'_paths': []},
            ],
        ),
        (
            [
                {'usage_key': VERTICAL1_USAGE_KEY, 'display_name': 'Vertical 4', '_paths': [PATH1]},
                {},
            ],
            [
                {'usage_key': VERTICAL1_USAGE_KEY, 'display_name': 'Vertical 5', '_paths': [PATH2]},
                {'_paths': [PATH1]},
            ],
        ),
    )
    def test_create(self, data):
        """
        Test XBlockCache.create() constructs and updates objects correctly.
        """
        for create_data, additional_data_to_expect in data:
            xblock_cache = XBlockCache.create(create_data)
            create_data.update(additional_data_to_expect)
            self.assert_xblock_cache_data(xblock_cache, create_data)

    @ddt.data(
        ([], [PATH1]),
        ([PATH1, PATH2], [PATH1]),
        ([PATH1], []),
    )
    @ddt.unpack
    def test_paths(self, original_paths, updated_paths):
        xblock_cache = XBlockCache.create({
            'usage_key': self.VERTICAL1_USAGE_KEY,
            'display_name': 'The end.',
            '_paths': original_paths,
        })
        self.assertEqual(xblock_cache.paths, [parse_path_data(path) for path in original_paths])

        xblock_cache.paths = [parse_path_data(path) for path in updated_paths]
        xblock_cache.save()

        xblock_cache = XBlockCache.objects.get(id=xblock_cache.id)
        self.assertEqual(xblock_cache._paths, updated_paths)  # pylint: disable=protected-access
        self.assertEqual(xblock_cache.paths, [parse_path_data(path) for path in updated_paths])
