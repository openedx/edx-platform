"""
Tests for Blocks Views
"""

from django.core.urlresolvers import reverse
from string import join

from opaque_keys.edx.locator import CourseLocator
from student.models import CourseEnrollment
from student.tests.factories import CourseEnrollmentFactory, UserFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import ToyCourseFactory

from .test_utils import deserialize_usage_key


class TestBlocksViewMixin(object):
    """
    Mixin class for test helpers for BlocksView related classes
    """
    @classmethod
    def setup_course(cls):
        """
        Create a sample course
        """
        cls.course_key = ToyCourseFactory.create().id

        cls.non_orphaned_block_usage_keys = set(
            unicode(item.location)
            for item in cls.store.get_items(cls.course_key)
            # remove all orphaned items in the course, except for the root 'course' block
            if cls.store.get_parent_location(item.location) or item.category == 'course'
        )

    def setup_user(self):
        """
        Create a user, enrolled in the sample course
        """
        self.user = UserFactory.create()  # pylint: disable=attribute-defined-outside-init
        self.client.login(username=self.user.username, password='test')

        CourseEnrollmentFactory.create(user=self.user, course_id=self.course_key)

    def verify_response(self, expected_status_code=200, params=None, url=None):
        """
        Ensure that the sending a GET request to the specified URL (or self.url)
        returns the expected status code (200 by default).

        Arguments:
            expected_status_code: (default 200)
            params:
                query parameters to include in the request (includes
                username=[self.user.username]&depth=all by default)
            url: (default [self.url])

        Returns:
            response: The HttpResponse returned by the request
        """
        query_params = {'username': self.user.username, 'depth': 'all'}
        if params:
            query_params.update(params)
        response = self.client.get(url or self.url, query_params)
        self.assertEquals(response.status_code, expected_status_code)
        return response

    def verify_response_block_list(self, response):
        """
        Verify that the response contains only the expected block ids.
        """
        self.assertSetEqual(
            {block['id'] for block in response.data},
            self.non_orphaned_block_usage_keys,
        )

    def verify_response_block_dict(self, response):
        """
        Verify that the response contains the expected blocks
        """
        self.assertSetEqual(
            set(response.data['blocks'].iterkeys()),
            self.non_orphaned_block_usage_keys,
        )

    requested_fields = ['graded', 'format', 'student_view_multi_device', 'children', 'not_a_field']

    def verify_response_with_requested_fields(self, response):
        """
        Verify the response has the expected structure
        """
        self.verify_response_block_dict(response)
        for block_key_string, block_data in response.data['blocks'].iteritems():
            block_key = deserialize_usage_key(block_key_string, self.course_key)
            xblock = self.store.get_item(block_key)

            self.assert_in_iff('children', block_data, xblock.has_children)
            self.assert_in_iff('graded', block_data, xblock.graded is not None)
            self.assert_in_iff('format', block_data, xblock.format is not None)
            self.assert_true_iff(block_data['student_view_multi_device'], block_data['type'] == 'html')
            self.assertNotIn('not_a_field', block_data)

            if xblock.has_children:
                self.assertSetEqual(
                    set(unicode(child.location) for child in xblock.get_children()),
                    set(block_data['children']),
                )

    def assert_in_iff(self, member, container, predicate):
        """
        Assert that member is in container if and only if predicate is true.

        Arguments:
            member - any object
            container - any container
            predicate - an expression, tested for truthiness
        """
        if predicate:
            self.assertIn(member, container)
        else:
            self.assertNotIn(member, container)

    def assert_true_iff(self, expression, predicate):
        """
        Assert that the expression is true if and only if the predicate is true

        Arguments:
            expression
            predicate
        """

        if predicate:
            self.assertTrue(expression)
        else:
            self.assertFalse(expression)


