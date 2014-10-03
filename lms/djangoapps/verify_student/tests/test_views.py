# encoding: utf-8
"""


verify_student/start?course_id=MITx/6.002x/2013_Spring # create
              /upload_face?course_id=MITx/6.002x/2013_Spring
              /upload_photo_id
              /confirm # mark_ready()

 ---> To Payment

"""
import json
import mock
import urllib
import decimal
from mock import patch, Mock
import pytz
from datetime import timedelta, datetime

from django.test.client import Client
from django.test import TestCase
from django.test.utils import override_settings
from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase, mixed_store_config
from xmodule.modulestore.tests.factories import CourseFactory
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from student.tests.factories import UserFactory
from student.models import CourseEnrollment
from course_modes.tests.factories import CourseModeFactory
from course_modes.models import CourseMode
from shoppingcart.models import Order, CertificateItem
from verify_student.views import render_to_response
from verify_student.models import SoftwareSecurePhotoVerification
from reverification.tests.factories import MidcourseReverificationWindowFactory


# Since we don't need any XML course fixtures, use a modulestore configuration
# that disables the XML modulestore.
MODULESTORE_CONFIG = mixed_store_config(settings.COMMON_TEST_DATA_ROOT, {}, include_xml=False)


def mock_render_to_response(*args, **kwargs):
    return render_to_response(*args, **kwargs)

render_mock = Mock(side_effect=mock_render_to_response)


class StartView(TestCase):

    def start_url(self, course_id=""):
        return "/verify_student/{0}".format(urllib.quote(course_id))

    def test_start_new_verification(self):
        """
        Test the case where the user has no pending `PhotoVerficiationAttempts`,
        but is just starting their first.
        """
        user = UserFactory.create(username="rusty", password="test")
        self.client.login(username="rusty", password="test")

    def must_be_logged_in(self):
        self.assertHttpForbidden(self.client.get(self.start_url()))


@override_settings(MODULESTORE=MODULESTORE_CONFIG)
class TestCreateOrderView(ModuleStoreTestCase):
    """
    Tests for the create_order view of verified course registration process
    """
    def setUp(self):
        self.user = UserFactory.create(username="rusty", password="test")
        self.client.login(username="rusty", password="test")
        self.course_id = 'Robot/999/Test_Course'
        self.course = CourseFactory.create(org='Robot', number='999', display_name='Test Course')
        verified_mode = CourseMode(
            course_id=SlashSeparatedCourseKey("Robot", "999", 'Test_Course'),
            mode_slug="verified",
            mode_display_name="Verified Certificate",
            min_price=50
        )
        verified_mode.save()
        course_mode_post_data = {
            'certificate_mode': 'Select Certificate',
            'contribution': 50,
            'contribution-other-amt': '',
            'explain': ''
        }
        self.client.post(
            reverse("course_modes_choose", kwargs={'course_id': self.course_id}),
            course_mode_post_data
        )

    def test_invalid_photos_data(self):
        """
        Test that the invalid photo data cannot be submitted
        """
        create_order_post_data = {
            'contribution': 50,
            'course_id': self.course_id,
            'face_image': '',
            'photo_id_image': ''
        }
        response = self.client.post(reverse('verify_student_create_order'), create_order_post_data)
        json_response = json.loads(response.content)
        self.assertFalse(json_response.get('success'))

    @patch.dict(settings.FEATURES, {'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': True})
    def test_invalid_amount(self):
        """
        Test that the user cannot give invalid amount
        """
        create_order_post_data = {
            'contribution': '1.a',
            'course_id': self.course_id,
            'face_image': ',',
            'photo_id_image': ','
        }
        response = self.client.post(reverse('verify_student_create_order'), create_order_post_data)
        self.assertEquals(response.status_code, 400)
        self.assertIn('Selected price is not valid number.', response.content)

    @patch.dict(settings.FEATURES, {'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': True})
    def test_invalid_mode(self):
        """
        Test that the course without verified mode cannot be processed
        """
        course_id = 'Fake/999/Test_Course'
        CourseFactory.create(org='Fake', number='999', display_name='Test Course')
        create_order_post_data = {
            'contribution': '50',
            'course_id': course_id,
            'face_image': ',',
            'photo_id_image': ','
        }
        response = self.client.post(reverse('verify_student_create_order'), create_order_post_data)
        self.assertEquals(response.status_code, 400)
        self.assertIn('This course doesn\'t support verified certificates', response.content)

    @patch.dict(settings.FEATURES, {'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': True})
    def test_create_order_success(self):
        """
        Test that the order is created successfully when given valid data
        """
        create_order_post_data = {
            'contribution': 50,
            'course_id': self.course_id,
            'face_image': ',',
            'photo_id_image': ','
        }
        response = self.client.post(reverse('verify_student_create_order'), create_order_post_data)
        json_response = json.loads(response.content)
        self.assertTrue(json_response.get('success'))
        self.assertIsNotNone(json_response.get('orderNumber'))

        # Verify that the order exists and is configured correctly
        order = Order.objects.get(user=self.user)
        self.assertEqual(order.status, 'paying')
        item = CertificateItem.objects.get(order=order)
        self.assertEqual(item.status, 'paying')
        self.assertEqual(item.course_id, self.course.id)
        self.assertEqual(item.mode, 'verified')


