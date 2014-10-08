"""
Tests for the Shopping Cart Models
"""
import smtplib
from boto.exception import BotoServerError  # this is a super-class of SESError and catches connection errors

from mock import patch, MagicMock, sentinel
from django.core import mail
from django.conf import settings
from django.db import DatabaseError
from django.test import TestCase
from django.test.utils import override_settings
from django.contrib.auth.models import AnonymousUser
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from courseware.tests.tests import TEST_DATA_MONGO_MODULESTORE
from shoppingcart.models import (Order, OrderItem, CertificateItem, InvalidCartItem, PaidCourseRegistration,
                                 OrderItemSubclassPK)
from student.tests.factories import UserFactory
from student.models import CourseEnrollment
from course_modes.models import CourseMode
from shoppingcart.exceptions import PurchasedCallbackException
import pytz
import datetime


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class OrderTest(ModuleStoreTestCase):
    def setUp(self):
        self.user = UserFactory.create()
        course = CourseFactory.create(org='org', number='test', display_name='Test Course')
        self.course_key = course.id
        for i in xrange(1, 5):
            CourseFactory.create(org='org', number='test', display_name='Test Course {0}'.format(i))
        self.cost = 40

    def test_get_cart_for_user(self):
        # create a cart
        cart = Order.get_cart_for_user(user=self.user)
        # add something to it
        CertificateItem.add_to_order(cart, self.course_key, self.cost, 'honor')
        # should return the same cart
        cart2 = Order.get_cart_for_user(user=self.user)
        self.assertEquals(cart2.orderitem_set.count(), 1)

    def test_user_cart_has_items(self):
        anon = AnonymousUser()
        self.assertFalse(Order.user_cart_has_items(anon))
        self.assertFalse(Order.user_cart_has_items(self.user))
        cart = Order.get_cart_for_user(self.user)
        item = OrderItem(order=cart, user=self.user)
        item.save()
        self.assertTrue(Order.user_cart_has_items(self.user))
        self.assertFalse(Order.user_cart_has_items(self.user, CertificateItem))
        self.assertFalse(Order.user_cart_has_items(self.user, PaidCourseRegistration))

    def test_user_cart_has_paid_course_registration_items(self):
        cart = Order.get_cart_for_user(self.user)
        item = PaidCourseRegistration(order=cart, user=self.user)
        item.save()
        self.assertTrue(Order.user_cart_has_items(self.user, PaidCourseRegistration))
        self.assertFalse(Order.user_cart_has_items(self.user, CertificateItem))

    def test_user_cart_has_certificate_items(self):
        cart = Order.get_cart_for_user(self.user)
        CertificateItem.add_to_order(cart, self.course_key, self.cost, 'honor')
        self.assertTrue(Order.user_cart_has_items(self.user, CertificateItem))
        self.assertFalse(Order.user_cart_has_items(self.user, PaidCourseRegistration))

    def test_cart_clear(self):
        cart = Order.get_cart_for_user(user=self.user)
        CertificateItem.add_to_order(cart, self.course_key, self.cost, 'honor')
        CertificateItem.add_to_order(cart, SlashSeparatedCourseKey('org', 'test', 'Test_Course_1'), self.cost, 'honor')
        self.assertEquals(cart.orderitem_set.count(), 2)
        self.assertTrue(cart.has_items())
        cart.clear()
        self.assertEquals(cart.orderitem_set.count(), 0)
        self.assertFalse(cart.has_items())

    def test_add_item_to_cart_currency_match(self):
        cart = Order.get_cart_for_user(user=self.user)
        CertificateItem.add_to_order(cart, self.course_key, self.cost, 'honor', currency='eur')
        # verify that a new item has been added
        self.assertEquals(cart.orderitem_set.count(), 1)
        # verify that the cart's currency was updated
        self.assertEquals(cart.currency, 'eur')
        with self.assertRaises(InvalidCartItem):
            CertificateItem.add_to_order(cart, self.course_key, self.cost, 'honor', currency='usd')
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
            CertificateItem.add_to_order(cart, SlashSeparatedCourseKey.from_deprecated_string(course), cost, 'honor')
        self.assertEquals(cart.orderitem_set.count(), len(course_costs))
        self.assertEquals(cart.total_cost, sum(cost for _course, cost in course_costs))

    def test_start_purchase(self):
        # Start the purchase, which will mark the cart as "paying"
        cart = Order.get_cart_for_user(user=self.user)
        CertificateItem.add_to_order(cart, self.course_key, self.cost, 'honor', currency='usd')
        cart.start_purchase()
        self.assertEqual(cart.status, 'paying')
        for item in cart.orderitem_set.all():
            self.assertEqual(item.status, 'paying')

        # Starting the purchase should be idempotent
        cart.start_purchase()
        self.assertEqual(cart.status, 'paying')
        for item in cart.orderitem_set.all():
            self.assertEqual(item.status, 'paying')

        # If we retrieve the cart for the user, we should get a different order
        next_cart = Order.get_cart_for_user(user=self.user)
        self.assertNotEqual(cart, next_cart)
        self.assertEqual(next_cart.status, 'cart')

        # Complete the first purchase
        cart.purchase()
        self.assertEqual(cart.status, 'purchased')
        for item in cart.orderitem_set.all():
            self.assertEqual(item.status, 'purchased')

        # Starting the purchase again should be a no-op
        cart.start_purchase()
        self.assertEqual(cart.status, 'purchased')
        for item in cart.orderitem_set.all():
            self.assertEqual(item.status, 'purchased')

    def test_purchase(self):
        # This test is for testing the subclassing functionality of OrderItem, but in
        # order to do this, we end up testing the specific functionality of
        # CertificateItem, which is not quite good unit test form. Sorry.
        cart = Order.get_cart_for_user(user=self.user)
        self.assertFalse(CourseEnrollment.is_enrolled(self.user, self.course_key))
        item = CertificateItem.add_to_order(cart, self.course_key, self.cost, 'honor')
        # course enrollment object should be created but still inactive
        self.assertFalse(CourseEnrollment.is_enrolled(self.user, self.course_key))
        cart.purchase()
        self.assertTrue(CourseEnrollment.is_enrolled(self.user, self.course_key))

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
        CertificateItem.add_to_order(cart, self.course_key, self.cost, 'honor')
        with patch('shoppingcart.models.CertificateItem.save', side_effect=DatabaseError):
            with self.assertRaises(DatabaseError):
                cart.purchase()
                # verify that we rolled back the entire transaction
                self.assertFalse(CourseEnrollment.is_enrolled(self.user, self.course_key))
                # verify that e-mail wasn't sent
                self.assertEquals(len(mail.outbox), 0)

    def test_purchase_twice(self):
        cart = Order.get_cart_for_user(self.user)
        CertificateItem.add_to_order(cart, self.course_key, self.cost, 'honor')
        # purchase the cart more than once
        cart.purchase()
        cart.purchase()
        self.assertEquals(len(mail.outbox), 1)

    @patch('shoppingcart.models.log.error')
    def test_purchase_item_email_smtp_failure(self, error_logger):
        cart = Order.get_cart_for_user(user=self.user)
        CertificateItem.add_to_order(cart, self.course_key, self.cost, 'honor')
        with patch('shoppingcart.models.send_mail', side_effect=smtplib.SMTPException):
            cart.purchase()
            self.assertTrue(error_logger.called)

    @patch('shoppingcart.models.log.error')
    def test_purchase_item_email_boto_failure(self, error_logger):
        cart = Order.get_cart_for_user(user=self.user)
        CertificateItem.add_to_order(cart, self.course_key, self.cost, 'honor')
        with patch('shoppingcart.models.send_mail', side_effect=BotoServerError("status", "reason")):
            cart.purchase()
            self.assertTrue(error_logger.called)

    def purchase_with_data(self, cart):
        """ purchase a cart with billing information """
        CertificateItem.add_to_order(cart, self.course_key, self.cost, 'honor')
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

    @patch('shoppingcart.models.render_to_string')
    @patch.dict(settings.FEATURES, {'STORE_BILLING_INFO': True})
    def test_billing_info_storage_on(self, render):
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
        ((_, context), _) = render.call_args
        self.assertTrue(context['has_billing_info'])

    @patch('shoppingcart.models.render_to_string')
    @patch.dict(settings.FEATURES, {'STORE_BILLING_INFO': False})
    def test_billing_info_storage_off(self, render):
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
        ((_, context), _) = render.call_args
        self.assertFalse(context['has_billing_info'])

    mock_gen_inst = MagicMock(return_value=(OrderItemSubclassPK(OrderItem, 1), set([])))

    def test_generate_receipt_instructions_callchain(self):
        """
        This tests the generate_receipt_instructions call chain (ie calling the function on the
        cart also calls it on items in the cart
        """
        cart = Order.get_cart_for_user(self.user)
        item = OrderItem(user=self.user, order=cart)
        item.save()
        self.assertTrue(cart.has_items())
        with patch.object(OrderItem, 'generate_receipt_instructions', self.mock_gen_inst):
            cart.generate_receipt_instructions()
            self.mock_gen_inst.assert_called_with()


