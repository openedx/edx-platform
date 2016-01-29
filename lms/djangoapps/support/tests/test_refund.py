"""
Tests for refunds on the support dashboard

DEPRECATION WARNING:
This test suite is deliberately separate from the other view tests
so we can easily deprecate it once the transition from shoppingcart
to the E-Commerce service is complete.

"""
import datetime

from django.test.client import Client

from course_modes.models import CourseMode
from shoppingcart.models import CertificateItem, Order
from student.models import CourseEnrollment
from student.roles import SupportStaffRole
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


class RefundTests(ModuleStoreTestCase):
    """
    Tests for the manual refund page
    """
    def setUp(self):
        super(RefundTests, self).setUp()

        self.course = CourseFactory.create(
            org='testorg', number='run1', display_name='refundable course'
        )
        self.course_id = self.course.location.course_key
        self.client = Client()
        self.admin = UserFactory.create(
            username='test_admin',
            email='test_admin+support@edx.org',
            password='foo'
        )
        SupportStaffRole().add_users(self.admin)
        self.client.login(username=self.admin.username, password='foo')

        self.student = UserFactory.create(
            username='student',
            email='student+refund@edx.org'
        )
        self.course_mode = CourseMode.objects.get_or_create(
            course_id=self.course_id,
            mode_slug='verified',
            min_price=1
        )[0]

        self.order = None
        self.form_pars = {'course_id': str(self.course_id), 'user': self.student.email}

    def tearDown(self):
        self.course_mode.delete()
        Order.objects.filter(user=self.student).delete()
        super(RefundTests, self).tearDown()

    def _enroll(self, purchase=True):
        # pylint: disable=missing-docstring
        CourseEnrollment.enroll(self.student, self.course_id, self.course_mode.mode_slug)
        if purchase:
            self.order = Order.get_cart_for_user(self.student)
            CertificateItem.add_to_order(self.order, self.course_id, 1, self.course_mode.mode_slug)
            self.order.purchase()
        self.course_mode.expiration_datetime = datetime.datetime(1983, 4, 6)
        self.course_mode.save()

    def test_support_access(self):
        response = self.client.get('/support/')
        self.assertTrue(response.status_code, 200)
        self.assertContains(response, 'Manual Refund')
        response = self.client.get('/support/refund/')
        self.assertTrue(response.status_code, 200)

        # users without the permission can't access support
        SupportStaffRole().remove_users(self.admin)
        response = self.client.get('/support/')
        self.assertTrue(response.status_code, 302)

        response = self.client.get('/support/refund/')
        self.assertTrue(response.status_code, 302)

    def test_bad_courseid(self):
        response = self.client.post('/support/refund/', {'course_id': 'foo', 'user': self.student.email})
        self.assertContains(response, 'Invalid course id')

    def test_bad_user(self):
        response = self.client.post('/support/refund/', {'course_id': str(self.course_id), 'user': 'unknown@foo.com'})
        self.assertContains(response, 'User not found')

    def test_not_refundable(self):
        self._enroll()
        self.course_mode.expiration_datetime = datetime.datetime(2033, 4, 6)
        self.course_mode.save()
        response = self.client.post('/support/refund/', self.form_pars)
        self.assertContains(response, 'not past the refund window')

    def test_no_order(self):
        self._enroll(purchase=False)
        response = self.client.post('/support/refund/', self.form_pars)
        self.assertContains(response, 'No order found for %s' % self.student.username)

    def test_valid_order(self):
        self._enroll()
        response = self.client.post('/support/refund/', self.form_pars)
        self.assertContains(response, "About to refund this order")
        self.assertContains(response, "enrolled")
        self.assertContains(response, "CertificateItem Status")

    def test_do_refund(self):
        self._enroll()
        pars = self.form_pars
        pars['confirmed'] = 'true'
        response = self.client.post('/support/refund/', pars)
        self.assertTrue(response.status_code, 302)
        response = self.client.get(response.get('location'))  # pylint: disable=maybe-no-member

        self.assertContains(response, "Unenrolled %s from" % self.student)
        self.assertContains(response, "Refunded 1.00 for order id")

        self.assertFalse(CourseEnrollment.is_enrolled(self.student, self.course_id))
