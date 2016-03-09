"""
Tests for Blocks Views
"""

from django.core.urlresolvers import reverse
from string import join
from urllib import urlencode
from urlparse import urlunparse

from course_blocks.tests.helpers import EnableTransformerRegistryMixin
from opaque_keys.edx.locator import CourseLocator
from student.models import CourseEnrollment
from student.tests.factories import AdminFactory, CourseEnrollmentFactory, UserFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import ToyCourseFactory

from .helpers import deserialize_usage_key


class TestBlocksView(EnableTransformerRegistryMixin, SharedModuleStoreTestCase):
    """
    Test class for BlocksView
    """
    requested_fields = ['graded', 'format', 'student_view_multi_device', 'children', 'not_a_field']

    @classmethod
    def setUpClass(cls):
        super(TestBlocksView, cls).setUpClass()

        # create a toy course
        cls.course_key = ToyCourseFactory.create().id
        cls.course_usage_key = cls.store.make_course_usage_key(cls.course_key)
        cls.non_orphaned_block_usage_keys = set(
            unicode(item.location)
            for item in cls.store.get_items(cls.course_key)
            # remove all orphaned items in the course, except for the root 'course' block
            if cls.store.get_parent_location(item.location) or item.category == 'course'
        )

    def setUp(self):
        super(TestBlocksView, self).setUp()

        # create a user, enrolled in the toy course
        self.user = UserFactory.create()
        self.client.login(username=self.user.username, password='test')
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course_key)

        # default values for url and query_params
        self.url = reverse(
            'blocks_in_block_tree',
            kwargs={'usage_key_string': unicode(self.course_usage_key)}
        )
        self.query_params = {'depth': 'all', 'username': self.user.username}

    def verify_response(self, expected_status_code=200, params=None, url=None):
        """
        Ensure that sending a GET request to the specified URL returns the
        expected status code.

        Arguments:
            expected_status_code: The status_code that is expected in the
                response.
            params: Parameters to add to self.query_params to include in the
                request.
            url: The URL to send the GET request.  Default is self.url.

        Returns:
            response: The HttpResponse returned by the request
        """
        if params:
            self.query_params.update(params)
        response = self.client.get(url or self.url, self.query_params)
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

    def test_no_user_non_staff(self):
        self.query_params.pop('username')
        self.query_params['all_blocks'] = True
        self.verify_response(403)

    def test_no_user_staff_not_all_blocks(self):
        self.query_params.pop('username')
        self.verify_response(400)

    def test_no_user_staff_all_blocks(self):
        self.client.login(username=AdminFactory.create().username, password='test')
        self.query_params.pop('username')
        self.query_params['all_blocks'] = True
        self.verify_response()

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

    def test_with_list_field_url(self):
        query = urlencode(self.query_params.items() + [
            ('requested_fields', self.requested_fields[0]),
            ('requested_fields', self.requested_fields[1]),
            ('requested_fields', join(self.requested_fields[1:], ',')),
        ])
        self.query_params = None
        response = self.verify_response(
            url=urlunparse(("", "", self.url, "", query, ""))
        )
        self.verify_response_with_requested_fields(response)


class TestBlocksInCourseView(TestBlocksView):  # pylint: disable=test-inherits-tests
    """
    Test class for BlocksInCourseView
    """
    def setUp(self):
        super(TestBlocksInCourseView, self).setUp()
        self.url = reverse('blocks_in_course')
        self.query_params['course_id'] = unicode(self.course_key)

    def test_no_course_id(self):
        self.query_params.pop('course_id')
        self.verify_response(400)

    def test_invalid_course_id(self):
        self.verify_response(400, params={'course_id': 'invalid_course_id'})

    def test_non_existent_course(self):
        self.verify_response(403, params={'course_id': unicode(CourseLocator('non', 'existent', 'course'))})
