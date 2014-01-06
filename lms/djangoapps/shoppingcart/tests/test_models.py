"""
Tests for the Shopping Cart Models
"""
import smtplib
import StringIO
from textwrap import dedent
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
from courseware.tests.tests import TEST_DATA_MONGO_MODULESTORE
from shoppingcart.models import (Order, OrderItem, CertificateItem, InvalidCartItem, PaidCourseRegistration,
                                 OrderItemSubclassPK, PaidCourseRegistrationAnnotation)
from shoppingcart.views import initialize_report, REPORT_TYPES
from shoppingcart.reports import ItemizedPurchaseReport, CertificateStatusReport, UniversityRevenueShareReport, RefundReport
from student.tests.factories import UserFactory
from student.models import CourseEnrollment
from course_modes.models import CourseMode
from shoppingcart.exceptions import PurchasedCallbackException, ReportTypeDoesNotExistException
import pytz
import datetime


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

    def test_user_cart_has_items(self):
        anon = AnonymousUser()
        self.assertFalse(Order.user_cart_has_items(anon))
        self.assertFalse(Order.user_cart_has_items(self.user))
        cart = Order.get_cart_for_user(self.user)
        item = OrderItem(order=cart, user=self.user)
        item.save()
        self.assertTrue(Order.user_cart_has_items(self.user))

    def test_cart_clear(self):
        cart = Order.get_cart_for_user(user=self.user)
        CertificateItem.add_to_order(cart, self.course_id, self.cost, 'honor')
        CertificateItem.add_to_order(cart, 'org/test/Test_Course_1', self.cost, 'honor')
        self.assertEquals(cart.orderitem_set.count(), 2)
        self.assertTrue(cart.has_items())
        cart.clear()
        self.assertEquals(cart.orderitem_set.count(), 0)
        self.assertFalse(cart.has_items())

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

    def test_purchase_twice(self):
        cart = Order.get_cart_for_user(self.user)
        CertificateItem.add_to_order(cart, self.course_id, self.cost, 'honor')
        # purchase the cart more than once
        cart.purchase()
        cart.purchase()
        self.assertEquals(len(mail.outbox), 1)

    @patch('shoppingcart.models.log.error')
    def test_purchase_item_email_smtp_failure(self, error_logger):
        cart = Order.get_cart_for_user(user=self.user)
        CertificateItem.add_to_order(cart, self.course_id, self.cost, 'honor')
        with patch('shoppingcart.models.send_mail', side_effect=smtplib.SMTPException):
            cart.purchase()
            self.assertTrue(error_logger.called)

    @patch('shoppingcart.models.log.error')
    def test_purchase_item_email_boto_failure(self, error_logger):
        cart = Order.get_cart_for_user(user=self.user)
        CertificateItem.add_to_order(cart, self.course_id, self.cost, 'honor')
        with patch('shoppingcart.models.send_mail', side_effect=BotoServerError("status", "reason")):
            cart.purchase()
            self.assertTrue(error_logger.called)

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
        self.assertTrue(PaidCourseRegistration.contained_in_order(self.cart, self.course_id))
        self.assertFalse(PaidCourseRegistration.contained_in_order(self.cart, self.course_id + "abcd"))
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
        self.assertTrue(PaidCourseRegistration.contained_in_order(self.cart, self.course_id))

    def test_purchased_callback(self):
        reg1 = PaidCourseRegistration.add_to_order(self.cart, self.course_id)
        self.cart.purchase()
        self.assertTrue(CourseEnrollment.is_enrolled(self.user, self.course_id))
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
        pr1 = PaidCourseRegistration.add_to_order(self.cart, self.course_id)
        pr2 = PaidCourseRegistration.add_to_order(self.cart, course2.id)
        self.cart.purchase()
        inst_dict, inst_set = self.cart.generate_receipt_instructions()
        self.assertEqual(2, len(inst_dict))
        self.assertEqual(1, len(inst_set))
        self.assertIn("dashboard", inst_set.pop())
        self.assertIn(pr1.pk_with_subclass, inst_dict)
        self.assertIn(pr2.pk_with_subclass, inst_dict)

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
class ItemizedPurchaseReportTest(ModuleStoreTestCase):
    """
    Tests for the models used to generate itemized purchase reports
    """
    FIVE_MINS = datetime.timedelta(minutes=5)
    TEST_ANNOTATION = u'Ba\xfc\u5305'

    def setUp(self):
        self.user = UserFactory.create()
        self.course_id = "MITx/999/Robot_Super_Course"
        self.cost = 40
        self.course = CourseFactory.create(org='MITx', number='999', display_name=u'Robot Super Course')
        course_mode = CourseMode(course_id=self.course_id,
                                 mode_slug="honor",
                                 mode_display_name="honor cert",
                                 min_price=self.cost)
        course_mode.save()
        course_mode2 = CourseMode(course_id=self.course_id,
                                  mode_slug="verified",
                                  mode_display_name="verified cert",
                                  min_price=self.cost)
        course_mode2.save()
        self.annotation = PaidCourseRegistrationAnnotation(course_id=self.course_id, annotation=self.TEST_ANNOTATION)
        self.annotation.save()
        self.cart = Order.get_cart_for_user(self.user)
        self.reg = PaidCourseRegistration.add_to_order(self.cart, self.course_id)
        self.cert_item = CertificateItem.add_to_order(self.cart, self.course_id, self.cost, 'verified')
        self.cart.purchase()
        self.now = datetime.datetime.now(pytz.UTC)

        paid_reg = PaidCourseRegistration.objects.get(course_id=self.course_id, user=self.user)
        paid_reg.fulfilled_time = self.now
        paid_reg.refund_requested_time = self.now
        paid_reg.save()

        cert = CertificateItem.objects.get(course_id=self.course_id, user=self.user)
        cert.fulfilled_time = self.now
        cert.refund_requested_time = self.now
        cert.save()

        self.CORRECT_CSV = dedent("""
            Purchase Time,Order ID,Status,Quantity,Unit Cost,Total Cost,Currency,Description,Comments
            {time_str},1,purchased,1,40,40,usd,Registration for Course: Robot Super Course,Ba\xc3\xbc\xe5\x8c\x85
            {time_str},1,purchased,1,40,40,usd,"Certificate of Achievement, verified cert for course Robot Super Course",
            """.format(time_str=str(self.now)))

    def test_purchased_items_btw_dates(self):
        report = initialize_report("itemized_purchase_report", self.now - self.FIVE_MINS, self.now + self.FIVE_MINS)
        purchases = report.rows()

        # since there's not many purchases, just run through the generator to make sure we've got the right number
        num_purchases = 0
        for item in purchases:
            num_purchases += 1
        self.assertEqual(num_purchases, 2)
        #self.assertIn(self.reg.orderitem_ptr, purchases)
        #self.assertIn(self.cert_item.orderitem_ptr, purchases)

        report = initialize_report("itemized_purchase_report", self.now + self.FIVE_MINS, self.now + self.FIVE_MINS + self.FIVE_MINS)
        no_purchases = report.rows()

        num_purchases = 0
        for item in no_purchases:
            num_purchases +=1
        self.assertEqual(num_purchases, 0)

    def test_purchased_csv(self):
        """
        Tests that a generated purchase report CSV is as we expect
        """
        report = initialize_report("itemized_purchase_report", self.now - self.FIVE_MINS, self.now + self.FIVE_MINS)
        csv_file = StringIO.StringIO()
        report.write_csv(csv_file)
        csv = csv_file.getvalue()
        csv_file.close()
        # Using excel mode csv, which automatically ends lines with \r\n, so need to convert to \n
        self.assertEqual(csv.replace('\r\n', '\n').strip(), self.CORRECT_CSV.strip())

    def test_csv_report_no_annotation(self):
        """
        Fill in gap in test coverage.  csv_report_comments for PaidCourseRegistration instance with no
        matching annotation
        """
        # delete the matching annotation
        self.annotation.delete()
        self.assertEqual(u"", self.reg.csv_report_comments)

    def test_paidcourseregistrationannotation_unicode(self):
        """
        Fill in gap in test coverage.  __unicode__ method of PaidCourseRegistrationAnnotation
        """
        self.assertEqual(unicode(self.annotation), u'{} : {}'.format(self.course_id, self.TEST_ANNOTATION))


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

        patcher = patch('student.models.server_track')
        self.mock_server_track = patcher.start()
        self.addCleanup(patcher.stop)
        crum_patcher = patch('student.models.crum.get_current_request')
        self.mock_get_current_request = crum_patcher.start()
        self.addCleanup(crum_patcher.stop)
        self.mock_get_current_request.return_value = sentinel.request

    def test_existing_enrollment(self):
        CourseEnrollment.enroll(self.user, self.course_id)
        cart = Order.get_cart_for_user(user=self.user)
        CertificateItem.add_to_order(cart, self.course_id, self.cost, 'verified')
        # verify that we are still enrolled
        self.assertTrue(CourseEnrollment.is_enrolled(self.user, self.course_id))
        self.mock_server_track.reset_mock()
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

    def test_refund_cert_callback_no_expiration(self):
        # When there is no expiration date on a verified mode, the user can always get a refund
        CourseEnrollment.enroll(self.user, self.course_id, 'verified')
        cart = Order.get_cart_for_user(user=self.user)
        CertificateItem.add_to_order(cart, self.course_id, self.cost, 'verified')
        cart.purchase()

        CourseEnrollment.unenroll(self.user, self.course_id)
        target_certs = CertificateItem.objects.filter(course_id=self.course_id, user_id=self.user, status='refunded', mode='verified')
        self.assertTrue(target_certs[0])
        self.assertTrue(target_certs[0].refund_requested_time)
        self.assertEquals(target_certs[0].order.status, 'refunded')

    def test_refund_cert_callback_before_expiration(self):
        # If the expiration date has not yet passed on a verified mode, the user can be refunded
        course_id = "refund_before_expiration/test/one"
        many_days = datetime.timedelta(days=60)

        CourseFactory.create(org='refund_before_expiration', number='test', run='course', display_name='one')
        course_mode = CourseMode(course_id=course_id,
                                 mode_slug="verified",
                                 mode_display_name="verified cert",
                                 min_price=self.cost,
                                 expiration_datetime=(datetime.datetime.now(pytz.utc) + many_days))
        course_mode.save()

        CourseEnrollment.enroll(self.user, course_id, 'verified')
        cart = Order.get_cart_for_user(user=self.user)
        CertificateItem.add_to_order(cart, course_id, self.cost, 'verified')
        cart.purchase()

        CourseEnrollment.unenroll(self.user, course_id)
        target_certs = CertificateItem.objects.filter(course_id=course_id, user_id=self.user, status='refunded', mode='verified')
        self.assertTrue(target_certs[0])
        self.assertTrue(target_certs[0].refund_requested_time)
        self.assertEquals(target_certs[0].order.status, 'refunded')

    @patch('shoppingcart.models.log.error')
    def test_refund_cert_callback_before_expiration_email_error(self, error_logger):
        # If there's an error sending an email to billing, we need to log this error
        course_id = "refund_before_expiration/test/one"
        many_days = datetime.timedelta(days=60)

        CourseFactory.create(org='refund_before_expiration', number='test', run='course', display_name='one')
        course_mode = CourseMode(course_id=course_id,
                                 mode_slug="verified",
                                 mode_display_name="verified cert",
                                 min_price=self.cost,
                                 expiration_datetime=datetime.datetime.now(pytz.utc) + many_days)
        course_mode.save()

        CourseEnrollment.enroll(self.user, course_id, 'verified')
        cart = Order.get_cart_for_user(user=self.user)
        CertificateItem.add_to_order(cart, course_id, self.cost, 'verified')
        cart.purchase()

        with patch('shoppingcart.models.send_mail', side_effect=smtplib.SMTPException):
            CourseEnrollment.unenroll(self.user, course_id)
            self.assertTrue(error_logger.called)

    def test_refund_cert_callback_after_expiration(self):
        # If the expiration date has passed, the user cannot get a refund
        course_id = "refund_after_expiration/test/two"
        many_days = datetime.timedelta(days=60)

        CourseFactory.create(org='refund_after_expiration', number='test', run='course', display_name='two')
        course_mode = CourseMode(course_id=course_id,
                                 mode_slug="verified",
                                 mode_display_name="verified cert",
                                 min_price=self.cost,)
        course_mode.save()

        CourseEnrollment.enroll(self.user, course_id, 'verified')
        cart = Order.get_cart_for_user(user=self.user)
        CertificateItem.add_to_order(cart, course_id, self.cost, 'verified')
        cart.purchase()

        course_mode.expiration_datetime = (datetime.datetime.now(pytz.utc) - many_days)
        course_mode.save()

        CourseEnrollment.unenroll(self.user, course_id)
        target_certs = CertificateItem.objects.filter(course_id=course_id, user_id=self.user, status='refunded', mode='verified')
        self.assertEqual(len(target_certs), 0)

    def test_refund_cert_no_cert_exists(self):
        # If there is no paid certificate, the refund callback should return nothing
        CourseEnrollment.enroll(self.user, self.course_id, 'verified')
        ret_val = CourseEnrollment.unenroll(self.user, self.course_id)
        self.assertFalse(ret_val)
