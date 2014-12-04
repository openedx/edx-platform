"""
Run these tests @ Devstack:
    paver test_system -s lms --fasttest --verbose --test_id=lms/djangoapps/course_api
"""
# pylint: disable=missing-docstring,invalid-name,maybe-no-member
from datetime import datetime
import uuid

from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from xmodule.modulestore.tests.django_utils import TEST_DATA_MOCK_MODULESTORE, ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory


TEST_SERVER_HOST = 'http://testserver'
TEST_API_KEY = str(uuid.uuid4())
USER_COUNT = 6
SAMPLE_GRADE_DATA_COUNT = 4

HEADERS = {
    'HTTP_X_EDX_API_KEY': TEST_API_KEY,
}


class TestCourseDataMixin(object):
    """
    Test mixin that generates course data.
    """

    def setUp(self):
        self.create_test_data()

    # pylint: disable=attribute-defined-outside-init
    def create_test_data(self):
        self.INVALID_COURSE_ID = 'foo/bar/baz'
        self.COURSE_NAME = 'An Introduction to API Testing'
        self.COURSE = CourseFactory.create(display_name=self.COURSE_NAME, raw_grader=[
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
        self.COURSE_ID = unicode(self.COURSE.id)

        self.GRADED_CONTENT = ItemFactory.create(
            category="sequential",
            parent_location=self.COURSE.location,
            display_name="Lesson 1",
            format="Homework",
            graded=True
        )

        self.PROBLEM = ItemFactory.create(
            category="problem",
            parent_location=self.GRADED_CONTENT.location,
            display_name="Problem 1"
        )

        self.EMPTY_COURSE = CourseFactory.create(
            start=datetime(2014, 6, 16, 14, 30),
            end=datetime(2015, 1, 16),
            org="MTD"
        )


class CourseViewTestsMixin(TestCourseDataMixin):
    """
    Mixin for course view tests.
    """
    view = None

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

        uri = self.build_absolute_url(reverse('course_api:v0:detail', kwargs={'course_id': unicode(course_key)}))
        self.assertEqual(data['uri'], uri)

    def assertValidResponseContent(self, data, content):
        child = {
            'id': unicode(content.location),
            'category': content.category,
            'name': content.display_name,
            'uri': self.build_absolute_url(reverse('course_api:v0:content:detail',
                                                   kwargs={'course_id': self.COURSE_ID,
                                                           'content_id': content.location}))
        }
        self.assertDictContainsSubset(child, data)

    def http_get(self, uri):
        """Submit an HTTP GET request"""
        response = self.client.get(uri, content_type='application/json', follow=True, **HEADERS)
        return response


class CourseDetailMixin(object):
    """
    Mixin for views utilizing only the course_id kwarg.
    """

    def test_get_invalid_course(self):
        """
        The view should return a 404 if the course ID is invalid.
        """
        response = self.http_get(reverse(self.view, kwargs={'course_id': self.INVALID_COURSE_ID}))
        self.assertEqual(response.status_code, 404)

    def test_get(self):
        """
        The view should return a 200 if the course ID is invalid.
        """
        response = self.http_get(reverse(self.view, kwargs={'course_id': self.COURSE_ID}))
        self.assertEqual(response.status_code, 200)

        # Return the response so child classes do not have to repeat the request.
        return response


@override_settings(MODULESTORE=TEST_DATA_MOCK_MODULESTORE)
@override_settings(EDX_API_KEY=TEST_API_KEY)
class CourseListTests(CourseViewTestsMixin, ModuleStoreTestCase):
    view = 'course_api:v0:list'

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

        self.assertValidResponseCourse(courses[0], self.EMPTY_COURSE)
        self.assertValidResponseCourse(courses[1], self.COURSE)

    def test_get_with_pagination(self):
        """
        The view should return a paginated list of courses.
        """
        url = "{}?page_size=1".format(reverse(self.view))
        response = self.http_get(url)
        self.assertEqual(response.status_code, 200)

        courses = response.data['results']
        self.assertEqual(len(courses), 1)
        self.assertValidResponseCourse(courses[0], self.EMPTY_COURSE)

    def test_get_filtering(self):
        """
        The view should return a list of details for the specified courses.
        """
        url = "{}?course_id={}".format(reverse(self.view), self.COURSE_ID)
        response = self.http_get(url)
        self.assertEqual(response.status_code, 200)

        courses = response.data['results']
        self.assertEqual(len(courses), 1)
        self.assertValidResponseCourse(courses[0], self.COURSE)


@override_settings(MODULESTORE=TEST_DATA_MOCK_MODULESTORE)
@override_settings(EDX_API_KEY=TEST_API_KEY)
class CourseDetailTests(CourseDetailMixin, CourseViewTestsMixin, ModuleStoreTestCase):
    view = 'course_api:v0:detail'

    def test_get(self):
        response = super(CourseDetailTests, self).test_get()
        self.assertValidResponseCourse(response.data, self.COURSE)
        self.assertNotIn('content', response.data)

    def test_get_with_depth(self):
        """
        The endpoint should return child content when the depth querystring parameter is specified.
        """
        url = "{}?depth=3".format(reverse(self.view, kwargs={'course_id': self.COURSE_ID}))
        response = self.http_get(url)
        self.assertEqual(response.status_code, 200)

        children = response.data['content']
        self.assertEqual(len(children), 1)
        self.assertValidResponseContent(children[0], self.GRADED_CONTENT)


@override_settings(MODULESTORE=TEST_DATA_MOCK_MODULESTORE)
@override_settings(EDX_API_KEY=TEST_API_KEY)
class CourseContentListTests(CourseDetailMixin, CourseViewTestsMixin, ModuleStoreTestCase):
    view = 'course_api:v0:content:list'

    def test_get(self):
        response = super(CourseContentListTests, self).test_get()
        self.assertEqual(len(response.data), 1)
        self.assertValidResponseContent(response.data[0], self.GRADED_CONTENT)

    def test_get_with_depth(self):
        """
        The endpoint should return child content when the depth querystring parameter is specified.
        """
        url = "{}?depth=3".format(reverse(self.view, kwargs={'course_id': self.COURSE_ID}))
        response = self.http_get(url)
        self.assertEqual(response.status_code, 200)

        child = response.data[0]
        self.assertValidResponseContent(child, self.GRADED_CONTENT)
        self.assertValidResponseContent(child['children'][0], self.PROBLEM)


@override_settings(MODULESTORE=TEST_DATA_MOCK_MODULESTORE)
@override_settings(EDX_API_KEY=TEST_API_KEY)
class CourseContentDetailTests(CourseDetailMixin, CourseViewTestsMixin, ModuleStoreTestCase):
    view = 'course_api:v0:content:detail'

    def test_get_invalid_course(self):
        """
        The view should return a 404 if the course ID or content ID is invalid.
        """
        url = reverse(self.view, kwargs={'course_id': self.INVALID_COURSE_ID,
                                         'content_id': unicode(self.GRADED_CONTENT.location)})
        response = self.http_get(url)
        self.assertEqual(response.status_code, 404)

        url = reverse(self.view, kwargs={'course_id': self.INVALID_COURSE_ID, 'content_id': 'i4x://foo/bar'})
        response = self.http_get(url)
        self.assertEqual(response.status_code, 404)

    def test_get(self):
        """
        The view should return a 200 if the course ID is invalid.
        """
        url = reverse(self.view,
                      kwargs={'course_id': self.COURSE_ID, 'content_id': unicode(self.GRADED_CONTENT.location)})
        response = self.http_get(url)
        self.assertEqual(response.status_code, 200)
        self.assertValidResponseContent(response.data, self.GRADED_CONTENT)

    def test_get_with_depth(self):
        url = reverse(self.view,
                      kwargs={'course_id': self.COURSE_ID, 'content_id': unicode(self.GRADED_CONTENT.location)})
        url = "{}?depth=3".format(url)
        response = self.http_get(url)
        self.assertEqual(response.status_code, 200)
        self.assertValidResponseContent(response.data, self.GRADED_CONTENT)
        self.assertValidResponseContent(response.data['children'][0], self.PROBLEM)


@override_settings(MODULESTORE=TEST_DATA_MOCK_MODULESTORE)
@override_settings(EDX_API_KEY=TEST_API_KEY)
class CourseGradedContentTests(CourseDetailMixin, CourseViewTestsMixin, ModuleStoreTestCase):
    view = 'course_api:v0:graded_content'

    def test_get(self):
        """
        The view should return graded content for a course.
        """
        response = super(CourseGradedContentTests, self).test_get()

        expected = [
            {
                'id': unicode(self.GRADED_CONTENT.location),
                'name': self.GRADED_CONTENT.display_name,
                'format': 'Homework',
                'problems': [
                    {
                        'id': unicode(self.PROBLEM.location),
                        'name': self.PROBLEM.display_name
                    }
                ]
            }
        ]
        self.assertListEqual(response.data, expected)


@override_settings(MODULESTORE=TEST_DATA_MOCK_MODULESTORE)
@override_settings(EDX_API_KEY=TEST_API_KEY)
class CourseGradingPolicyTests(CourseDetailMixin, CourseViewTestsMixin, ModuleStoreTestCase):
    view = 'course_api:v0:grading_policy'

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
