""" Commerce API v1 view tests. """
from datetime import datetime
import itertools
import json

import ddt
from django.conf import settings
from django.contrib.auth.models import Permission
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings
from edx_rest_api_client import exceptions
from flaky import flaky
from nose.plugins.attrib import attr
import pytz
from rest_framework.utils.encoders import JSONEncoder
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from commerce.tests import TEST_API_URL, TEST_API_SIGNING_KEY
from commerce.tests.mocks import mock_order_endpoint
from commerce.tests.test_views import UserMixin
from course_modes.models import CourseMode
from student.tests.factories import UserFactory
from verify_student.models import VerificationDeadline

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

    @classmethod
    def _serialize_datetime(cls, dt):  # pylint: disable=invalid-name
        """ Serializes datetime values using Django REST Framework's encoder.

        Use this to simplify equality assertions.
        """
        if dt:
            return JSONEncoder().default(dt)
        return None

    @classmethod
    def _serialize_course_mode(cls, course_mode):
        """ Serialize a CourseMode to a dict. """
        return {
            u'name': course_mode.mode_slug,
            u'currency': course_mode.currency.lower(),
            u'price': course_mode.min_price,
            u'sku': course_mode.sku,
            u'expires': cls._serialize_datetime(course_mode.expiration_datetime),
        }

    @classmethod
    def _serialize_course(cls, course, modes=None, verification_deadline=None):
        """ Serializes a course to a Python dict. """
        modes = modes or []
        verification_deadline = verification_deadline or VerificationDeadline.deadline_for_course(course.id)

        return {
            u'id': unicode(course.id),
            u'name': unicode(course.display_name),
            u'verification_deadline': cls._serialize_datetime(verification_deadline),
            u'modes': [cls._serialize_course_mode(mode) for mode in modes]
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
        expected = [self._serialize_course(self.course, [self.course_mode])]
        self.assertListEqual(actual, expected)


@ddt.ddt
class CourseRetrieveUpdateViewTests(CourseApiViewTestMixin, ModuleStoreTestCase):
    """ Tests for CourseRetrieveUpdateView. """

    def setUp(self):
        super(CourseRetrieveUpdateViewTests, self).setUp()
        self.path = reverse('commerce_api:v1:courses:retrieve_update', args=[unicode(self.course.id)])
        self.user = UserFactory.create()
        self.client.login(username=self.user.username, password=PASSWORD)

        permission = Permission.objects.get(name='Can change course mode')
        self.user.user_permissions.add(permission)

    @ddt.data('get', 'post', 'put')
    def test_authentication_required(self, method):
        """ Verify only authenticated users can access the view. """
        self.client.logout()
        response = getattr(self.client, method)(self.path, content_type=JSON_CONTENT_TYPE)
        self.assertEqual(response.status_code, 401)

    @ddt.data('post', 'put')
    def test_authorization_required(self, method):
        self.user.user_permissions.clear()
        """ Verify create/edit operations require appropriate permissions. """
        response = getattr(self.client, method)(self.path, content_type=JSON_CONTENT_TYPE)
        self.assertEqual(response.status_code, 403)

    def test_retrieve(self):
        """ Verify the view displays info for a given course. """
        response = self.client.get(self.path, content_type=JSON_CONTENT_TYPE)
        self.assertEqual(response.status_code, 200)

        actual = json.loads(response.content)
        expected = self._serialize_course(self.course, [self.course_mode])
        self.assertEqual(actual, expected)

    def test_retrieve_invalid_course(self):
        """ The view should return HTTP 404 when retrieving data for a course that does not exist. """
        path = reverse('commerce_api:v1:courses:retrieve_update', args=['a/b/c'])
        response = self.client.get(path, content_type=JSON_CONTENT_TYPE)
        self.assertEqual(response.status_code, 404)

    def _get_update_response_and_expected_data(self, mode_expiration, verification_deadline):
        """ Returns expected data and response for course update. """
        expected_course_mode = CourseMode(
            mode_slug=u'verified',
            min_price=200,
            currency=u'USD',
            sku=u'ABC123',
            expiration_datetime=mode_expiration
        )
        expected = self._serialize_course(self.course, [expected_course_mode], verification_deadline)

        # Sanity check: The API should return HTTP status 200 for updates
        response = self.client.put(self.path, json.dumps(expected), content_type=JSON_CONTENT_TYPE)

        return response, expected

    @flaky  # TODO This test will fail if one of the timestamps (in actual or expected) ends in .000
    def test_update(self):
        """ Verify the view supports updating a course. """
        # Sanity check: Ensure no verification deadline is set
        self.assertIsNone(VerificationDeadline.deadline_for_course(self.course.id))

        # Generate the expected data
        verification_deadline = datetime(year=2020, month=12, day=31, tzinfo=pytz.utc)
        expiration_datetime = datetime.now(pytz.utc)
        response, expected = self._get_update_response_and_expected_data(expiration_datetime, verification_deadline)

        # Sanity check: The API should return HTTP status 200 for updates
        self.assertEqual(response.status_code, 200)

        # Verify the course and modes are returned as JSON
        actual = json.loads(response.content)
        self.assertEqual(actual, expected)

        # Verify the verification deadline is updated
        self.assertEqual(VerificationDeadline.deadline_for_course(self.course.id), verification_deadline)

    def test_update_invalid_dates(self):
        """
        Verify the API does not allow the verification deadline to be set before the course mode upgrade deadlines.
        """
        expiration_datetime = datetime.now(pytz.utc)
        verification_deadline = datetime(year=1915, month=5, day=7, tzinfo=pytz.utc)
        response, __ = self._get_update_response_and_expected_data(expiration_datetime, verification_deadline)
        self.assertEqual(response.status_code, 400)

        # Verify the error message is correct
        actual = json.loads(response.content)
        expected = {
            'non_field_errors': ['Verification deadline must be after the course mode upgrade deadlines.']
        }
        self.assertEqual(actual, expected)

    def test_update_verification_deadline_without_expiring_modes(self):
        """ Verify verification deadline can be set if no course modes expire.

         This accounts for the verified professional mode, which requires verification but should never expire.
        """
        verification_deadline = datetime(year=1915, month=5, day=7, tzinfo=pytz.utc)
        response, __ = self._get_update_response_and_expected_data(None, verification_deadline)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(VerificationDeadline.deadline_for_course(self.course.id), verification_deadline)

    def test_update_overwrite(self):
        """ Verify that data submitted via PUT overwrites/deletes modes that are
        not included in the body of the request. """
        course_id = unicode(self.course.id)
        expected_course_mode = CourseMode(mode_slug=u'credit', min_price=500, currency=u'USD', sku=u'ABC123')
        expected = self._serialize_course(self.course, [expected_course_mode])
        path = reverse('commerce_api:v1:courses:retrieve_update', args=[course_id])
        response = self.client.put(path, json.dumps(expected), content_type=JSON_CONTENT_TYPE)
        self.assertEqual(response.status_code, 200)
        actual = json.loads(response.content)
        self.assertEqual(actual, expected)

        # The existing CourseMode should have been removed.
        self.assertFalse(CourseMode.objects.filter(id=self.course_mode.id).exists())

    @ddt.data(*itertools.product(
        ('honor', 'audit', 'verified', 'professional', 'no-id-professional'),
        (datetime.now(), None),
    ))
    @ddt.unpack
    def test_update_professional_expiration(self, mode_slug, expiration_datetime):
        """ Verify that pushing a mode with a professional certificate and an expiration datetime
        will be rejected (this is not allowed). """
        mode = self._serialize_course_mode(
            CourseMode(
                mode_slug=mode_slug,
                min_price=500,
                currency=u'USD',
                sku=u'ABC123',
                expiration_datetime=expiration_datetime
            )
        )
        course_id = unicode(self.course.id)
        payload = {u'id': course_id, u'modes': [mode]}
        path = reverse('commerce_api:v1:courses:retrieve_update', args=[course_id])

        expected_status = 400 if CourseMode.is_professional_slug(mode_slug) and expiration_datetime is not None else 200
        response = self.client.put(path, json.dumps(payload), content_type=JSON_CONTENT_TYPE)
        self.assertEqual(response.status_code, expected_status)

    def assert_can_create_course(self, **request_kwargs):
        """ Verify a course can be created by the view. """
        course = CourseFactory.create()
        expected_modes = [CourseMode(mode_slug=u'verified', min_price=150, currency=u'USD', sku=u'ABC123'),
                          CourseMode(mode_slug=u'honor', min_price=0, currency=u'USD', sku=u'DEADBEEF')]
        expected = self._serialize_course(course, expected_modes)
        path = reverse('commerce_api:v1:courses:retrieve_update', args=[unicode(course.id)])

        response = self.client.put(path, json.dumps(expected), content_type=JSON_CONTENT_TYPE, **request_kwargs)
        self.assertEqual(response.status_code, 201)

        actual = json.loads(response.content)
        self.assertEqual(actual, expected)

        # Verify the display names are correct
        course_modes = CourseMode.objects.filter(course_id=course.id)
        actual = [course_mode.mode_display_name for course_mode in course_modes]
        self.assertListEqual(actual, ['Verified Certificate', 'Honor Certificate'])

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

    def test_create_with_non_existent_course(self):
        """ Verify the API does not allow data to be created for courses that do not exist. """

        permissions = Permission.objects.filter(name__in=('Can add course mode', 'Can change course mode'))
        for permission in permissions:
            self.user.user_permissions.add(permission)

        expected_modes = [
            CourseMode(
                mode_slug=u'honor',
                min_price=150, currency=u'USD',
                sku=u'ABC123'
            )
        ]

        course_key = 'non/existing/key'

        course_dict = {
            u'id': unicode(course_key),
            u'name': unicode('Non Existing Course'),
            u'verification_deadline': None,
            u'modes': [self._serialize_course_mode(mode) for mode in expected_modes]
        }

        path = reverse('commerce_api:v1:courses:retrieve_update', args=[unicode(course_key)])

        response = self.client.put(path, json.dumps(course_dict), content_type=JSON_CONTENT_TYPE)
        self.assertEqual(response.status_code, 400)

        expected_dict = {
            'id': [
                u'Course {} does not exist.'.format(
                    course_key
                )
            ]
        }
        self.assertDictEqual(expected_dict, json.loads(response.content))


@attr('shard_1')
@override_settings(ECOMMERCE_API_URL=TEST_API_URL, ECOMMERCE_API_SIGNING_KEY=TEST_API_SIGNING_KEY)
class OrderViewTests(UserMixin, TestCase):
    """ Tests for the basket order view. """
    view_name = 'commerce_api:v1:orders:detail'
    ORDER_NUMBER = 'EDX-100001'
    MOCK_ORDER = {'number': ORDER_NUMBER}
    path = reverse(view_name, kwargs={'number': ORDER_NUMBER})

    def setUp(self):
        super(OrderViewTests, self).setUp()
        self._login()

    def test_order_found(self):
        """ If the order is located, the view should pass the data from the API. """
        with mock_order_endpoint(order_number=self.ORDER_NUMBER, response=self.MOCK_ORDER):
            response = self.client.get(self.path)

        self.assertEqual(response.status_code, 200)
        actual = json.loads(response.content)
        self.assertEqual(actual, self.MOCK_ORDER)

    def test_order_not_found(self):
        """ If the order is not found, the view should return a 404. """
        with mock_order_endpoint(order_number=self.ORDER_NUMBER, exception=exceptions.HttpNotFoundError):
            response = self.client.get(self.path)
        self.assertEqual(response.status_code, 404)

    def test_login_required(self):
        """ The view should return 403 if the user is not logged in. """
        self.client.logout()
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 403)
