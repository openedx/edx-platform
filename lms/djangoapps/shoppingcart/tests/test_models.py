"""
Tests for the Shopping Cart Models
"""

from factory import DjangoModelFactory
from mock import patch
from django.core import mail
from django.conf import settings
from django.db import DatabaseError
from django.test import TestCase
from django.test.utils import override_settings

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from courseware.tests.tests import TEST_DATA_MONGO_MODULESTORE
from shoppingcart.models import Order, OrderItem, CertificateItem, InvalidCartItem, PaidCourseRegistration
from student.tests.factories import UserFactory
from student.models import CourseEnrollment
from course_modes.models import CourseMode
from shoppingcart.exceptions import PurchasedCallbackException


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class OrderTest(ModuleStoreTestCase):
    def setUp(self):
        self.user = UserFactory.create()
        self.course_id = "org/test/Test_Course"
        CourseFactory.create(org='org', number='test', display_name='Test Course')
        for i in xrange(1, 5):
            CourseFactory.create(org='org', number='test', display_name='Test Course {0}'.format(i))
        self.cost = 40

    def test_get_cart_for_user(self):
        # create a cart
        cart = Order.get_cart_for_user(user=self.user)
        # add something to it
        CertificateItem.add_to_order(cart, self.course_id, self.cost, 'honor')
        # should return the same cart
        cart2 = Order.get_cart_for_user(user=self.user)
        self.assertEquals(cart2.orderitem_set.count(), 1)

    def test_cart_clear(self):
        cart = Order.get_cart_for_user(user=self.user)
        CertificateItem.add_to_order(cart, self.course_id, self.cost, 'honor')
        CertificateItem.add_to_order(cart, 'org/test/Test_Course_1', self.cost, 'honor')
        self.assertEquals(cart.orderitem_set.count(), 2)
        cart.clear()
        self.assertEquals(cart.orderitem_set.count(), 0)

    def test_add_item_to_cart_currency_match(self):
        cart = Order.get_cart_for_user(user=self.user)
        CertificateItem.add_to_order(cart, self.course_id, self.cost, 'honor', currency='eur')
        # verify that a new item has been added
        self.assertEquals(cart.orderitem_set.count(), 1)
        # verify that the cart's currency was updated
        self.assertEquals(cart.currency, 'eur')
        with self.assertRaises(InvalidCartItem):
            CertificateItem.add_to_order(cart, self.course_id, self.cost, 'honor', currency='usd')
        # assert that this item did not get added to the cart
        self.assertEquals(cart.orderitem_set.count(), 1)

    def test_total_cost(self):
        cart = Order.get_cart_for_user(user=self.user)
        # add items to the order
        course_costs = [('org/test/Test_Course_1', 30),
                        ('org/test/Test_Course_2', 40),
                        ('org/test/Test_Course_3', 10),
                        ('org/test/Test_Course_4', 20)]
        for course, cost in course_costs:
            CertificateItem.add_to_order(cart, course, cost, 'honor')
        self.assertEquals(cart.orderitem_set.count(), len(course_costs))
        self.assertEquals(cart.total_cost, sum(cost for _course, cost in course_costs))

    def test_purchase(self):
        # This test is for testing the subclassing functionality of OrderItem, but in
        # order to do this, we end up testing the specific functionality of
        # CertificateItem, which is not quite good unit test form. Sorry.
        cart = Order.get_cart_for_user(user=self.user)
        self.assertFalse(CourseEnrollment.is_enrolled(self.user, self.course_id))
        item = CertificateItem.add_to_order(cart, self.course_id, self.cost, 'honor')
        # course enrollment object should be created but still inactive
        self.assertFalse(CourseEnrollment.is_enrolled(self.user, self.course_id))
        cart.purchase()
        self.assertTrue(CourseEnrollment.is_enrolled(self.user, self.course_id))

        # test e-mail sending
        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals('Order Payment Confirmation', mail.outbox[0].subject)
        self.assertIn(settings.PAYMENT_SUPPORT_EMAIL, mail.outbox[0].body)
        self.assertIn(unicode(cart.total_cost), mail.outbox[0].body)
        self.assertIn(item.additional_instruction_text, mail.outbox[0].body)

    def test_purchase_item_failure(self):
        # once again, we're testing against the specific implementation of
        # CertificateItem
        cart = Order.get_cart_for_user(user=self.user)
        CertificateItem.add_to_order(cart, self.course_id, self.cost, 'honor')
        with patch('shoppingcart.models.CertificateItem.save', side_effect=DatabaseError):
            with self.assertRaises(DatabaseError):
                cart.purchase()
                # verify that we rolled back the entire transaction
                self.assertFalse(CourseEnrollment.is_enrolled(self.user, self.course_id))
                # verify that e-mail wasn't sent
                self.assertEquals(len(mail.outbox), 0)

    def purchase_with_data(self, cart):
        """ purchase a cart with billing information """
        CertificateItem.add_to_order(cart, self.course_id, self.cost, 'honor')
        cart.purchase(
            first='John',
            last='Smith',
            street1='11 Cambridge Center',
            street2='Suite 101',
            city='Cambridge',
            state='MA',
            postalcode='02412',
            country='US',
            ccnum='1111',
            cardtype='001',
        )

    @patch.dict(settings.MITX_FEATURES, {'STORE_BILLING_INFO': True})
    def test_billing_info_storage_on(self):
        cart = Order.get_cart_for_user(self.user)
        self.purchase_with_data(cart)
        self.assertNotEqual(cart.bill_to_first, '')
        self.assertNotEqual(cart.bill_to_last, '')
        self.assertNotEqual(cart.bill_to_street1, '')
        self.assertNotEqual(cart.bill_to_street2, '')
        self.assertNotEqual(cart.bill_to_postalcode, '')
        self.assertNotEqual(cart.bill_to_ccnum, '')
        self.assertNotEqual(cart.bill_to_cardtype, '')
        self.assertNotEqual(cart.bill_to_city, '')
        self.assertNotEqual(cart.bill_to_state, '')
        self.assertNotEqual(cart.bill_to_country, '')

    @patch.dict(settings.MITX_FEATURES, {'STORE_BILLING_INFO': False})
    def test_billing_info_storage_off(self):
        cart = Order.get_cart_for_user(self.user)
        cart = Order.get_cart_for_user(self.user)
        self.purchase_with_data(cart)
        self.assertNotEqual(cart.bill_to_first, '')
        self.assertNotEqual(cart.bill_to_last, '')
        self.assertNotEqual(cart.bill_to_city, '')
        self.assertNotEqual(cart.bill_to_state, '')
        self.assertNotEqual(cart.bill_to_country, '')
        self.assertNotEqual(cart.bill_to_postalcode, '')
        # things we expect to be missing when the feature is off
        self.assertEqual(cart.bill_to_street1, '')
        self.assertEqual(cart.bill_to_street2, '')
        self.assertEqual(cart.bill_to_ccnum, '')
        self.assertEqual(cart.bill_to_cardtype, '')


