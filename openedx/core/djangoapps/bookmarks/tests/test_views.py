"""
Tests for bookmark views.
"""

import ddt
import json
from nose.plugins.attrib import attr
from unittest import skipUnless
import urllib

from django.conf import settings
from django.core.urlresolvers import reverse
from mock import patch
from rest_framework.test import APIClient

from xmodule.modulestore import ModuleStoreEnum

from .test_models import BookmarksTestsBase
from .test_api import BookmarkApiEventTestMixin


# pylint: disable=no-member
class BookmarksViewsTestsBase(BookmarksTestsBase, BookmarkApiEventTestMixin):
    """
    Base class for bookmarks views tests.
    """
    def setUp(self):
        super(BookmarksViewsTestsBase, self).setUp()

        self.anonymous_client = APIClient()
        self.client = self.login_client(user=self.user)

    def login_client(self, user):
        """
        Helper method for getting the client and user and logging in. Returns client.
        """
        client = APIClient()
        client.login(username=user.username, password=self.TEST_PASSWORD)
        return client

    def send_get(self, client, url, query_parameters=None, expected_status=200):
        """
        Helper method for sending a GET to the server. Verifies the expected status and returns the response.
        """
        url = url + '?' + query_parameters if query_parameters else url
        response = client.get(url)
        self.assertEqual(expected_status, response.status_code)
        return response

    def send_post(self, client, url, data, content_type='application/json', expected_status=201):
        """
        Helper method for sending a POST to the server. Verifies the expected status and returns the response.
        """
        response = client.post(url, data=json.dumps(data), content_type=content_type)
        self.assertEqual(expected_status, response.status_code)
        return response

    def send_delete(self, client, url, expected_status=204):
        """
        Helper method for sending a DELETE to the server. Verifies the expected status and returns the response.
        """
        response = client.delete(url)
        self.assertEqual(expected_status, response.status_code)
        return response


