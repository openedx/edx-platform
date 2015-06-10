"""
Run these tests @ Devstack:
    paver test_system -s lms --fasttest --verbose --test_id=lms/djangoapps/course_structure_api
"""
# pylint: disable=missing-docstring,invalid-name,maybe-no-member,attribute-defined-outside-init
from abc import ABCMeta
from datetime import datetime
from mock import patch, Mock
from itertools import product

from django.core.urlresolvers import reverse

from capa.tests.response_xml_factory import MultipleChoiceResponseXMLFactory
from oauth2_provider.tests.factories import AccessTokenFactory, ClientFactory
from opaque_keys.edx.locator import CourseLocator
from xmodule.error_module import ErrorDescriptor
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory, check_mongo_calls
from xmodule.modulestore.xml import CourseLocationManager
from xmodule.tests import get_test_system

from student.tests.factories import UserFactory, CourseEnrollmentFactory
from courseware.tests.factories import GlobalStaffFactory, StaffFactory
from openedx.core.djangoapps.content.course_structures.models import CourseStructure
from openedx.core.djangoapps.content.course_structures.tasks import update_course_structure


TEST_SERVER_HOST = 'http://testserver'


class CourseViewTestsMixin(object):
    """
    Mixin for course view tests.
    """
    view = None

    def setUp(self):
        super(CourseViewTestsMixin, self).setUp()
        self.create_test_data()
        self.create_user_and_access_token()

    def create_user(self):
        self.user = GlobalStaffFactory.create()

    def create_user_and_access_token(self):
        self.create_user()
        self.oauth_client = ClientFactory.create()
        self.access_token = AccessTokenFactory.create(user=self.user, client=self.oauth_client).token

    def create_test_data(self):
        self.invalid_course_id = 'foo/bar/baz'
        self.course = CourseFactory.create(display_name='An Introduction to API Testing', raw_grader=[
            {
                "min_count": 24,
                "weight": 0.2,
                "type": "Homework",
                "drop_count": 0,
                "short_label": "HW"
            },
            {
                "min_count": 4,
                "weight": 0.8,
                "type": "Exam",
                "drop_count": 0,
                "short_label": "Exam"
            }
        ])
        self.course_id = unicode(self.course.id)

        self.sequential = ItemFactory.create(
            category="sequential",
            parent_location=self.course.location,
            display_name="Lesson 1",
            format="Homework",
            graded=True
        )

        factory = MultipleChoiceResponseXMLFactory()
        args = {'choices': [False, True, False]}
        problem_xml = factory.build_xml(**args)
        ItemFactory.create(
            category="problem",
            parent_location=self.sequential.location,
            display_name="Problem 1",
            format="Homework",
            data=problem_xml,
        )

        self.video = ItemFactory.create(
            category="video",
            parent_location=self.sequential.location,
            display_name="Video 1",
        )

        self.empty_course = CourseFactory.create(
            start=datetime(2014, 6, 16, 14, 30),
            end=datetime(2015, 1, 16),
            org="MTD",
            # Use mongo so that we can get a test with a SlashSeparatedCourseKey
            default_store=ModuleStoreEnum.Type.mongo
        )

    def build_absolute_url(self, path=None):
        """ Build absolute URL pointing to test server.
        :param path: Path to append to the URL
        """
        url = TEST_SERVER_HOST

        if path:
            url += path

        return url

    def assertValidResponseCourse(self, data, course):
        """ Determines if the given response data (dict) matches the specified course. """

        course_key = course.id
        self.assertEqual(data['id'], unicode(course_key))
        self.assertEqual(data['name'], course.display_name)
        self.assertEqual(data['course'], course_key.course)
        self.assertEqual(data['org'], course_key.org)
        self.assertEqual(data['run'], course_key.run)

        uri = self.build_absolute_url(
            reverse('course_structure_api:v0:detail', kwargs={'course_id': unicode(course_key)}))
        self.assertEqual(data['uri'], uri)

    def http_get(self, uri, **headers):
        """Submit an HTTP GET request"""

        default_headers = {
            'HTTP_AUTHORIZATION': 'Bearer ' + self.access_token
        }
        default_headers.update(headers)

        response = self.client.get(uri, follow=True, **default_headers)
        return response

    def http_get_for_course(self, course_id=None, **headers):
        """Submit an HTTP GET request to the view for the given course"""

        return self.http_get(
            reverse(self.view, kwargs={'course_id': course_id or self.course_id}),
            **headers
        )

    def test_not_authenticated(self):
        """
        Verify that access is denied to non-authenticated users.
        """
        raise NotImplementedError

    def test_not_authorized(self):
        """
        Verify that access is denied to non-authorized users.
        """
        raise NotImplementedError


