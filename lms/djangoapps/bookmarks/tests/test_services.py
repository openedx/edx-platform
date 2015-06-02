"""
Tests for bookmark services.
"""

from opaque_keys.edx.keys import UsageKey

from .factories import BookmarkFactory
from ..services import BookmarksService

from student.tests.factories import UserFactory

from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


class BookmarksAPITests(ModuleStoreTestCase):
    """
    Tests the Bookmarks service.
    """

    def setUp(self):
        super(BookmarksAPITests, self).setUp()

        self.user = UserFactory.create(password='test')
        self.other_user = UserFactory.create(password='test')

        self.course = CourseFactory.create(display_name='An Introduction to API Testing')
        self.course_id = unicode(self.course.id)

        self.chapter = ItemFactory.create(
            parent_location=self.course.location, category='chapter', display_name='Week 1'
        )
        self.sequential = ItemFactory.create(
            parent_location=self.chapter.location, category='sequential', display_name='Lesson 1'
        )
        self.vertical = ItemFactory.create(
            parent_location=self.sequential.location, category='vertical', display_name='Subsection 1'
        )
        self.vertical_1 = ItemFactory.create(
            parent_location=self.sequential.location, category='vertical', display_name='Subsection 1.1'
        )
        self.bookmark = BookmarkFactory.create(
            user=self.user,
            course_key=self.course_id,
            usage_key=self.vertical.location,
            display_name=self.vertical.display_name
        )
        self.bookmark_service = BookmarksService(user=self.user)

    def assert_bookmark_response(self, response_data, bookmark):
        """
        Determines if the given response data (dict) matches the specified bookmark.
        """
        self.assertEqual(response_data['id'], '%s,%s' % (self.user.username, unicode(bookmark.usage_key)))
        self.assertEqual(response_data['course_id'], unicode(bookmark.course_key))
        self.assertEqual(response_data['usage_id'], unicode(bookmark.usage_key))
        self.assertEqual(response_data['block_type'], unicode(bookmark.usage_key.block_type))
        self.assertIsNotNone(response_data['created'])

        self.assertEqual(response_data['display_name'], bookmark.display_name)
        self.assertEqual(response_data['path'], bookmark.path)

    def test_get_bookmarks(self):
        """
        Verifies get_bookmarks returns data as expected.
        """

        bookmarks_data = self.bookmark_service.bookmarks(course_key=self.course.id)

        self.assertEqual(len(bookmarks_data), 1)
        self.assert_bookmark_response(bookmarks_data[0], self.bookmark)

    def test_is_bookmarked(self):
        """
        Verifies is_bookmarked returns Bool as expected.
        """
        self.assertTrue(self.bookmark_service.is_bookmarked(usage_key=self.vertical.location))
        self.assertFalse(self.bookmark_service.is_bookmarked(usage_key=self.vertical_1.location))

        # Get bookmark that does not exist.
        bookmark_service = BookmarksService(self.other_user)
        self.assertFalse(bookmark_service.is_bookmarked(usage_key=self.vertical.location))

    def test_set_bookmarked(self):
        """
        Verifies set_bookmarked returns Bool as expected.
        """
        # Assert False for item that does not exist.
        self.assertFalse(
            self.bookmark_service.set_bookmarked(usage_key=UsageKey.from_string("i4x://ed/ed/ed/interactive"))
        )

        self.assertTrue(self.bookmark_service.set_bookmarked(usage_key=self.vertical_1.location))

    def test_unset_bookmarked(self):
        """
        Verifies unset_bookmarked returns Bool as expected.
        """
        self.assertFalse(
            self.bookmark_service.unset_bookmarked(usage_key=UsageKey.from_string("i4x://ed/ed/ed/interactive"))
        )
        self.assertTrue(self.bookmark_service.unset_bookmarked(usage_key=self.vertical.location))