@attr('shard_2')
@ddt.ddt
@skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Tests only valid in LMS')
class BookmarksListViewTests(BookmarksViewsTestsBase):
    """
    This contains the tests for GET & POST methods of bookmark.views.BookmarksListView class
    GET /api/bookmarks/v1/bookmarks/?course_id={course_id1}
    POST /api/bookmarks/v1/bookmarks
    """
    @ddt.data(
        (1, False),
        (10, False),
        (25, False),
        (1, True),
        (10, True),
        (25, True),
    )
    @ddt.unpack
    @patch('eventtracking.tracker.emit')
    def test_get_bookmarks_successfully(self, bookmarks_count, check_all_fields, mock_tracker):
        """
        Test that requesting bookmarks for a course returns records successfully in
        expected order without optional fields.
        """

        course, __, bookmarks = self.create_course_with_bookmarks_count(
            bookmarks_count, store_type=ModuleStoreEnum.Type.mongo
        )

        query_parameters = 'course_id={}&page_size={}'.format(urllib.quote(unicode(course.id)), 100)
        if check_all_fields:
            query_parameters += '&fields=path,display_name'

        response = self.send_get(
            client=self.client,
            url=reverse('bookmarks'),
            query_parameters=query_parameters,
        )
        bookmarks_data = response.data['results']

        self.assertEqual(len(bookmarks_data), len(bookmarks))
        self.assertEqual(response.data['count'], len(bookmarks))
        self.assertEqual(response.data['num_pages'], 1)

        # As bookmarks are sorted by -created so we will compare in that order.
        self.assert_bookmark_data_is_valid(bookmarks[-1], bookmarks_data[0], check_optional_fields=check_all_fields)
        self.assert_bookmark_data_is_valid(bookmarks[0], bookmarks_data[-1], check_optional_fields=check_all_fields)

        self.assert_bookmark_event_emitted(
            mock_tracker,
            event_name='edx.bookmark.listed',
            course_id=unicode(course.id),
            list_type='per_course',
            bookmarks_count=bookmarks_count,
            page_size=100,
            page_number=1
        )

    @ddt.data(
        10, 25
    )
    @patch('eventtracking.tracker.emit')
    def test_get_bookmarks_with_pagination(self, bookmarks_count, mock_tracker):
        """
        Test that requesting bookmarks for a course return results with pagination 200 code.
        """

        course, __, bookmarks = self.create_course_with_bookmarks_count(
            bookmarks_count, store_type=ModuleStoreEnum.Type.mongo
        )

        page_size = 5
        query_parameters = 'course_id={}&page_size={}'.format(urllib.quote(unicode(course.id)), page_size)

        response = self.send_get(
            client=self.client,
            url=reverse('bookmarks'),
            query_parameters=query_parameters
        )
        bookmarks_data = response.data['results']

        # Pagination assertions.
        self.assertEqual(response.data['count'], bookmarks_count)
        self.assertIn('page=2&page_size={}'.format(page_size), response.data['next'])
        self.assertEqual(response.data['num_pages'], bookmarks_count / page_size)

        self.assertEqual(len(bookmarks_data), min(bookmarks_count, page_size))
        self.assert_bookmark_data_is_valid(bookmarks[-1], bookmarks_data[0])

        self.assert_bookmark_event_emitted(
            mock_tracker,
            event_name='edx.bookmark.listed',
            course_id=unicode(course.id),
            list_type='per_course',
            bookmarks_count=bookmarks_count,
            page_size=page_size,
            page_number=1
        )

    @patch('eventtracking.tracker.emit')
    def test_get_bookmarks_with_invalid_data(self, mock_tracker):
        """
        Test that requesting bookmarks with invalid data returns 0 records.
        """
        # Invalid course id.
        response = self.send_get(
            client=self.client,
            url=reverse('bookmarks'),
            query_parameters='course_id=invalid'
        )
        bookmarks_data = response.data['results']

        self.assertEqual(len(bookmarks_data), 0)
        self.assertFalse(mock_tracker.emit.called)  # pylint: disable=maybe-no-member

    @patch('eventtracking.tracker.emit')
    def test_get_all_bookmarks_when_course_id_not_given(self, mock_tracker):
        """
        Test that requesting bookmarks returns all records for that user.
        """
        # Without course id we would return all the bookmarks for that user.
        response = self.send_get(
            client=self.client,
            url=reverse('bookmarks')
        )
        bookmarks_data = response.data['results']
        self.assertEqual(len(bookmarks_data), 3)
        self.assert_bookmark_data_is_valid(self.other_bookmark_1, bookmarks_data[0])
        self.assert_bookmark_data_is_valid(self.bookmark_2, bookmarks_data[1])
        self.assert_bookmark_data_is_valid(self.bookmark_1, bookmarks_data[2])

        self.assert_bookmark_event_emitted(
            mock_tracker,
            event_name='edx.bookmark.listed',
            list_type='all_courses',
            bookmarks_count=3,
            page_size=10,
            page_number=1
        )

    def test_anonymous_access(self):
        """
        Test that an anonymous client (not logged in) cannot call GET or POST.
        """
        query_parameters = 'course_id={}'.format(self.course_id)
        self.send_get(
            client=self.anonymous_client,
            url=reverse('bookmarks'),
            query_parameters=query_parameters,
            expected_status=401
        )
        self.send_post(
            client=self.anonymous_client,
            url=reverse('bookmarks'),
            data={'usage_id': 'test'},
            expected_status=401
        )

    def test_post_bookmark_successfully(self):
        """
        Test that posting a bookmark successfully returns newly created data with 201 code.
        """
        response = self.send_post(
            client=self.client,
            url=reverse('bookmarks'),
            data={'usage_id': unicode(self.vertical_3.location)}
        )

        # Assert Newly created bookmark.
        self.assertEqual(response.data['id'], '%s,%s' % (self.user.username, unicode(self.vertical_3.location)))
        self.assertEqual(response.data['course_id'], self.course_id)
        self.assertEqual(response.data['usage_id'], unicode(self.vertical_3.location))
        self.assertIsNotNone(response.data['created'])
        self.assertEqual(len(response.data['path']), 2)
        self.assertEqual(response.data['display_name'], self.vertical_3.display_name)

    def test_post_bookmark_with_invalid_data(self):
        """
        Test that posting a bookmark for a block with invalid usage id returns a 400.
        Scenarios:
            1) Invalid usage id.
            2) Without usage id.
            3) With empty request.data
        """
        # Send usage_id with invalid format.
        response = self.send_post(
            client=self.client,
            url=reverse('bookmarks'),
            data={'usage_id': 'invalid'},
            expected_status=400
        )
        self.assertEqual(response.data['user_message'], u'An error has occurred. Please try again.')

        # Send data without usage_id.
        response = self.send_post(
            client=self.client,
            url=reverse('bookmarks'),
            data={'course_id': 'invalid'},
            expected_status=400
        )
        self.assertEqual(response.data['user_message'], u'An error has occurred. Please try again.')
        self.assertEqual(response.data['developer_message'], u'Parameter usage_id not provided.')

        # Send empty data dictionary.
        with self.assertNumQueries(8):  # No queries for bookmark table.
            response = self.send_post(
                client=self.client,
                url=reverse('bookmarks'),
                data={},
                expected_status=400
            )
        self.assertEqual(response.data['user_message'], u'An error has occurred. Please try again.')
        self.assertEqual(response.data['developer_message'], u'No data provided.')

    def test_post_bookmark_for_non_existing_block(self):
        """
        Test that posting a bookmark for a block that does not exist returns a 400.
        """
        response = self.send_post(
            client=self.client,
            url=reverse('bookmarks'),
            data={'usage_id': 'i4x://arbi/100/html/340ef1771a094090ad260ec940d04a21'},
            expected_status=400
        )
        self.assertEqual(
            response.data['user_message'],
            u'An error has occurred. Please try again.'
        )
        self.assertEqual(
            response.data['developer_message'],
            u'Block with usage_id: i4x://arbi/100/html/340ef1771a094090ad260ec940d04a21 not found.'
        )

    @patch('django.conf.settings.MAX_BOOKMARKS_PER_COURSE', 5)
    def test_post_bookmark_when_max_bookmarks_already_exist(self):
        """
        Test that posting a bookmark for a block that does not exist returns a 400.
        """
        max_bookmarks = settings.MAX_BOOKMARKS_PER_COURSE
        __, blocks, __ = self.create_course_with_bookmarks_count(max_bookmarks)

        response = self.send_post(
            client=self.client,
            url=reverse('bookmarks'),
            data={'usage_id': unicode(blocks[-1].location)},
            expected_status=400
        )
        self.assertEqual(
            response.data['user_message'],
            u'You can create up to {0} bookmarks.'
            u' You must remove some bookmarks before you can add new ones.'.format(max_bookmarks)
        )
        self.assertEqual(
            response.data['developer_message'],
            u'You can create up to {0} bookmarks.'
            u' You must remove some bookmarks before you can add new ones.'.format(max_bookmarks)
        )

    def test_unsupported_methods(self):
        """
        Test that DELETE and PUT are not supported.
        """
        self.client.login(username=self.user.username, password=self.TEST_PASSWORD)
        self.assertEqual(405, self.client.put(reverse('bookmarks')).status_code)
        self.assertEqual(405, self.client.delete(reverse('bookmarks')).status_code)

    @patch('eventtracking.tracker.emit')
    @ddt.unpack
    @ddt.data(
        {'page_size': -1, 'expected_bookmarks_count': 2, 'expected_page_size': 10, 'expected_page_number': 1},
        {'page_size': 0, 'expected_bookmarks_count': 2, 'expected_page_size': 10, 'expected_page_number': 1},
        {'page_size': 999, 'expected_bookmarks_count': 2, 'expected_page_size': 100, 'expected_page_number': 1}
    )
    def test_listed_event_for_different_page_size_values(self, mock_tracker, page_size, expected_bookmarks_count,
                                                         expected_page_size, expected_page_number):
        """ Test that edx.course.bookmark.listed event values are as expected for different page size values """
        query_parameters = 'course_id={}&page_size={}'.format(urllib.quote(self.course_id), page_size)

        self.send_get(client=self.client, url=reverse('bookmarks'), query_parameters=query_parameters)

        self.assert_bookmark_event_emitted(
            mock_tracker,
            event_name='edx.bookmark.listed',
            course_id=self.course_id,
            list_type='per_course',
            bookmarks_count=expected_bookmarks_count,
            page_size=expected_page_size,
            page_number=expected_page_number
        )

    @patch('openedx.core.djangoapps.bookmarks.views.eventtracking.tracker.emit')
    def test_listed_event_for_page_number(self, mock_tracker):
        """ Test that edx.course.bookmark.listed event values are as expected when we request a specific page number """
        self.send_get(client=self.client, url=reverse('bookmarks'), query_parameters='page_size=2&page=2')

        self.assert_bookmark_event_emitted(
            mock_tracker,
            event_name='edx.bookmark.listed',
            list_type='all_courses',
            bookmarks_count=3,
            page_size=2,
            page_number=2
        )