class CourseDetailTestMixin(object):
    """
    Mixin for views utilizing only the course_id kwarg.
    """
    view_supports_debug_mode = True

    def test_get_invalid_course(self):
        """
        The view should return a 404 if the course ID is invalid.
        """
        response = self.http_get_for_course(self.invalid_course_id)
        self.assertEqual(response.status_code, 404)

    def test_get(self):
        """
        The view should return a 200 if the course ID is valid.
        """
        response = self.http_get_for_course()
        self.assertEqual(response.status_code, 200)

        # Return the response so child classes do not have to repeat the request.
        return response

    def test_not_authenticated(self):
        """ The view should return HTTP status 401 if no user is authenticated. """
        # HTTP 401 should be returned if the user is not authenticated.
        response = self.http_get_for_course(HTTP_AUTHORIZATION=None)
        self.assertEqual(response.status_code, 401)

    def test_not_authorized(self):
        user = StaffFactory(course_key=self.course.id)
        access_token = AccessTokenFactory.create(user=user, client=self.oauth_client).token
        auth_header = 'Bearer ' + access_token

        # Access should be granted if the proper access token is supplied.
        response = self.http_get_for_course(HTTP_AUTHORIZATION=auth_header)
        self.assertEqual(response.status_code, 200)

        # Access should be denied if the user is not course staff.
        response = self.http_get_for_course(course_id=unicode(self.empty_course.id), HTTP_AUTHORIZATION=auth_header)
        self.assertEqual(response.status_code, 404)


class CourseListTests(CourseViewTestsMixin, ModuleStoreTestCase):
    view = 'course_structure_api:v0:list'

    def test_get(self):
        """
        The view should return a list of all courses.
        """
        response = self.http_get(reverse(self.view))
        self.assertEqual(response.status_code, 200)
        data = response.data
        courses = data['results']

        self.assertEqual(len(courses), 2)
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['num_pages'], 1)

        self.assertValidResponseCourse(courses[0], self.empty_course)
        self.assertValidResponseCourse(courses[1], self.course)

    def test_get_with_pagination(self):
        """
        The view should return a paginated list of courses.
        """
        url = "{}?page_size=1".format(reverse(self.view))
        response = self.http_get(url)
        self.assertEqual(response.status_code, 200)

        courses = response.data['results']
        self.assertEqual(len(courses), 1)
        self.assertValidResponseCourse(courses[0], self.empty_course)

    def test_get_filtering(self):
        """
        The view should return a list of details for the specified courses.
        """
        url = "{}?course_id={}".format(reverse(self.view), self.course_id)
        response = self.http_get(url)
        self.assertEqual(response.status_code, 200)

        courses = response.data['results']
        self.assertEqual(len(courses), 1)
        self.assertValidResponseCourse(courses[0], self.course)

    def test_not_authenticated(self):
        response = self.http_get(reverse(self.view), HTTP_AUTHORIZATION=None)
        self.assertEqual(response.status_code, 401)

    def test_not_authorized(self):
        """
        Unauthorized users should get an empty list.
        """
        user = StaffFactory(course_key=self.course.id)
        access_token = AccessTokenFactory.create(user=user, client=self.oauth_client).token
        auth_header = 'Bearer ' + access_token

        # Data should be returned if the user is authorized.
        response = self.http_get(reverse(self.view), HTTP_AUTHORIZATION=auth_header)
        self.assertEqual(response.status_code, 200)

        url = "{}?course_id={}".format(reverse(self.view), self.course_id)
        response = self.http_get(url, HTTP_AUTHORIZATION=auth_header)
        self.assertEqual(response.status_code, 200)
        data = response.data['results']
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], self.course.display_name)

        # The view should return an empty list if the user cannot access any courses.
        url = "{}?course_id={}".format(reverse(self.view), unicode(self.empty_course.id))
        response = self.http_get(url, HTTP_AUTHORIZATION=auth_header)
        self.assertEqual(response.status_code, 200)
        self.assertDictContainsSubset({'count': 0, u'results': []}, response.data)

    def test_course_error(self):
        """
        Ensure the view still returns results even if get_courses() returns an ErrorDescriptor. The ErrorDescriptor
        should be filtered out.
        """

        error_descriptor = ErrorDescriptor.from_xml(
            '<course></course>',
            get_test_system(),
            CourseLocationManager(CourseLocator(org='org', course='course', run='run')),
            None
        )

        descriptors = [error_descriptor, self.empty_course, self.course]

        with patch('xmodule.modulestore.mixed.MixedModuleStore.get_courses', Mock(return_value=descriptors)):
            self.test_get()