class OrderItemTest(TestCase):
    def setUp(self):
        self.user = UserFactory.create()

    def test_order_item_purchased_callback(self):
        """
        This tests that calling purchased_callback on the base OrderItem class raises NotImplementedError
        """
        item = OrderItem(user=self.user, order=Order.get_cart_for_user(self.user))
        with self.assertRaises(NotImplementedError):
            item.purchased_callback()

    def test_order_item_generate_receipt_instructions(self):
        """
        This tests that the generate_receipt_instructions call chain and also
        that calling it on the base OrderItem class returns an empty list
        """
        cart = Order.get_cart_for_user(self.user)
        item = OrderItem(user=self.user, order=cart)
        item.save()
        self.assertTrue(cart.has_items())
        (inst_dict, inst_set) = cart.generate_receipt_instructions()
        self.assertDictEqual({item.pk_with_subclass: set([])}, inst_dict)
        self.assertEquals(set([]), inst_set)


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class PaidCourseRegistrationTest(ModuleStoreTestCase):
    def setUp(self):
        self.user = UserFactory.create()
        self.cost = 40
        self.course = CourseFactory.create(org='MITx', number='999', display_name='Robot Super Course')
        self.course_key = self.course.id
        self.course_mode = CourseMode(course_id=self.course_key,
                                      mode_slug="honor",
                                      mode_display_name="honor cert",
                                      min_price=self.cost)
        self.course_mode.save()
        self.cart = Order.get_cart_for_user(self.user)

    def test_add_to_order(self):
        reg1 = PaidCourseRegistration.add_to_order(self.cart, self.course_key)

        self.assertEqual(reg1.unit_cost, self.cost)
        self.assertEqual(reg1.line_cost, self.cost)
        self.assertEqual(reg1.unit_cost, self.course_mode.min_price)
        self.assertEqual(reg1.mode, "honor")
        self.assertEqual(reg1.user, self.user)
        self.assertEqual(reg1.status, "cart")
        self.assertTrue(PaidCourseRegistration.contained_in_order(self.cart, self.course_key))
        self.assertFalse(PaidCourseRegistration.contained_in_order(self.cart, SlashSeparatedCourseKey("MITx", "999", "Robot_Super_Course_abcd")))

        self.assertEqual(self.cart.total_cost, self.cost)

    def test_add_with_default_mode(self):
        """
        Tests add_to_cart where the mode specified in the argument is NOT in the database
        and NOT the default "honor".  In this case it just adds the user in the CourseMode.DEFAULT_MODE, 0 price
        """
        reg1 = PaidCourseRegistration.add_to_order(self.cart, self.course_key, mode_slug="DNE")

        self.assertEqual(reg1.unit_cost, 0)
        self.assertEqual(reg1.line_cost, 0)
        self.assertEqual(reg1.mode, "honor")
        self.assertEqual(reg1.user, self.user)
        self.assertEqual(reg1.status, "cart")
        self.assertEqual(self.cart.total_cost, 0)
        self.assertTrue(PaidCourseRegistration.contained_in_order(self.cart, self.course_key))

    def test_purchased_callback(self):
        reg1 = PaidCourseRegistration.add_to_order(self.cart, self.course_key)
        self.cart.purchase()
        self.assertTrue(CourseEnrollment.is_enrolled(self.user, self.course_key))
        reg1 = PaidCourseRegistration.objects.get(id=reg1.id)  # reload from DB to get side-effect
        self.assertEqual(reg1.status, "purchased")

    def test_generate_receipt_instructions(self):
        """
        Add 2 courses to the order and make sure the instruction_set only contains 1 element (no dups)
        """
        course2 = CourseFactory.create(org='MITx', number='998', display_name='Robot Duper Course')
        course_mode2 = CourseMode(course_id=course2.id,
                                  mode_slug="honor",
                                  mode_display_name="honor cert",
                                  min_price=self.cost)
        course_mode2.save()
        pr1 = PaidCourseRegistration.add_to_order(self.cart, self.course_key)
        pr2 = PaidCourseRegistration.add_to_order(self.cart, course2.id)
        self.cart.purchase()
        inst_dict, inst_set = self.cart.generate_receipt_instructions()
        self.assertEqual(2, len(inst_dict))
        self.assertEqual(1, len(inst_set))
        self.assertIn("dashboard", inst_set.pop())
        self.assertIn(pr1.pk_with_subclass, inst_dict)
        self.assertIn(pr2.pk_with_subclass, inst_dict)

    def test_purchased_callback_exception(self):
        reg1 = PaidCourseRegistration.add_to_order(self.cart, self.course_key)
        reg1.course_id = SlashSeparatedCourseKey("changed", "forsome", "reason")
        reg1.save()
        with self.assertRaises(PurchasedCallbackException):
            reg1.purchased_callback()
        self.assertFalse(CourseEnrollment.is_enrolled(self.user, self.course_key))

        reg1.course_id = SlashSeparatedCourseKey("abc", "efg", "hij")
        reg1.save()
        with self.assertRaises(PurchasedCallbackException):
            reg1.purchased_callback()
        self.assertFalse(CourseEnrollment.is_enrolled(self.user, self.course_key))

    def test_user_cart_has_both_items(self):
        """
        This test exists b/c having both CertificateItem and PaidCourseRegistration in an order used to break
        PaidCourseRegistration.contained_in_order
        """
        cart = Order.get_cart_for_user(self.user)
        CertificateItem.add_to_order(cart, self.course_key, self.cost, 'honor')
        PaidCourseRegistration.add_to_order(self.cart, self.course_key)
        self.assertTrue(PaidCourseRegistration.contained_in_order(cart, self.course_key))


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class CertificateItemTest(ModuleStoreTestCase):
    """
    Tests for verifying specific CertificateItem functionality
    """
    def setUp(self):
        self.user = UserFactory.create()
        self.cost = 40
        course = CourseFactory.create(org='org', number='test', display_name='Test Course')
        self.course_key = course.id
        course_mode = CourseMode(course_id=self.course_key,
                                 mode_slug="honor",
                                 mode_display_name="honor cert",
                                 min_price=self.cost)
        course_mode.save()
        course_mode = CourseMode(course_id=self.course_key,
                                 mode_slug="verified",
                                 mode_display_name="verified cert",
                                 min_price=self.cost)
        course_mode.save()

        patcher = patch('student.models.tracker')
        self.mock_tracker = patcher.start()
        self.addCleanup(patcher.stop)

    def test_existing_enrollment(self):
        CourseEnrollment.enroll(self.user, self.course_key)
        cart = Order.get_cart_for_user(user=self.user)
        CertificateItem.add_to_order(cart, self.course_key, self.cost, 'verified')
        # verify that we are still enrolled
        self.assertTrue(CourseEnrollment.is_enrolled(self.user, self.course_key))
        self.mock_tracker.reset_mock()
        cart.purchase()
        enrollment = CourseEnrollment.objects.get(user=self.user, course_id=self.course_key)
        self.assertEquals(enrollment.mode, u'verified')

    def test_single_item_template(self):
        cart = Order.get_cart_for_user(user=self.user)
        cert_item = CertificateItem.add_to_order(cart, self.course_key, self.cost, 'verified')

        self.assertEquals(cert_item.single_item_receipt_template,
                          'shoppingcart/verified_cert_receipt.html')

        cert_item = CertificateItem.add_to_order(cart, self.course_key, self.cost, 'honor')
        self.assertEquals(cert_item.single_item_receipt_template,
                          'shoppingcart/receipt.html')

    def test_refund_cert_callback_no_expiration(self):
        # When there is no expiration date on a verified mode, the user can always get a refund
        CourseEnrollment.enroll(self.user, self.course_key, 'verified')
        cart = Order.get_cart_for_user(user=self.user)
        CertificateItem.add_to_order(cart, self.course_key, self.cost, 'verified')
        cart.purchase()

        CourseEnrollment.unenroll(self.user, self.course_key)
        target_certs = CertificateItem.objects.filter(course_id=self.course_key, user_id=self.user, status='refunded', mode='verified')
        self.assertTrue(target_certs[0])
        self.assertTrue(target_certs[0].refund_requested_time)
        self.assertEquals(target_certs[0].order.status, 'refunded')

    def test_refund_cert_callback_before_expiration(self):
        # If the expiration date has not yet passed on a verified mode, the user can be refunded
        many_days = datetime.timedelta(days=60)

        course = CourseFactory.create(org='refund_before_expiration', number='test', display_name='one')
        course_key = course.id
        course_mode = CourseMode(course_id=course_key,
                                 mode_slug="verified",
                                 mode_display_name="verified cert",
                                 min_price=self.cost,
                                 expiration_datetime=(datetime.datetime.now(pytz.utc) + many_days))
        course_mode.save()

        CourseEnrollment.enroll(self.user, course_key, 'verified')
        cart = Order.get_cart_for_user(user=self.user)
        CertificateItem.add_to_order(cart, course_key, self.cost, 'verified')
        cart.purchase()

        CourseEnrollment.unenroll(self.user, course_key)
        target_certs = CertificateItem.objects.filter(course_id=course_key, user_id=self.user, status='refunded', mode='verified')
        self.assertTrue(target_certs[0])
        self.assertTrue(target_certs[0].refund_requested_time)
        self.assertEquals(target_certs[0].order.status, 'refunded')

    def test_refund_cert_callback_before_expiration_email(self):
        """ Test that refund emails are being sent correctly. """
        course = CourseFactory.create(org='refund_before_expiration', number='test', run='course', display_name='one')
        course_key = course.id
        many_days = datetime.timedelta(days=60)

        course_mode = CourseMode(course_id=course_key,
                                 mode_slug="verified",
                                 mode_display_name="verified cert",
                                 min_price=self.cost,
                                 expiration_datetime=datetime.datetime.now(pytz.utc) + many_days)
        course_mode.save()

        CourseEnrollment.enroll(self.user, course_key, 'verified')
        cart = Order.get_cart_for_user(user=self.user)
        CertificateItem.add_to_order(cart, course_key, self.cost, 'verified')
        cart.purchase()

        mail.outbox = []
        with patch('shoppingcart.models.log.error') as mock_error_logger:
            CourseEnrollment.unenroll(self.user, course_key)
            self.assertFalse(mock_error_logger.called)
            self.assertEquals(len(mail.outbox), 1)
            self.assertEquals('[Refund] User-Requested Refund', mail.outbox[0].subject)
            self.assertEquals(settings.PAYMENT_SUPPORT_EMAIL, mail.outbox[0].from_email)
            self.assertIn('has requested a refund on Order', mail.outbox[0].body)

    @patch('shoppingcart.models.log.error')
    def test_refund_cert_callback_before_expiration_email_error(self, error_logger):
        # If there's an error sending an email to billing, we need to log this error
        many_days = datetime.timedelta(days=60)

        course = CourseFactory.create(org='refund_before_expiration', number='test', display_name='one')
        course_key = course.id

        course_mode = CourseMode(course_id=course_key,
                                 mode_slug="verified",
                                 mode_display_name="verified cert",
                                 min_price=self.cost,
                                 expiration_datetime=datetime.datetime.now(pytz.utc) + many_days)
        course_mode.save()

        CourseEnrollment.enroll(self.user, course_key, 'verified')
        cart = Order.get_cart_for_user(user=self.user)
        CertificateItem.add_to_order(cart, course_key, self.cost, 'verified')
        cart.purchase()

        with patch('shoppingcart.models.send_mail', side_effect=smtplib.SMTPException):
            CourseEnrollment.unenroll(self.user, course_key)
            self.assertTrue(error_logger.call_args[0][0].startswith('Failed sending email'))

    def test_refund_cert_callback_after_expiration(self):
        # If the expiration date has passed, the user cannot get a refund
        many_days = datetime.timedelta(days=60)

        course = CourseFactory.create(org='refund_after_expiration', number='test', display_name='two')
        course_key = course.id
        course_mode = CourseMode(course_id=course_key,
                                 mode_slug="verified",
                                 mode_display_name="verified cert",
                                 min_price=self.cost,)
        course_mode.save()

        CourseEnrollment.enroll(self.user, course_key, 'verified')
        cart = Order.get_cart_for_user(user=self.user)
        CertificateItem.add_to_order(cart, course_key, self.cost, 'verified')
        cart.purchase()

        course_mode.expiration_datetime = (datetime.datetime.now(pytz.utc) - many_days)
        course_mode.save()

        CourseEnrollment.unenroll(self.user, course_key)
        target_certs = CertificateItem.objects.filter(course_id=course_key, user_id=self.user, status='refunded', mode='verified')
        self.assertEqual(len(target_certs), 0)

    def test_refund_cert_no_cert_exists(self):
        # If there is no paid certificate, the refund callback should return nothing
        CourseEnrollment.enroll(self.user, self.course_key, 'verified')
        ret_val = CourseEnrollment.unenroll(self.user, self.course_key)
        self.assertFalse(ret_val)