@override_settings(MODULESTORE=MODULESTORE_CONFIG)
class TestVerifyView(ModuleStoreTestCase):
    def setUp(self):
        self.user = UserFactory.create(username="rusty", password="test")
        self.client.login(username="rusty", password="test")
        self.course_key = SlashSeparatedCourseKey('Robot', '999', 'Test_Course')
        CourseFactory.create(org='Robot', number='999', display_name='Test Course')
        verified_mode = CourseMode(course_id=self.course_key,
                                   mode_slug="verified",
                                   mode_display_name="Verified Certificate",
                                   min_price=50,
                                   suggested_prices="50.0,100.0")
        verified_mode.save()

    def test_invalid_course(self):
        fake_course_id = "Robot/999/Fake_Course"
        url = reverse('verify_student_verify',
                      kwargs={"course_id": fake_course_id})
        response = self.client.get(url)
        self.assertEquals(response.status_code, 302)

    def test_valid_course_registration_text(self):
        url = reverse('verify_student_verify',
                      kwargs={"course_id": unicode(self.course_key)})
        response = self.client.get(url)

        self.assertIn("You are registering for", response.content)

    def test_valid_course_upgrade_text(self):
        url = reverse('verify_student_verify',
                      kwargs={"course_id": unicode(self.course_key)})
        response = self.client.get(url, {'upgrade': "True"})
        self.assertIn("You are upgrading your registration for", response.content)

    def test_show_selected_contribution_amount(self):
        # Set the donation amount in the client's session
        session = self.client.session
        session['donation_for_course'] = {
            unicode(self.course_key): decimal.Decimal('1.23')
        }
        session.save()

        # Retrieve the page
        url = reverse('verify_student_verify', kwargs={"course_id": unicode(self.course_key)})
        response = self.client.get(url)

        # Expect that the user's contribution amount is shown on the page
        self.assertContains(response, '1.23')


@override_settings(MODULESTORE=MODULESTORE_CONFIG)
class TestVerifiedView(ModuleStoreTestCase):
    """
    Tests for VerifiedView.
    """
    def setUp(self):
        self.user = UserFactory.create(username="abc", password="test")
        self.client.login(username="abc", password="test")
        self.course = CourseFactory.create(org='MITx', number='999.1x', display_name='Verified Course')
        self.course_id = self.course.id

    def test_verified_course_mode_none(self):
        """
        Test VerifiedView when there is no active verified mode for course.
        """
        url = reverse('verify_student_verified', kwargs={"course_id": self.course_id.to_deprecated_string()})

        verify_mode = CourseMode.mode_for_course(self.course_id, "verified")
        # Verify mode should be None.
        self.assertEquals(verify_mode, None)

        response = self.client.get(url)
        # Status code should be 302.
        self.assertTrue(response.status_code, 302)
        # Location should contains dashboard.
        self.assertIn('dashboard', response._headers.get('location')[1])

    def test_show_selected_contribution_amount(self):
        # Configure the course to have a verified mode
        for mode in ('audit', 'honor', 'verified'):
            CourseModeFactory(mode_slug=mode, course_id=self.course.id)

        # Set the donation amount in the client's session
        session = self.client.session
        session['donation_for_course'] = {
            unicode(self.course_id): decimal.Decimal('1.23')
        }
        session.save()

        # Retrieve the page
        url = reverse('verify_student_verified', kwargs={"course_id": unicode(self.course_id)})
        response = self.client.get(url)

        # Expect that the user's contribution amount is shown on the page
        self.assertContains(response, '1.23')