class CourseDetailTests(CourseDetailTestMixin, CourseViewTestsMixin, ModuleStoreTestCase):
    view = 'course_structure_api:v0:detail'

    def test_get(self):
        response = super(CourseDetailTests, self).test_get()
        self.assertValidResponseCourse(response.data, self.course)


class CourseStructureTests(CourseDetailTestMixin, CourseViewTestsMixin, ModuleStoreTestCase):
    view = 'course_structure_api:v0:structure'

    def setUp(self):
        super(CourseStructureTests, self).setUp()

        # Ensure course structure exists for the course
        update_course_structure(unicode(self.course.id))

    def test_get(self):
        """
        If the course structure exists in the database, the view should return the data. Otherwise, the view should
        initiate an asynchronous course structure generation and return a 503.
        """

        # Attempt to retrieve data for a course without stored structure
        CourseStructure.objects.all().delete()
        self.assertFalse(CourseStructure.objects.filter(course_id=self.course.id).exists())
        response = self.http_get_for_course()
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response['Retry-After'], '120')

        # Course structure generation shouldn't take long. Generate the data and try again.
        self.assertTrue(CourseStructure.objects.filter(course_id=self.course.id).exists())
        response = self.http_get_for_course()
        self.assertEqual(response.status_code, 200)

        blocks = {}

        def add_block(xblock):
            children = xblock.get_children()
            blocks[unicode(xblock.location)] = {
                u'id': unicode(xblock.location),
                u'type': xblock.category,
                u'parent': None,
                u'display_name': xblock.display_name,
                u'format': xblock.format,
                u'graded': xblock.graded,
                u'children': [unicode(child.location) for child in children]
            }

            for child in children:
                add_block(child)

        course = self.store.get_course(self.course.id, depth=None)
        add_block(course)

        expected = {
            u'root': unicode(self.course.location),
            u'blocks': blocks
        }

        self.maxDiff = None
        self.assertDictEqual(response.data, expected)


class CourseGradingPolicyTests(CourseDetailTestMixin, CourseViewTestsMixin, ModuleStoreTestCase):
    view = 'course_structure_api:v0:grading_policy'

    def test_get(self):
        """
        The view should return grading policy for a course.
        """
        response = super(CourseGradingPolicyTests, self).test_get()

        expected = [
            {
                "count": 24,
                "weight": 0.2,
                "assignment_type": "Homework",
                "dropped": 0
            },
            {
                "count": 4,
                "weight": 0.8,
                "assignment_type": "Exam",
                "dropped": 0
            }
        ]
        self.assertListEqual(response.data, expected)


#####################################################################################
#
# The following Mixins/Classes collectively test the CourseBlocksAndNavigation view.
#
# The class hierarchy is:
#
#      ----------------->  CourseBlocksOrNavigationTestMixin  <--------------
#      |                                   ^                                |
#      |                                   |                                |
#      |        CourseNavigationTestMixin  |   CourseBlocksTestMixin        |
#      |          ^                  ^     |    ^               ^           |
#      |          |                  |     |    |               |           |
#      |          |                  |     |    |               |           |
#   CourseNavigationTests   CourseBlocksAndNavigationTests   CourseBlocksTests
#
#
# Each Test Mixin is an abstract class that implements tests specific to its
# corresponding functionality.
#
# The concrete Test classes are expected to define the following class fields:
#
#   block_navigation_view_type - The view's name as it should be passed to the django
#       reverse method.
#   container_fields - A list of fields that are expected to be included in the view's
#       response for all container block types.
#   block_fields - A list of fields that are expected to be included in the view's
#       response for all block types.
#
######################################################################################


