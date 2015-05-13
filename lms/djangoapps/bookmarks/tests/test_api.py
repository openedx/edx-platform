"""
Tests for bookmarks api.
"""

from django.core.exceptions import ObjectDoesNotExist

from opaque_keys.edx.keys import UsageKey

from student.tests.factories import UserFactory

from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from .factories import BookmarkFactory
from .. import api, DEFAULT_FIELDS, OPTIONAL_FIELDS
from ..models import Bookmark


class BookmarksAPITests(ModuleStoreTestCase):
    """
    These tests cover the parts of the API methods.
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

        self.course_2 = CourseFactory.create(display_name='An Introduction to API Testing 2')
        self.chapter_2 = ItemFactory.create(
            parent_location=self.course_2.location, category='chapter', display_name='Week 2'
        )
        self.sequential_2 = ItemFactory.create(
            parent_location=self.chapter_2.location, category='sequential', display_name='Lesson 2'
        )
        self.vertical_2 = ItemFactory.create(
            parent_location=self.sequential_2.location, category='vertical', display_name='Subsection 2'
        )
        self.bookmark_2 = BookmarkFactory.create(
            user=self.user,
            course_key=self.course_2.id,
            usage_key=self.vertical_2.location,
            display_name=self.vertical_2.display_name
        )
        self.all_fields = DEFAULT_FIELDS + OPTIONAL_FIELDS

    def assert_bookmark_response(self, response_data, bookmark, optional_fields=False):
        """
        Determines if the given response data (dict) matches the given bookmark.
        """
        self.assertEqual(response_data['id'], '%s,%s' % (self.user.username, unicode(bookmark.usage_key)))
        self.assertEqual(response_data['course_id'], unicode(bookmark.course_key))
        self.assertEqual(response_data['usage_id'], unicode(bookmark.usage_key))
        self.assertIsNotNone(response_data['created'])

        if optional_fields:
            self.assertEqual(response_data['display_name'], bookmark.display_name)
            self.assertEqual(response_data['path'], bookmark.path)

    def test_get_bookmark(self):
        """
        Verifies that get_bookmark returns data as expected.
        """
        bookmark_data = api.get_bookmark(user=self.user, usage_key=self.vertical.location)
        self.assert_bookmark_response(bookmark_data, self.bookmark)

        # With Optional fields.
        bookmark_data = api.get_bookmark(
            user=self.user,
            usage_key=self.vertical.location,
            fields=self.all_fields
        )
        self.assert_bookmark_response(bookmark_data, self.bookmark, optional_fields=True)

    def test_get_bookmark_raises_error(self):
        """
        Verifies that get_bookmark raises error as expected.
        """
        with self.assertRaises(ObjectDoesNotExist):
            api.get_bookmark(user=self.other_user, usage_key=self.vertical.location)

    def test_get_bookmarks(self):
        """
        Verifies that get_bookmarks returns data as expected.
        """
        # Without course key.
        bookmarks_data = api.get_bookmarks(user=self.user)
        self.assertEqual(len(bookmarks_data), 2)
        # Assert them in ordered manner.
        self.assert_bookmark_response(bookmarks_data[0], self.bookmark_2)
        self.assert_bookmark_response(bookmarks_data[1], self.bookmark)

        # With course key.
        bookmarks_data = api.get_bookmarks(user=self.user, course_key=self.course.id)
        self.assertEqual(len(bookmarks_data), 1)
        self.assert_bookmark_response(bookmarks_data[0], self.bookmark)

        # With optional fields.
        bookmarks_data = api.get_bookmarks(user=self.user, course_key=self.course.id, fields=self.all_fields)
        self.assertEqual(len(bookmarks_data), 1)
        self.assert_bookmark_response(bookmarks_data[0], self.bookmark, optional_fields=True)

        # Without Serialized.
        bookmarks = api.get_bookmarks(user=self.user, course_key=self.course.id, serialized=False)
        self.assertEqual(len(bookmarks), 1)
        self.assertTrue(bookmarks.model is Bookmark)  # pylint: disable=no-member
        self.assertEqual(bookmarks[0], self.bookmark)

    def test_create_bookmark(self):
        """
        Verifies that create_bookmark create & returns data as expected.
        """
        self.assertEqual(len(api.get_bookmarks(user=self.user, course_key=self.course.id)), 1)

        api.create_bookmark(user=self.user, usage_key=self.vertical_1.location)

        self.assertEqual(len(api.get_bookmarks(user=self.user, course_key=self.course.id)), 2)

    def test_create_bookmark_do_not_create_duplicates(self):
        """
        Verifies that create_bookmark do not create duplicate bookmarks.
        """
        self.assertEqual(len(api.get_bookmarks(user=self.user, course_key=self.course.id)), 1)
        bookmark_data = api.create_bookmark(user=self.user, usage_key=self.vertical_1.location)

        self.assertEqual(len(api.get_bookmarks(user=self.user, course_key=self.course.id)), 2)

        bookmark_data_2 = api.create_bookmark(user=self.user, usage_key=self.vertical_1.location)
        self.assertEqual(len(api.get_bookmarks(user=self.user, course_key=self.course.id)), 2)
        self.assertEqual(bookmark_data, bookmark_data_2)

    def test_create_bookmark_raises_error(self):
        """
        Verifies that create_bookmark raises error as expected.
        """
        with self.assertRaises(ItemNotFoundError):
            api.create_bookmark(user=self.user, usage_key=UsageKey.from_string('i4x://brb/100/html/340ef1771a0940'))

    def test_delete_bookmark(self):
        """
        Verifies that delete_bookmark removes bookmark as expected.
        """
        self.assertEqual(len(api.get_bookmarks(user=self.user)), 2)

        api.delete_bookmark(user=self.user, usage_key=self.vertical.location)

        bookmarks_data = api.get_bookmarks(user=self.user)
        self.assertEqual(len(bookmarks_data), 1)
        self.assertNotEqual(unicode(self.vertical.location), bookmarks_data[0]['usage_id'])

    def test_delete_bookmark_raises_error(self):
        """
        Verifies that delete_bookmark raises error as expected.
        """
        with self.assertRaises(ObjectDoesNotExist):
            api.delete_bookmark(user=self.other_user, usage_key=self.vertical.location)