# pylint: disable=no-member
class TestBlocksView(TestBlocksViewMixin, SharedModuleStoreTestCase):
    """
    Test class for BlocksView
    """
    @classmethod
    def setUpClass(cls):
        super(TestBlocksView, cls).setUpClass()
        cls.setup_course()
        cls.course_usage_key = cls.store.make_course_usage_key(cls.course_key)
        cls.url = reverse(
            'blocks_in_block_tree',
            kwargs={'usage_key_string': unicode(cls.course_usage_key)}
        )

    def setUp(self):
        super(TestBlocksView, self).setUp()
        self.setup_user()

    def test_not_authenticated(self):
        self.client.logout()
        self.verify_response(401)

    def test_not_enrolled(self):
        CourseEnrollment.unenroll(self.user, self.course_key)
        self.verify_response(403)

    def test_non_existent_course(self):
        usage_key = self.store.make_course_usage_key(CourseLocator('non', 'existent', 'course'))
        url = reverse(
            'blocks_in_block_tree',
            kwargs={'usage_key_string': unicode(usage_key)}
        )
        self.verify_response(403, url=url)

    def test_basic(self):
        response = self.verify_response()
        self.assertEquals(response.data['root'], unicode(self.course_usage_key))
        self.verify_response_block_dict(response)
        for block_key_string, block_data in response.data['blocks'].iteritems():
            block_key = deserialize_usage_key(block_key_string, self.course_key)
            self.assertEquals(block_data['id'], block_key_string)
            self.assertEquals(block_data['type'], block_key.block_type)
            self.assertEquals(block_data['display_name'], self.store.get_item(block_key).display_name or '')

    def test_return_type_param(self):
        response = self.verify_response(params={'return_type': 'list'})
        self.verify_response_block_list(response)

    def test_block_counts_param(self):
        response = self.verify_response(params={'block_counts': ['course', 'chapter']})
        self.verify_response_block_dict(response)
        for block_data in response.data['blocks'].itervalues():
            self.assertEquals(
                block_data['block_counts']['course'],
                1 if block_data['type'] == 'course' else 0,
            )
            self.assertEquals(
                block_data['block_counts']['chapter'],
                (
                    1 if block_data['type'] == 'chapter' else
                    5 if block_data['type'] == 'course' else
                    0
                )
            )

    def test_student_view_data_param(self):
        response = self.verify_response(params={'student_view_data': ['video', 'chapter']})
        self.verify_response_block_dict(response)
        for block_data in response.data['blocks'].itervalues():
            self.assert_in_iff('student_view_data', block_data, block_data['type'] == 'video')

    def test_navigation_param(self):
        response = self.verify_response(params={'nav_depth': 10})
        self.verify_response_block_dict(response)
        for block_data in response.data['blocks'].itervalues():
            self.assertIn('descendants', block_data)

    def test_requested_fields_param(self):
        response = self.verify_response(
            params={'requested_fields': self.requested_fields}
        )
        self.verify_response_with_requested_fields(response)


class TestBlocksInCourseView(TestBlocksViewMixin, SharedModuleStoreTestCase):
    """
    Test class for BlocksInCourseView
    """
    @classmethod
    def setUpClass(cls):
        super(TestBlocksInCourseView, cls).setUpClass()
        cls.setup_course()
        cls.url = reverse('blocks_in_course')

    def setUp(self):
        super(TestBlocksInCourseView, self).setUp()
        self.setup_user()

    def test_basic(self):
        response = self.verify_response(params={'course_id': unicode(self.course_key)})
        self.verify_response_block_dict(response)

    def test_no_course_id(self):
        self.verify_response(400)

    def test_invalid_course_id(self):
        self.verify_response(400, params={'course_id': 'invalid_course_id'})

    def test_with_list_field_url(self):
        url = '{base_url}?course_id={course_id}&username={username}&depth=all'.format(
            course_id=unicode(self.course_key),
            base_url=self.url.format(),
            username=self.user.username,
        )
        url += '&requested_fields={0}&requested_fields={1}&requested_fields={2}'.format(
            self.requested_fields[0],
            self.requested_fields[1],
            join(self.requested_fields[1:], ','),
        )
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        self.verify_response_with_requested_fields(response)