class CourseBlocksOrNavigationTestMixin(CourseDetailTestMixin, CourseViewTestsMixin):
    """
    A Mixin class for testing all views related to Course blocks and/or navigation.
    """
    __metaclass__ = ABCMeta

    view_supports_debug_mode = False

    def setUp(self):
        """
        Override the base `setUp` method to enroll the user in the course, since these views
        require enrollment for non-staff users.
        """
        super(CourseBlocksOrNavigationTestMixin, self).setUp()
        CourseEnrollmentFactory(user=self.user, course_id=self.course.id)

    def create_user(self):
        """
        Override the base `create_user` method to test with non-staff users for these views.
        """
        self.user = UserFactory.create()

    @property
    def view(self):
        """
        Returns the name of the view for testing to use in the django `reverse` call.
        """
        return 'course_structure_api:v0:' + self.block_navigation_view_type

    def test_get(self):
        with check_mongo_calls(3):
            response = super(CourseBlocksOrNavigationTestMixin, self).test_get()

        # verify root element
        self.assertIn('root', response.data)
        root_string = unicode(self.course.location)
        self.assertEquals(response.data['root'], root_string)

        # verify ~blocks element
        self.assertTrue(self.block_navigation_view_type in response.data)
        blocks = response.data[self.block_navigation_view_type]

        # verify number of blocks
        self.assertEquals(len(blocks), 4)

        # verify fields in blocks
        for field, block in product(self.block_fields, blocks.values()):
            self.assertIn(field, block)

        # verify container fields in container blocks
        for field in self.container_fields:
            self.assertIn(field, blocks[root_string])

    def test_parse_error(self):
        """
        Verifies the view returns a 400 when a query parameter is incorrectly formatted.
        """
        response = self.http_get_for_course(data={'block_json': 'incorrect'})
        self.assertEqual(response.status_code, 400)

    def test_no_access_to_block(self):
        """
        Verifies the view returns only the top-level course block, excluding the sequential block
        and its descendants when the user does not have access to the sequential.
        """
        self.sequential.visible_to_staff_only = True
        modulestore().update_item(self.sequential, self.user.id)

        response = super(CourseBlocksOrNavigationTestMixin, self).test_get()
        self.assertEquals(len(response.data[self.block_navigation_view_type]), 1)


class CourseBlocksTestMixin(object):
    """
    A Mixin class for testing all views related to Course blocks.
    """
    __metaclass__ = ABCMeta

    view_supports_debug_mode = False
    block_fields = ['id', 'type', 'display_name', 'web_url', 'block_url', 'graded', 'format']

    def test_block_json(self):
        """
        Verifies the view's response when the block_json data is requested.
        """
        response = self.http_get_for_course(
            data={'block_json': '{"video":{"profiles":["mobile_low"]}}'}
        )
        self.assertEquals(response.status_code, 200)
        video_block = response.data[self.block_navigation_view_type][unicode(self.video.location)]
        self.assertIn('block_json', video_block)

    def test_block_count(self):
        """
        Verifies the view's response when the block_count data is requested.
        """
        response = self.http_get_for_course(
            data={'block_count': 'problem'}
        )
        self.assertEquals(response.status_code, 200)
        root_block = response.data[self.block_navigation_view_type][unicode(self.course.location)]
        self.assertIn('block_count', root_block)
        self.assertIn('problem', root_block['block_count'])
        self.assertEquals(root_block['block_count']['problem'], 1)


class CourseNavigationTestMixin(object):
    """
    A Mixin class for testing all views related to Course navigation.
    """
    __metaclass__ = ABCMeta

    def test_depth_zero(self):
        """
        Tests that all descendants are bundled into the root block when the navigation_depth is set to 0.
        """
        response = self.http_get_for_course(
            data={'navigation_depth': '0'}
        )
        root_block = response.data[self.block_navigation_view_type][unicode(self.course.location)]
        self.assertIn('descendants', root_block)
        self.assertEquals(len(root_block['descendants']), 3)

    def test_depth(self):
        """
        Tests that all container blocks have descendants listed in their data.
        """
        response = self.http_get_for_course()

        container_descendants = (
            (self.course.location, 1),
            (self.sequential.location, 2),
        )
        for container_location, expected_num_descendants in container_descendants:
            block = response.data[self.block_navigation_view_type][unicode(container_location)]
            self.assertIn('descendants', block)
            self.assertEquals(len(block['descendants']), expected_num_descendants)


class CourseBlocksTests(CourseBlocksOrNavigationTestMixin, CourseBlocksTestMixin, ModuleStoreTestCase):
    """
    A Test class for testing the Course 'blocks' view.
    """
    block_navigation_view_type = 'blocks'
    container_fields = ['children']


class CourseNavigationTests(CourseBlocksOrNavigationTestMixin, CourseNavigationTestMixin, ModuleStoreTestCase):
    """
    A Test class for testing the Course 'navigation' view.
    """
    block_navigation_view_type = 'navigation'
    container_fields = ['descendants']
    block_fields = []


class CourseBlocksAndNavigationTests(CourseBlocksOrNavigationTestMixin, CourseBlocksTestMixin,
                                     CourseNavigationTestMixin, ModuleStoreTestCase):
    """
    A Test class for testing the Course 'blocks+navigation' view.
    """
    block_navigation_view_type = 'blocks+navigation'
    container_fields = ['children', 'descendants']