@override_settings(MODULESTORE=MODULESTORE_CONFIG)
class TestReverifyView(ModuleStoreTestCase):
    """
    Tests for the reverification views

    """
    def setUp(self):
        self.user = UserFactory.create(username="rusty", password="test")
        self.client.login(username="rusty", password="test")
        self.course = CourseFactory.create(org='MITx', number='999', display_name='Robot Super Course')
        self.course_key = self.course.id

    @patch('verify_student.views.render_to_response', render_mock)
    def test_reverify_get(self):
        url = reverse('verify_student_reverify')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        ((_template, context), _kwargs) = render_mock.call_args
        self.assertFalse(context['error'])

    @patch('verify_student.views.render_to_response', render_mock)
    def test_reverify_post_failure(self):
        url = reverse('verify_student_reverify')
        response = self.client.post(url, {'face_image': '',
                                          'photo_id_image': ''})
        self.assertEquals(response.status_code, 200)
        ((template, context), _kwargs) = render_mock.call_args
        self.assertIn('photo_reverification', template)
        self.assertTrue(context['error'])

    @patch.dict(settings.FEATURES, {'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': True})
    def test_reverify_post_success(self):
        url = reverse('verify_student_reverify')
        response = self.client.post(url, {'face_image': ',',
                                          'photo_id_image': ','})
        self.assertEquals(response.status_code, 302)
        try:
            verification_attempt = SoftwareSecurePhotoVerification.objects.get(user=self.user)
            self.assertIsNotNone(verification_attempt)
        except ObjectDoesNotExist:
            self.fail('No verification object generated')
        ((template, context), _kwargs) = render_mock.call_args
        self.assertIn('photo_reverification', template)
        self.assertTrue(context['error'])


