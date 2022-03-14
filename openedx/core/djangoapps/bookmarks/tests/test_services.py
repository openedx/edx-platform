"""
Tests for bookmark services.
"""


from opaque_keys.edx.keys import UsageKey

from openedx.core.djangolib.testing.utils import skip_unless_lms

from ..services import BookmarksService
from .test_models import BookmarksTestsBase


@skip_unless_lms
class BookmarksServiceTests(BookmarksTestsBase):
    """
    Tests the Bookmarks service.
    """

    def setUp(self):
        super().setUp()

        self.bookmark_service = BookmarksService(user=self.user)

    def test_get_bookmarks(self):
        """
        Verifies get_bookmarks returns data as expected.
        """
        with self.assertNumQueries(1):
            bookmarks_data = self.bookmark_service.bookmarks(course_key=self.course.id)

        assert len(bookmarks_data) == 4
        self.assert_bookmark_data_is_valid(self.bookmark_4, bookmarks_data[0])
        self.assert_bookmark_data_is_valid(self.bookmark_3, bookmarks_data[1])
        self.assert_bookmark_data_is_valid(self.bookmark_2, bookmarks_data[2])
        self.assert_bookmark_data_is_valid(self.bookmark_1, bookmarks_data[3])

    def test_is_bookmarked(self):
        """
        Verifies is_bookmarked returns Bool as expected.
        """
        with self.assertNumQueries(1):
            assert self.bookmark_service.is_bookmarked(usage_key=self.sequential_1.location)
            assert not self.bookmark_service.is_bookmarked(usage_key=self.vertical_2.location)
            assert self.bookmark_service.is_bookmarked(usage_key=self.sequential_2.location)

        self.bookmark_service.set_bookmarked(usage_key=self.chapter_1.location)
        with self.assertNumQueries(0):
            assert self.bookmark_service.is_bookmarked(usage_key=self.chapter_1.location)
            assert not self.bookmark_service.is_bookmarked(usage_key=self.vertical_2.location)

        # Removing a bookmark should result in the cache being updated on the next request
        self.bookmark_service.unset_bookmarked(usage_key=self.chapter_1.location)
        with self.assertNumQueries(0):
            assert not self.bookmark_service.is_bookmarked(usage_key=self.chapter_1.location)
            assert not self.bookmark_service.is_bookmarked(usage_key=self.vertical_2.location)

        # Get bookmark that does not exist.
        bookmark_service = BookmarksService(self.other_user)
        with self.assertNumQueries(1):
            assert not bookmark_service.is_bookmarked(usage_key=self.sequential_1.location)

    def test_set_bookmarked(self):
        """
        Verifies set_bookmarked returns Bool as expected.
        """
        # Assert False for item that does not exist.
        with self.assertNumQueries(0):
            assert not self.bookmark_service\
                .set_bookmarked(usage_key=UsageKey.from_string('i4x://ed/ed/ed/interactive'))

        with self.assertNumQueries(10):
            assert self.bookmark_service.set_bookmarked(usage_key=self.vertical_2.location)

    def test_unset_bookmarked(self):
        """
        Verifies unset_bookmarked returns Bool as expected.
        """
        with self.assertNumQueries(1):
            assert not self.bookmark_service\
                .unset_bookmarked(usage_key=UsageKey.from_string('i4x://ed/ed/ed/interactive'))

        with self.assertNumQueries(3):
            assert self.bookmark_service.unset_bookmarked(usage_key=self.sequential_1.location)
