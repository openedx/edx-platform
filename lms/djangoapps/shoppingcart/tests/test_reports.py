# -*- coding: utf-8 -*-

"""
Tests for the Shopping Cart Models
"""
import StringIO
from textwrap import dedent
import pytz
import datetime

from django.conf import settings
from django.test.utils import override_settings

from course_modes.models import CourseMode
from courseware.tests.tests import TEST_DATA_MONGO_MODULESTORE
from shoppingcart.models import (Order, CertificateItem, PaidCourseRegistration, PaidCourseRegistrationAnnotation)
from shoppingcart.views import initialize_report
from student.tests.factories import UserFactory
from student.models import CourseEnrollment
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class ReportTypeTests(ModuleStoreTestCase):
    """
    Tests for the models used to generate certificate status reports
    """
    FIVE_MINS = datetime.timedelta(minutes=5)

    def setUp(self):
        # Need to make a *lot* of users for this one
        self.first_verified_user = UserFactory.create()
        self.first_verified_user.profile.name = "John Doe"
        self.first_verified_user.profile.save()

        self.second_verified_user = UserFactory.create()
        self.second_verified_user.profile.name = "Jane Deer"
        self.second_verified_user.profile.save()

        self.first_audit_user = UserFactory.create()
        self.first_audit_user.profile.name = "Joe Miller"
        self.first_audit_user.profile.save()

        self.second_audit_user = UserFactory.create()
        self.second_audit_user.profile.name = "Simon Blackquill"
        self.second_audit_user.profile.save()

        self.third_audit_user = UserFactory.create()
        self.third_audit_user.profile.name = "Super Mario"
        self.third_audit_user.profile.save()

        self.honor_user = UserFactory.create()
        self.honor_user.profile.name = "Princess Peach"
        self.honor_user.profile.save()

        self.first_refund_user = UserFactory.create()
        self.first_refund_user.profile.name = u"King Bowsér"
        self.first_refund_user.profile.save()

        self.second_refund_user = UserFactory.create()
        self.second_refund_user.profile.name = u"Súsan Smith"
        self.second_refund_user.profile.save()

        # Two are verified, three are audit, one honor

        self.cost = 40
        self.course = CourseFactory.create(org='MITx', number='999', display_name=u'Robot Super Course')
        self.course_key = self.course.id
        settings.COURSE_LISTINGS['default'] = [self.course_key.to_deprecated_string()]
        course_mode = CourseMode(course_id=self.course_key,
                                 mode_slug="honor",
                                 mode_display_name="honor cert",
                                 min_price=self.cost)
        course_mode.save()

        course_mode2 = CourseMode(course_id=self.course_key,
                                  mode_slug="verified",
                                  mode_display_name="verified cert",
                                  min_price=self.cost)
        course_mode2.save()

        # User 1 & 2 will be verified
        self.cart1 = Order.get_cart_for_user(self.first_verified_user)
        CertificateItem.add_to_order(self.cart1, self.course_key, self.cost, 'verified')
        self.cart1.purchase()

        self.cart2 = Order.get_cart_for_user(self.second_verified_user)
        CertificateItem.add_to_order(self.cart2, self.course_key, self.cost, 'verified')
        self.cart2.purchase()

        # Users 3, 4, and 5 are audit
        CourseEnrollment.enroll(self.first_audit_user, self.course_key, "audit")
        CourseEnrollment.enroll(self.second_audit_user, self.course_key, "audit")
        CourseEnrollment.enroll(self.third_audit_user, self.course_key, "audit")

        # User 6 is honor
        CourseEnrollment.enroll(self.honor_user, self.course_key, "honor")

        self.now = datetime.datetime.now(pytz.UTC)

        # Users 7 & 8 are refunds
        self.cart = Order.get_cart_for_user(self.first_refund_user)
        CertificateItem.add_to_order(self.cart, self.course_key, self.cost, 'verified')
        self.cart.purchase()
        CourseEnrollment.unenroll(self.first_refund_user, self.course_key)

        self.cart = Order.get_cart_for_user(self.second_refund_user)
        CertificateItem.add_to_order(self.cart, self.course_key, self.cost, 'verified')
        self.cart.purchase(self.second_refund_user, self.course_key)
        CourseEnrollment.unenroll(self.second_refund_user, self.course_key)

        self.test_time = datetime.datetime.now(pytz.UTC)

        first_refund = CertificateItem.objects.get(id=3)
        first_refund.fulfilled_time = self.test_time
        first_refund.refund_requested_time = self.test_time
        first_refund.save()

        second_refund = CertificateItem.objects.get(id=4)
        second_refund.fulfilled_time = self.test_time
        second_refund.refund_requested_time = self.test_time
        second_refund.save()

        self.CORRECT_REFUND_REPORT_CSV = dedent("""
            Order Number,Customer Name,Date of Original Transaction,Date of Refund,Amount of Refund,Service Fees (if any)
            3,King Bowsér,{time_str},{time_str},40,0
            4,Súsan Smith,{time_str},{time_str},40,0
            """.format(time_str=str(self.test_time)))

        self.CORRECT_CERT_STATUS_CSV = dedent("""
            University,Course,Course Announce Date,Course Start Date,Course Registration Close Date,Course Registration Period,Total Enrolled,Audit Enrollment,Honor Code Enrollment,Verified Enrollment,Gross Revenue,Gross Revenue over the Minimum,Number of Verified Students Contributing More than the Minimum,Number of Refunds,Dollars Refunded
            MITx,999 Robot Super Course,,,,,6,3,1,2,80.00,0.00,0,2,80.00
            """.format(time_str=str(self.test_time)))

        self.CORRECT_UNI_REVENUE_SHARE_CSV = dedent("""
            University,Course,Number of Transactions,Total Payments Collected,Service Fees (if any),Number of Successful Refunds,Total Amount of Refunds
            MITx,999 Robot Super Course,6,80.00,0.00,2,80.00
            """.format(time_str=str(self.test_time)))

    def test_refund_report_rows(self):
        report = initialize_report("refund_report", self.now - self.FIVE_MINS, self.now + self.FIVE_MINS)
        refunded_certs = report.rows()

        # check that we have the right number
        num_certs = 0
        for cert in refunded_certs:
            num_certs += 1
        self.assertEqual(num_certs, 2)

        self.assertTrue(CertificateItem.objects.get(user=self.first_refund_user, course_id=self.course_key))
        self.assertTrue(CertificateItem.objects.get(user=self.second_refund_user, course_id=self.course_key))

    def test_refund_report_purchased_csv(self):
        """
        Tests that a generated purchase report CSV is as we expect
        """
        report = initialize_report("refund_report", self.now - self.FIVE_MINS, self.now + self.FIVE_MINS)
        csv_file = StringIO.StringIO()
        report.write_csv(csv_file)
        csv = csv_file.getvalue()
        csv_file.close()
        # Using excel mode csv, which automatically ends lines with \r\n, so need to convert to \n
        self.assertEqual(csv.replace('\r\n', '\n').strip(), self.CORRECT_REFUND_REPORT_CSV.strip())

    def test_basic_cert_status_csv(self):
        report = initialize_report("certificate_status", self.now - self.FIVE_MINS, self.now + self.FIVE_MINS, 'A', 'Z')
        csv_file = StringIO.StringIO()
        report.write_csv(csv_file)
        csv = csv_file.getvalue()
        self.assertEqual(csv.replace('\r\n', '\n').strip(), self.CORRECT_CERT_STATUS_CSV.strip())

    def test_basic_uni_revenue_share_csv(self):
        report = initialize_report("university_revenue_share", self.now - self.FIVE_MINS, self.now + self.FIVE_MINS, 'A', 'Z')
        csv_file = StringIO.StringIO()
        report.write_csv(csv_file)
        csv = csv_file.getvalue()
        self.assertEqual(csv.replace('\r\n', '\n').strip(), self.CORRECT_UNI_REVENUE_SHARE_CSV.strip())


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class ItemizedPurchaseReportTest(ModuleStoreTestCase):
    """
    Tests for the models used to generate itemized purchase reports
    """
    FIVE_MINS = datetime.timedelta(minutes=5)
    TEST_ANNOTATION = u'Ba\xfc\u5305'

    def setUp(self):
        self.user = UserFactory.create()
        self.cost = 40
        self.course = CourseFactory.create(org='MITx', number='999', display_name=u'Robot Super Course')
        self.course_key = self.course.id
        course_mode = CourseMode(course_id=self.course_key,
                                 mode_slug="honor",
                                 mode_display_name="honor cert",
                                 min_price=self.cost)
        course_mode.save()
        course_mode2 = CourseMode(course_id=self.course_key,
                                  mode_slug="verified",
                                  mode_display_name="verified cert",
                                  min_price=self.cost)
        course_mode2.save()
        self.annotation = PaidCourseRegistrationAnnotation(course_id=self.course_key, annotation=self.TEST_ANNOTATION)
        self.annotation.save()
        self.cart = Order.get_cart_for_user(self.user)
        self.reg = PaidCourseRegistration.add_to_order(self.cart, self.course_key)
        self.cert_item = CertificateItem.add_to_order(self.cart, self.course_key, self.cost, 'verified')
        self.cart.purchase()
        self.now = datetime.datetime.now(pytz.UTC)

        paid_reg = PaidCourseRegistration.objects.get(course_id=self.course_key, user=self.user)
        paid_reg.fulfilled_time = self.now
        paid_reg.refund_requested_time = self.now
        paid_reg.save()

        cert = CertificateItem.objects.get(course_id=self.course_key, user=self.user)
        cert.fulfilled_time = self.now
        cert.refund_requested_time = self.now
        cert.save()

        self.CORRECT_CSV = dedent("""
            Purchase Time,Order ID,Status,Quantity,Unit Cost,Total Cost,Currency,Description,Comments
            {time_str},1,purchased,1,40,40,usd,Registration for Course: Robot Super Course,Ba\xc3\xbc\xe5\x8c\x85
            {time_str},1,purchased,1,40,40,usd,verified cert for course Robot Super Course,
            """.format(time_str=str(self.now)))

    def test_purchased_items_btw_dates(self):
        report = initialize_report("itemized_purchase_report", self.now - self.FIVE_MINS, self.now + self.FIVE_MINS)
        purchases = report.rows()

        # since there's not many purchases, just run through the generator to make sure we've got the right number
        num_purchases = 0
        for item in purchases:
            num_purchases += 1
        self.assertEqual(num_purchases, 2)

        report = initialize_report("itemized_purchase_report", self.now + self.FIVE_MINS, self.now + self.FIVE_MINS + self.FIVE_MINS)
        no_purchases = report.rows()

        num_purchases = 0
        for item in no_purchases:
            num_purchases += 1
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
        self.assertEqual(unicode(self.annotation), u'{} : {}'.format(self.course_key.to_deprecated_string(), self.TEST_ANNOTATION))