@override_settings(MODULESTORE=MODULESTORE_CONFIG)
class TestPhotoVerificationResultsCallback(ModuleStoreTestCase):
    """
    Tests for the results_callback view.
    """
    def setUp(self):
        self.course = CourseFactory.create(org='Robot', number='999', display_name='Test Course')
        self.course_id = self.course.id
        self.user = UserFactory.create()
        self.attempt = SoftwareSecurePhotoVerification(
            status="submitted",
            user=self.user
        )
        self.attempt.save()
        self.receipt_id = self.attempt.receipt_id
        self.client = Client()

    def mocked_has_valid_signature(method, headers_dict, body_dict, access_key, secret_key):
        return True

    def test_invalid_json(self):
        """
        Test for invalid json being posted by software secure.
        """
        data = {"Testing invalid"}
        response = self.client.post(
            reverse('verify_student_results_callback'),
            data=data,
            content_type='application/json',
            HTTP_AUTHORIZATION='test BBBBBBBBBBBBBBBBBBBB: testing',
            HTTP_DATE='testdate'
        )
        self.assertIn('Invalid JSON', response.content)
        self.assertEqual(response.status_code, 400)

    def test_invalid_dict(self):
        """
        Test for invalid dictionary being posted by software secure.
        """
        data = '"\\"Test\\tTesting"'
        response = self.client.post(
            reverse('verify_student_results_callback'),
            data=data,
            content_type='application/json',
            HTTP_AUTHORIZATION='test BBBBBBBBBBBBBBBBBBBB:testing',
            HTTP_DATE='testdate'
        )
        self.assertIn('JSON should be dict', response.content)
        self.assertEqual(response.status_code, 400)

    @mock.patch('verify_student.ssencrypt.has_valid_signature', mock.Mock(side_effect=mocked_has_valid_signature))
    def test_invalid_access_key(self):
        """
        Test for invalid access key.
        """
        data = {
            "EdX-ID": self.receipt_id,
            "Result": "Testing",
            "Reason": "Testing",
            "MessageType": "Testing"
        }
        json_data = json.dumps(data)
        response = self.client.post(
            reverse('verify_student_results_callback'),
            data=json_data,
            content_type='application/json',
            HTTP_AUTHORIZATION='test testing:testing',
            HTTP_DATE='testdate'
        )
        self.assertIn('Access key invalid', response.content)
        self.assertEqual(response.status_code, 400)

    @mock.patch('verify_student.ssencrypt.has_valid_signature', mock.Mock(side_effect=mocked_has_valid_signature))
    def test_wrong_edx_id(self):
        """
        Test for wrong id of Software secure verification attempt.
        """
        data = {
            "EdX-ID": "Invalid-Id",
            "Result": "Testing",
            "Reason": "Testing",
            "MessageType": "Testing"
        }
        json_data = json.dumps(data)
        response = self.client.post(
            reverse('verify_student_results_callback'),
            data=json_data,
            content_type='application/json',
            HTTP_AUTHORIZATION='test BBBBBBBBBBBBBBBBBBBB:testing',
            HTTP_DATE='testdate'
        )
        self.assertIn('edX ID Invalid-Id not found', response.content)
        self.assertEqual(response.status_code, 400)

    @mock.patch('verify_student.ssencrypt.has_valid_signature', mock.Mock(side_effect=mocked_has_valid_signature))
    def test_pass_result(self):
        """
        Test for verification passed.
        """
        data = {
            "EdX-ID": self.receipt_id,
            "Result": "PASS",
            "Reason": "",
            "MessageType": "You have been verified."
        }
        json_data = json.dumps(data)
        response = self.client.post(
            reverse('verify_student_results_callback'), data=json_data,
            content_type='application/json',
            HTTP_AUTHORIZATION='test BBBBBBBBBBBBBBBBBBBB:testing',
            HTTP_DATE='testdate'
        )
        attempt = SoftwareSecurePhotoVerification.objects.get(receipt_id=self.receipt_id)
        self.assertEqual(attempt.status, u'approved')
        self.assertEquals(response.content, 'OK!')

    @mock.patch('verify_student.ssencrypt.has_valid_signature', mock.Mock(side_effect=mocked_has_valid_signature))
    def test_fail_result(self):
        """
        Test for failed verification.
        """
        data = {
            "EdX-ID": self.receipt_id,
            "Result": 'FAIL',
            "Reason": 'Invalid photo',
            "MessageType": 'Your photo doesn\'t meet standards.'
        }
        json_data = json.dumps(data)
        response = self.client.post(
            reverse('verify_student_results_callback'),
            data=json_data,
            content_type='application/json',
            HTTP_AUTHORIZATION='test BBBBBBBBBBBBBBBBBBBB:testing',
            HTTP_DATE='testdate'
        )
        attempt = SoftwareSecurePhotoVerification.objects.get(receipt_id=self.receipt_id)
        self.assertEqual(attempt.status, u'denied')
        self.assertEqual(attempt.error_code, u'Your photo doesn\'t meet standards.')
        self.assertEqual(attempt.error_msg, u'"Invalid photo"')
        self.assertEquals(response.content, 'OK!')

    @mock.patch('verify_student.ssencrypt.has_valid_signature', mock.Mock(side_effect=mocked_has_valid_signature))
    def test_system_fail_result(self):
        """
        Test for software secure result system failure.
        """
        data = {"EdX-ID": self.receipt_id,
                "Result": 'SYSTEM FAIL',
                "Reason": 'Memory overflow',
                "MessageType": 'You must retry the verification.'}
        json_data = json.dumps(data)
        response = self.client.post(
            reverse('verify_student_results_callback'),
            data=json_data,
            content_type='application/json',
            HTTP_AUTHORIZATION='test BBBBBBBBBBBBBBBBBBBB:testing',
            HTTP_DATE='testdate'
        )
        attempt = SoftwareSecurePhotoVerification.objects.get(receipt_id=self.receipt_id)
        self.assertEqual(attempt.status, u'must_retry')
        self.assertEqual(attempt.error_code, u'You must retry the verification.')
        self.assertEqual(attempt.error_msg, u'"Memory overflow"')
        self.assertEquals(response.content, 'OK!')

    @mock.patch('verify_student.ssencrypt.has_valid_signature', mock.Mock(side_effect=mocked_has_valid_signature))
    def test_unknown_result(self):
        """
        test for unknown software secure result
        """
        data = {
            "EdX-ID": self.receipt_id,
            "Result": 'Unknown',
            "Reason": 'Unknown reason',
            "MessageType": 'Unknown message'
        }
        json_data = json.dumps(data)
        response = self.client.post(
            reverse('verify_student_results_callback'),
            data=json_data,
            content_type='application/json',
            HTTP_AUTHORIZATION='test BBBBBBBBBBBBBBBBBBBB:testing',
            HTTP_DATE='testdate'
        )
        self.assertIn('Result Unknown not understood', response.content)

    @mock.patch('verify_student.ssencrypt.has_valid_signature', mock.Mock(side_effect=mocked_has_valid_signature))
    def test_reverification(self):
        """
         Test software secure result for reverification window.
        """
        data = {
            "EdX-ID": self.receipt_id,
            "Result": "PASS",
            "Reason": "",
            "MessageType": "You have been verified."
        }
        window = MidcourseReverificationWindowFactory(course_id=self.course_id)
        self.attempt.window = window
        self.attempt.save()
        json_data = json.dumps(data)
        self.assertEqual(CourseEnrollment.objects.filter(course_id=self.course_id).count(), 0)
        response = self.client.post(
            reverse('verify_student_results_callback'),
            data=json_data,
            content_type='application/json',
            HTTP_AUTHORIZATION='test BBBBBBBBBBBBBBBBBBBB:testing',
            HTTP_DATE='testdate'
        )
        self.assertEquals(response.content, 'OK!')
        self.assertIsNotNone(CourseEnrollment.objects.get(course_id=self.course_id))


