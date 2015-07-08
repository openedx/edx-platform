""" Commerce API v1 view tests. """
import json

import ddt
from django.conf import settings
from django.contrib.auth.models import Permission
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from course_modes.models import CourseMode
from student.tests.factories import UserFactory

PASSWORD = 'test'
JSON_CONTENT_TYPE = 'application/json'


class CourseApiViewTestMixin(object):
    """ Mixin for CourseApi views.

    Automatically creates a course and CourseMode.
    """

    def setUp(self):
        super(CourseApiViewTestMixin, self).setUp()
        self.course = CourseFactory.create()
        self.course_mode = CourseMode.objects.create(course_id=self.course.id, mode_slug=u'verified', min_price=100,
                                                     currency=u'USD', sku=u'ABC123')

    @staticmethod
    def _serialize_course_mode(course_mode):
        """ Serialize a CourseMode to a dict. """
        return {
            u'name': course_mode.mode_slug,
            u'currency': course_mode.currency,
            u'price': course_mode.min_price,
            u'sku': course_mode.sku
        }


class CourseListViewTests(CourseApiViewTestMixin, ModuleStoreTestCase):
    """ Tests for CourseListView. """
    path = reverse('commerce_api:v1:courses:list')

    def test_authentication_required(self):
        """ Verify only authenticated users can access the view. """
        self.client.logout()
        response = self.client.get(self.path, content_type=JSON_CONTENT_TYPE)
        self.assertEqual(response.status_code, 401)

    def test_list(self):
        """ Verify the view lists the available courses and modes. """
        user = UserFactory.create()
        self.client.login(username=user.username, password=PASSWORD)
        response = self.client.get(self.path, content_type=JSON_CONTENT_TYPE)

        self.assertEqual(response.status_code, 200)
        actual = json.loads(response.content)
        expected = [
            {
                u'id': unicode(self.course.id),
                u'modes': [self._serialize_course_mode(self.course_mode)]
            }
        ]
        self.assertListEqual(actual, expected)


@ddt.ddt
class CourseRetrieveUpdateViewTests(CourseApiViewTestMixin, ModuleStoreTestCase):
    """ Tests for CourseRetrieveUpdateView. """

    def setUp(self):
        super(CourseRetrieveUpdateViewTests, self).setUp()
        self.path = reverse('commerce_api:v1:courses:retrieve_update', args=[unicode(self.course.id)])
        self.user = UserFactory.create()
        self.client.login(username=self.user.username, password=PASSWORD)

    @ddt.data('get', 'post', 'put')
    def test_authentication_required(self, method):
        """ Verify only authenticated users can access the view. """
        self.client.logout()
        response = getattr(self.client, method)(self.path, content_type=JSON_CONTENT_TYPE)
        self.assertEqual(response.status_code, 401)

    @ddt.data('post', 'put')
    def test_authorization_required(self, method):
        """ Verify create/edit operations require appropriate permissions. """
        response = getattr(self.client, method)(self.path, content_type=JSON_CONTENT_TYPE)
        self.assertEqual(response.status_code, 403)

    def test_retrieve(self):
        """ Verify the view displays info for a given course. """
        response = self.client.get(self.path, content_type=JSON_CONTENT_TYPE)
        self.assertEqual(response.status_code, 200)

        actual = json.loads(response.content)
        expected = {
            u'id': unicode(self.course.id),
            u'modes': [self._serialize_course_mode(self.course_mode)]
        }
        self.assertEqual(actual, expected)

    def test_retrieve_invalid_course(self):
        """ The view should return HTTP 404 when retrieving data for a course that does not exist. """
        path = reverse('commerce_api:v1:courses:retrieve_update', args=['a/b/c'])
        response = self.client.get(path, content_type=JSON_CONTENT_TYPE)
        self.assertEqual(response.status_code, 404)

    def test_update(self):
        """ Verify the view supports updating a course. """
        permission = Permission.objects.get(name='Can change course mode')
        self.user.user_permissions.add(permission)
        expected_course_mode = CourseMode(mode_slug=u'verified', min_price=200, currency=u'USD', sku=u'ABC123')
        expected = {
            u'id': unicode(self.course.id),
            u'modes': [self._serialize_course_mode(expected_course_mode)]
        }
        response = self.client.put(self.path, json.dumps(expected), content_type=JSON_CONTENT_TYPE)
        self.assertEqual(response.status_code, 200)

        actual = json.loads(response.content)
        self.assertEqual(actual, expected)

    def test_update_overwrite(self):
        """ Verify that data submitted via PUT overwrites/deletes modes that are
        not included in the body of the request. """
        permission = Permission.objects.get(name='Can change course mode')
        self.user.user_permissions.add(permission)

        course_id = unicode(self.course.id)
        expected = {
            u'id': course_id,
            u'modes': [self._serialize_course_mode(
                CourseMode(mode_slug=u'credit', min_price=500, currency=u'USD', sku=u'ABC123')), ]
        }
        path = reverse('commerce_api:v1:courses:retrieve_update', args=[course_id])
        response = self.client.put(path, json.dumps(expected), content_type=JSON_CONTENT_TYPE)
        self.assertEqual(response.status_code, 200)
        actual = json.loads(response.content)
        self.assertEqual(actual, expected)

        # The existing CourseMode should have been removed.
        self.assertFalse(CourseMode.objects.filter(id=self.course_mode.id).exists())

    def assert_can_create_course(self, **request_kwargs):
        """ Verify a course can be created by the view. """
        course = CourseFactory.create()
        course_id = unicode(course.id)
        expected = {
            u'id': course_id,
            u'modes': [
                self._serialize_course_mode(
                    CourseMode(mode_slug=u'verified', min_price=150, currency=u'USD', sku=u'ABC123')),
                self._serialize_course_mode(
                    CourseMode(mode_slug=u'honor', min_price=0, currency=u'USD', sku=u'DEADBEEF')),
            ]
        }
        path = reverse('commerce_api:v1:courses:retrieve_update', args=[course_id])
        response = self.client.put(path, json.dumps(expected), content_type=JSON_CONTENT_TYPE, **request_kwargs)
        self.assertEqual(response.status_code, 201)
        actual = json.loads(response.content)
        self.assertEqual(actual, expected)

    def test_create_with_permissions(self):
        """ Verify the view supports creating a course as a user with the appropriate permissions. """
        permissions = Permission.objects.filter(name__in=('Can add course mode', 'Can change course mode'))
        for permission in permissions:
            self.user.user_permissions.add(permission)

        self.assert_can_create_course()

    @override_settings(EDX_API_KEY='edx')
    def test_create_with_api_key(self):
        """ Verify the view supports creating a course when authenticated with the API header key. """
        self.client.logout()
        self.assert_can_create_course(HTTP_X_EDX_API_KEY=settings.EDX_API_KEY)
