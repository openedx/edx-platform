"""
Tests for Bookmarks models.
"""

from bookmarks.models import Bookmark
from student.tests.factories import UserFactory

from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


class BookmarkModelTest(ModuleStoreTestCase):
    """
    Test the Bookmark model.
    """
    def setUp(self):
        super(BookmarkModelTest, self).setUp()

        self.user = UserFactory.create(password='test')

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
        self.vertical_2 = ItemFactory.create(
            parent_location=self.sequential.location, category='vertical', display_name='Subsection 2'
        )

        self.path = [
            {'display_name': self.chapter.display_name, 'usage_id': unicode(self.chapter.location)},
            {'display_name': self.sequential.display_name, 'usage_id': unicode(self.sequential.location)}
        ]

    def get_bookmark_data(self, block):
        """
        Returns bookmark data for testing.
        """
        return {
            'user': self.user,
            'course_key': self.course.id,
            'usage_key': block.location,
            'display_name': block.display_name,
        }

    def assert_valid_bookmark(self, bookmark_object, bookmark_data):
        """
        Check if the given data matches the specified bookmark.
        """
        self.assertEqual(bookmark_object.user, self.user)
        self.assertEqual(bookmark_object.course_key, bookmark_data['course_key'])
        self.assertEqual(bookmark_object.usage_key, self.vertical.location)
        self.assertEqual(bookmark_object.display_name, bookmark_data['display_name'])
        self.assertEqual(bookmark_object.path, self.path)
        self.assertIsNotNone(bookmark_object.created)

    def test_create_bookmark_success(self):
        """
        Tests creation of bookmark.
        """
        bookmark_data = self.get_bookmark_data(self.vertical)
        bookmark_object = Bookmark.create(bookmark_data)
        self.assert_valid_bookmark(bookmark_object, bookmark_data)

    def test_get_path(self):
        """
        Tests creation of path with given block.
        """
        path_object = Bookmark.get_path(block=self.vertical)
        self.assertEqual(path_object, self.path)

    def test_get_path_with_given_chapter_block(self):
        """
        Tests path for chapter level block.
        """
        path_object = Bookmark.get_path(block=self.chapter)
        self.assertEqual(len(path_object), 0)

    def test_get_path_with_given_sequential_block(self):
        """
        Tests path for sequential level block.
        """
        path_object = Bookmark.get_path(block=self.sequential)
        self.assertEqual(len(path_object), 1)
        self.assertEqual(path_object[0], self.path[0])

    def test_get_path_returns_empty_list_for_unreachable_parent(self):
        """
        Tests get_path returns empty list if block has no parent.
        """
        path = Bookmark.get_path(block=self.course)
        self.assertEqual(path, [])