@override_settings(MODULESTORE=MODULESTORE_CONFIG)
class TestMidCourseReverifyView(ModuleStoreTestCase):
    """ Tests for the midcourse reverification views """
    def setUp(self):
        self.user = UserFactory.create(username="rusty", password="test")
        self.client.login(username="rusty", password="test")
        self.course_key = SlashSeparatedCourseKey("Robot", "999", "Test_Course")
        CourseFactory.create(org='Robot', number='999', display_name='Test Course')

        patcher = patch('student.models.tracker')
        self.mock_tracker = patcher.start()
        self.addCleanup(patcher.stop)

    @patch('verify_student.views.render_to_response', render_mock)
    def test_midcourse_reverify_get(self):
        url = reverse('verify_student_midcourse_reverify',
                      kwargs={"course_id": self.course_key.to_deprecated_string()})
        response = self.client.get(url)

        self.mock_tracker.emit.assert_any_call(  # pylint: disable=maybe-no-member
            'edx.course.enrollment.mode_changed',
            {
                'user_id': self.user.id,
                'course_id': self.course_key.to_deprecated_string(),
                'mode': "verified",
            }
        )

        # Check that user entering the reverify flow was logged, and that it was the last call
        self.mock_tracker.emit.assert_called_with(  # pylint: disable=maybe-no-member
            'edx.course.enrollment.reverify.started',
            {
                'user_id': self.user.id,
                'course_id': self.course_key.to_deprecated_string(),
                'mode': "verified",
            }
        )

        self.assertTrue(self.mock_tracker.emit.call_count, 2)

        self.mock_tracker.emit.reset_mock()  # pylint: disable=maybe-no-member

        self.assertEquals(response.status_code, 200)
        ((_template, context), _kwargs) = render_mock.call_args
        self.assertFalse(context['error'])

    @patch.dict(settings.FEATURES, {'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': True})
    def test_midcourse_reverify_post_success(self):
        window = MidcourseReverificationWindowFactory(course_id=self.course_key)
        url = reverse('verify_student_midcourse_reverify', kwargs={'course_id': self.course_key.to_deprecated_string()})

        response = self.client.post(url, {'face_image': ','})

        self.mock_tracker.emit.assert_any_call(  # pylint: disable=maybe-no-member
            'edx.course.enrollment.mode_changed',
            {
                'user_id': self.user.id,
                'course_id': self.course_key.to_deprecated_string(),
                'mode': "verified",
            }
        )

        # Check that submission event was logged, and that it was the last call
        self.mock_tracker.emit.assert_called_with(  # pylint: disable=maybe-no-member
            'edx.course.enrollment.reverify.submitted',
            {
                'user_id': self.user.id,
                'course_id': self.course_key.to_deprecated_string(),
                'mode': "verified",
            }
        )

        self.assertTrue(self.mock_tracker.emit.call_count, 2)

        self.mock_tracker.emit.reset_mock()  # pylint: disable=maybe-no-member

        self.assertEquals(response.status_code, 302)
        try:
            verification_attempt = SoftwareSecurePhotoVerification.objects.get(user=self.user, window=window)
            self.assertIsNotNone(verification_attempt)
        except ObjectDoesNotExist:
            self.fail('No verification object generated')

    @patch.dict(settings.FEATURES, {'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': True})
    def test_midcourse_reverify_post_failure_expired_window(self):
        window = MidcourseReverificationWindowFactory(
            course_id=self.course_key,
            start_date=datetime.now(pytz.UTC) - timedelta(days=100),
            end_date=datetime.now(pytz.UTC) - timedelta(days=50),
        )
        url = reverse('verify_student_midcourse_reverify', kwargs={'course_id': self.course_key.to_deprecated_string()})
        response = self.client.post(url, {'face_image': ','})
        self.assertEquals(response.status_code, 302)
        with self.assertRaises(ObjectDoesNotExist):
            SoftwareSecurePhotoVerification.objects.get(user=self.user, window=window)

    @patch('verify_student.views.render_to_response', render_mock)
    def test_midcourse_reverify_dash(self):
        url = reverse('verify_student_midcourse_reverify_dash')
        response = self.client.get(url)
        # not enrolled in any courses
        self.assertEquals(response.status_code, 200)

        enrollment = CourseEnrollment.get_or_create_enrollment(self.user, self.course_key)
        enrollment.update_enrollment(mode="verified", is_active=True)
        MidcourseReverificationWindowFactory(course_id=self.course_key)
        response = self.client.get(url)
        # enrolled in a verified course, and the window is open
        self.assertEquals(response.status_code, 200)