@attr('shard_2')
@ddt.ddt
@skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Tests only valid in LMS')
class BookmarksDetailViewTests(BookmarksViewsTestsBase):
    """
    This contains the tests for GET & DELETE methods of bookmark.views.BookmarksDetailView class
    """
    @ddt.data(
        ('', False),
        ('fields=path,display_name', True)
    )
    @ddt.unpack
    def test_get_bookmark_successfully(self, query_params, check_optional_fields):
        """
        Test that requesting bookmark returns data with 200 code.
        """
        response = self.send_get(
            client=self.client,
            url=reverse(
                'bookmarks_detail',
                kwargs={'username': self.user.username, 'usage_id': unicode(self.sequential_1.location)}
            ),
            query_parameters=query_params
        )
        data = response.data
        self.assertIsNotNone(data)
        self.assert_bookmark_data_is_valid(self.bookmark_1, data, check_optional_fields=check_optional_fields)

    def test_get_bookmark_that_belongs_to_other_user(self):
        """
        Test that requesting bookmark that belongs to other user returns 404 status code.
        """
        self.send_get(
            client=self.client,
            url=reverse(
                'bookmarks_detail',
                kwargs={'username': 'other', 'usage_id': unicode(self.vertical_1.location)}
            ),
            expected_status=404
        )

    def test_get_bookmark_that_does_not_exist(self):
        """
        Test that requesting bookmark that does not exist returns 404 status code.
        """
        response = self.send_get(
            client=self.client,
            url=reverse(
                'bookmarks_detail',
                kwargs={'username': self.user.username, 'usage_id': 'i4x://arbi/100/html/340ef1771a0940'}
            ),
            expected_status=404
        )
        self.assertEqual(
            response.data['user_message'],
            'Bookmark with usage_id: i4x://arbi/100/html/340ef1771a0940 does not exist.'
        )
        self.assertEqual(
            response.data['developer_message'],
            'Bookmark with usage_id: i4x://arbi/100/html/340ef1771a0940 does not exist.'
        )

    def test_get_bookmark_with_invalid_usage_id(self):
        """
        Test that requesting bookmark with invalid usage id returns 400.
        """
        response = self.send_get(
            client=self.client,
            url=reverse(
                'bookmarks_detail',
                kwargs={'username': self.user.username, 'usage_id': 'i4x'}
            ),
            expected_status=404
        )
        self.assertEqual(response.data['user_message'], u'Invalid usage_id: i4x.')

    def test_anonymous_access(self):
        """
        Test that an anonymous client (not logged in) cannot call GET or DELETE.
        """
        url = reverse('bookmarks_detail', kwargs={'username': self.user.username, 'usage_id': 'i4x'})
        self.send_get(
            client=self.anonymous_client,
            url=url,
            expected_status=401
        )
        self.send_delete(
            client=self.anonymous_client,
            url=url,
            expected_status=401
        )

    def test_delete_bookmark_successfully(self):
        """
        Test that delete bookmark returns 204 status code with success.
        """
        query_parameters = 'course_id={}'.format(urllib.quote(self.course_id))
        response = self.send_get(client=self.client, url=reverse('bookmarks'), query_parameters=query_parameters)
        bookmarks_data = response.data['results']
        self.assertEqual(len(bookmarks_data), 2)

        self.send_delete(
            client=self.client,
            url=reverse(
                'bookmarks_detail',
                kwargs={'username': self.user.username, 'usage_id': unicode(self.sequential_1.location)}
            )
        )
        response = self.send_get(client=self.client, url=reverse('bookmarks'), query_parameters=query_parameters)
        bookmarks_data = response.data['results']

        self.assertEqual(len(bookmarks_data), 1)

    def test_delete_bookmark_that_belongs_to_other_user(self):
        """
        Test that delete bookmark that belongs to other user returns 404.
        """
        self.send_delete(
            client=self.client,
            url=reverse(
                'bookmarks_detail',
                kwargs={'username': 'other', 'usage_id': unicode(self.vertical_1.location)}
            ),
            expected_status=404
        )

    def test_delete_bookmark_that_does_not_exist(self):
        """
        Test that delete bookmark that does not exist returns 404.
        """
        response = self.send_delete(
            client=self.client,
            url=reverse(
                'bookmarks_detail',
                kwargs={'username': self.user.username, 'usage_id': 'i4x://arbi/100/html/340ef1771a0940'}
            ),
            expected_status=404
        )
        self.assertEqual(
            response.data['user_message'],
            u'Bookmark with usage_id: i4x://arbi/100/html/340ef1771a0940 does not exist.'
        )
        self.assertEqual(
            response.data['developer_message'],
            'Bookmark with usage_id: i4x://arbi/100/html/340ef1771a0940 does not exist.'
        )

    def test_delete_bookmark_with_invalid_usage_id(self):
        """
        Test that delete bookmark with invalid usage id returns 400.
        """
        response = self.send_delete(
            client=self.client,
            url=reverse(
                'bookmarks_detail',
                kwargs={'username': self.user.username, 'usage_id': 'i4x'}
            ),
            expected_status=404
        )
        self.assertEqual(response.data['user_message'], u'Invalid usage_id: i4x.')

    def test_unsupported_methods(self):
        """
        Test that POST and PUT are not supported.
        """
        url = reverse('bookmarks_detail', kwargs={'username': self.user.username, 'usage_id': 'i4x'})
        self.client.login(username=self.user.username, password=self.TEST_PASSWORD)
        self.assertEqual(405, self.client.put(url).status_code)
        self.assertEqual(405, self.client.post(url).status_code)
