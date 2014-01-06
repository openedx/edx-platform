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
from shoppingcart.models import (Order, CertificateItem)
from shoppingcart.reports import ItemizedPurchaseReport, CertificateStatusReport, UniversityRevenueShareReport, RefundReport
from shoppingcart.views import initialize_report, REPORT_TYPES
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
        self.first_refund_user.profile.name = "King Bowser"
        self.first_refund_user.profile.save()

        self.second_refund_user = UserFactory.create()
        self.second_refund_user.profile.name = "Susan Smith"
        self.second_refund_user.profile.save()

        # Two are verified, three are audit, one honor

        self.course_id = "MITx/999/Robot_Super_Course"
        settings.COURSE_LISTINGS['default'] = [self.course_id]
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

        # User 1 & 2 will be verified
        self.cart1 = Order.get_cart_for_user(self.first_verified_user)
        CertificateItem.add_to_order(self.cart1, self.course_id, self.cost, 'verified')
        self.cart1.purchase()

        self.cart2 = Order.get_cart_for_user(self.second_verified_user)
        CertificateItem.add_to_order(self.cart2, self.course_id, self.cost, 'verified')
        self.cart2.purchase()

        # Users 3, 4, and 5 are audit
        CourseEnrollment.enroll(self.first_audit_user, self.course_id, "audit")
        CourseEnrollment.enroll(self.second_audit_user, self.course_id, "audit")
        CourseEnrollment.enroll(self.third_audit_user, self.course_id, "audit")

        # User 6 is honor
        CourseEnrollment.enroll(self.honor_user, self.course_id, "honor")

        self.now = datetime.datetime.now(pytz.UTC)

        # Users 7 & 8 are refunds
        self.cart = Order.get_cart_for_user(self.first_refund_user)
        CertificateItem.add_to_order(self.cart, self.course_id, self.cost, 'verified')
        self.cart.purchase()
        CourseEnrollment.unenroll(self.first_refund_user, self.course_id)

        self.cart = Order.get_cart_for_user(self.second_refund_user)
        CertificateItem.add_to_order(self.cart, self.course_id, self.cost, 'verified')
        self.cart.purchase(self.second_refund_user, self.course_id)
        CourseEnrollment.unenroll(self.second_refund_user, self.course_id)

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
            3,King Bowser,{time_str},{time_str},40,0
            4,Susan Smith,{time_str},{time_str},40,0
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

        self.assertTrue(CertificateItem.objects.get(user=self.first_refund_user, course_id=self.course_id))
        self.assertTrue(CertificateItem.objects.get(user=self.second_refund_user, course_id=self.course_id))

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