@override_settings(MODULESTORE=MODULESTORE_CONFIG)
class TestReverificationBanner(ModuleStoreTestCase):
    """ Tests for the midcourse reverification  failed toggle banner off """

    @patch.dict(settings.FEATURES, {'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': True})
    def setUp(self):
        self.user = UserFactory.create(username="rusty", password="test")
        self.client.login(username="rusty", password="test")
        self.course_id = 'Robot/999/Test_Course'
        CourseFactory.create(org='Robot', number='999', display_name=u'Test Course é')
        self.window = MidcourseReverificationWindowFactory(course_id=self.course_id)
        url = reverse('verify_student_midcourse_reverify', kwargs={'course_id': self.course_id})
        self.client.post(url, {'face_image': ','})
        photo_verification = SoftwareSecurePhotoVerification.objects.get(user=self.user, window=self.window)
        photo_verification.status = 'denied'
        photo_verification.save()

    def test_banner_display_off(self):
        self.client.post(reverse('verify_student_toggle_failed_banner_off'))
        photo_verification = SoftwareSecurePhotoVerification.objects.get(user=self.user, window=self.window)
        self.assertFalse(photo_verification.display)


@override_settings(MODULESTORE=MODULESTORE_CONFIG)
class TestCreateOrder(ModuleStoreTestCase):
    """ Tests for the create order view. """

    def setUp(self):
        """ Create a user and course. """
        self.user = UserFactory.create(username="test", password="test")
        self.course = CourseFactory.create()
        for mode in ('audit', 'honor', 'verified'):
            CourseModeFactory(mode_slug=mode, course_id=self.course.id)
        self.client.login(username="test", password="test")

    def test_create_order_already_verified(self):
        # Verify the student so we don't need to submit photos
        self._verify_student()

        # Create an order
        url = reverse('verify_student_create_order')
        params = {
            'course_id': unicode(self.course.id),
        }
        response = self.client.post(url, params)
        self.assertEqual(response.status_code, 200)

        # Verify that the information will be sent to the correct callback URL
        # (configured by test settings)
        data = json.loads(response.content)
        self.assertEqual(data['override_custom_receipt_page'], "http://testserver/shoppingcart/postpay_callback/")

        # Verify that the course ID is included in "merchant-defined data"
        self.assertEqual(data['merchant_defined_data1'], unicode(self.course.id))

    def test_create_order_set_donation_amount(self):
        # Verify the student so we don't need to submit photos
        self._verify_student()

        # Create an order
        url = reverse('verify_student_create_order')
        params = {
            'course_id': unicode(self.course.id),
            'contribution': '1.23'
        }
        self.client.post(url, params)

        # Verify that the client's session contains the new donation amount
        self.assertIn('donation_for_course', self.client.session)
        self.assertIn(unicode(self.course.id), self.client.session['donation_for_course'])

        actual_amount = self.client.session['donation_for_course'][unicode(self.course.id)]
        expected_amount = decimal.Decimal('1.23')
        self.assertEqual(actual_amount, expected_amount)

    def _verify_student(self):
        """ Simulate that the student's identity has already been verified. """
        attempt = SoftwareSecurePhotoVerification.objects.create(user=self.user)
        attempt.mark_ready()
        attempt.submit()
        attempt.approve()