class OrderItemTest(TestCase):
    def setUp(self):
        self.user = UserFactory.create()

    def test_orderItem_purchased_callback(self):
        """
        This tests that calling purchased_callback on the base OrderItem class raises NotImplementedError
        """
        item = OrderItem(user=self.user, order=Order.get_cart_for_user(self.user))
        with self.assertRaises(NotImplementedError):
            item.purchased_callback()


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class PaidCourseRegistrationTest(ModuleStoreTestCase):
    def setUp(self):
        self.user = UserFactory.create()
        self.course_id = "MITx/999/Robot_Super_Course"
        self.cost = 40
        self.course = CourseFactory.create(org='MITx', number='999', display_name='Robot Super Course')
        self.course_mode = CourseMode(course_id=self.course_id,
                                      mode_slug="honor",
                                      mode_display_name="honor cert",
                                      min_price=self.cost)
        self.course_mode.save()
        self.cart = Order.get_cart_for_user(self.user)

    def test_add_to_order(self):
        reg1 = PaidCourseRegistration.add_to_order(self.cart, self.course_id)

        self.assertEqual(reg1.unit_cost, self.cost)
        self.assertEqual(reg1.line_cost, self.cost)
        self.assertEqual(reg1.unit_cost, self.course_mode.min_price)
        self.assertEqual(reg1.mode, "honor")
        self.assertEqual(reg1.user, self.user)
        self.assertEqual(reg1.status, "cart")
        self.assertTrue(PaidCourseRegistration.part_of_order(self.cart, self.course_id))
        self.assertFalse(PaidCourseRegistration.part_of_order(self.cart, self.course_id + "abcd"))
        self.assertEqual(self.cart.total_cost, self.cost)

    def test_add_with_default_mode(self):
        """
        Tests add_to_cart where the mode specified in the argument is NOT in the database
        and NOT the default "honor".  In this case it just adds the user in the CourseMode.DEFAULT_MODE, 0 price
        """
        reg1 = PaidCourseRegistration.add_to_order(self.cart, self.course_id, mode_slug="DNE")

        self.assertEqual(reg1.unit_cost, 0)
        self.assertEqual(reg1.line_cost, 0)
        self.assertEqual(reg1.mode, "honor")
        self.assertEqual(reg1.user, self.user)
        self.assertEqual(reg1.status, "cart")
        self.assertEqual(self.cart.total_cost, 0)
        self.assertTrue(PaidCourseRegistration.part_of_order(self.cart, self.course_id))

    def test_purchased_callback(self):
        reg1 = PaidCourseRegistration.add_to_order(self.cart, self.course_id)
        self.cart.purchase()
        self.assertTrue(CourseEnrollment.is_enrolled(self.user, self.course_id))
        reg1 = PaidCourseRegistration.objects.get(id=reg1.id)  # reload from DB to get side-effect
        self.assertEqual(reg1.status, "purchased")

    def test_purchased_callback_exception(self):
        reg1 = PaidCourseRegistration.add_to_order(self.cart, self.course_id)
        reg1.course_id = "changedforsomereason"
        reg1.save()
        with self.assertRaises(PurchasedCallbackException):
            reg1.purchased_callback()
        self.assertFalse(CourseEnrollment.is_enrolled(self.user, self.course_id))

        reg1.course_id = "abc/efg/hij"
        reg1.save()
        with self.assertRaises(PurchasedCallbackException):
            reg1.purchased_callback()
        self.assertFalse(CourseEnrollment.is_enrolled(self.user, self.course_id))


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class CertificateItemTest(ModuleStoreTestCase):
    """
    Tests for verifying specific CertificateItem functionality
    """
    def setUp(self):
        self.user = UserFactory.create()
        self.course_id = "org/test/Test_Course"
        self.cost = 40
        CourseFactory.create(org='org', number='test', run='course', display_name='Test Course')
        course_mode = CourseMode(course_id=self.course_id,
                                 mode_slug="honor",
                                 mode_display_name="honor cert",
                                 min_price=self.cost)
        course_mode.save()
        course_mode = CourseMode(course_id=self.course_id,
                                 mode_slug="verified",
                                 mode_display_name="verified cert",
                                 min_price=self.cost)
        course_mode.save()

    def test_existing_enrollment(self):
        CourseEnrollment.enroll(self.user, self.course_id)
        cart = Order.get_cart_for_user(user=self.user)
        CertificateItem.add_to_order(cart, self.course_id, self.cost, 'verified')
        # verify that we are still enrolled
        self.assertTrue(CourseEnrollment.is_enrolled(self.user, self.course_id))
        cart.purchase()
        enrollment = CourseEnrollment.objects.get(user=self.user, course_id=self.course_id)
        self.assertEquals(enrollment.mode, u'verified')

    def test_single_item_template(self):
        cart = Order.get_cart_for_user(user=self.user)
        cert_item = CertificateItem.add_to_order(cart, self.course_id, self.cost, 'verified')

        self.assertEquals(cert_item.single_item_receipt_template,
                          'shoppingcart/verified_cert_receipt.html')

        cert_item = CertificateItem.add_to_order(cart, self.course_id, self.cost, 'honor')
        self.assertEquals(cert_item.single_item_receipt_template,
                          'shoppingcart/receipt.html')
