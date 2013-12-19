"""
Tests for the Shopping Cart Models
"""
import StringIO
from textwrap import dedent

from django.conf import settings
from django.test.utils import override_settings
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from courseware.tests.tests import TEST_DATA_MONGO_MODULESTORE
from shoppingcart.models import (Order, CertificateItem)
from shoppingcart.reports import ItemizedPurchaseReport, CertificateStatusReport, UniversityRevenueShareReport, RefundReport
from student.tests.factories import UserFactory
from student.models import CourseEnrollment
from course_modes.models import CourseMode
from shoppingcart.views import initialize_report, REPORT_TYPES
import pytz
import datetime


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class ReportTypeTests(ModuleStoreTestCase):
    """
    Tests for the models used to generate certificate status reports
    """
    FIVE_MINS = datetime.timedelta(minutes=5)

    def setUp(self):
        # Need to make a *lot* of users for this one
        self.user1 = UserFactory.create()
        self.user1.first_name = "John"
        self.user1.last_name = "Doe"
        self.user1.save()

        self.user2 = UserFactory.create()
        self.user2.first_name = "Jane"
        self.user2.last_name = "Deer"
        self.user2.save()

        self.user3 = UserFactory.create()
        self.user3.first_name = "Joe"
        self.user3.last_name = "Miller"
        self.user3.save()

        self.user4 = UserFactory.create()
        self.user4.first_name = "Simon"
        self.user4.last_name = "Blackquill"
        self.user4.save()

        self.user5 = UserFactory.create()
        self.user5.first_name = "Super"
        self.user5.last_name = "Mario"
        self.user5.save()

        self.user6 = UserFactory.create()
        self.user6.first_name = "Princess"
        self.user6.last_name = "Peach"
        self.user6.save()

        self.user7 = UserFactory.create()
        self.user7.first_name = "King"
        self.user7.last_name = "Bowser"
        self.user7.save()

        self.user8 = UserFactory.create()
        self.user8.first_name = "Susan"
        self.user8.last_name = "Smith"
        self.user8.save()

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
        self.cart1 = Order.get_cart_for_user(self.user1)
        CertificateItem.add_to_order(self.cart1, self.course_id, self.cost, 'verified')
        self.cart1.purchase()

        self.cart2 = Order.get_cart_for_user(self.user2)
        CertificateItem.add_to_order(self.cart2, self.course_id, self.cost, 'verified')
        self.cart2.purchase()

        # Users 3, 4, and 5 are audit
        CourseEnrollment.enroll(self.user3, self.course_id, "audit")
        CourseEnrollment.enroll(self.user4, self.course_id, "audit")
        CourseEnrollment.enroll(self.user5, self.course_id, "audit")

        # User 6 is honor
        CourseEnrollment.enroll(self.user6, self.course_id, "honor")

        self.now = datetime.datetime.now(pytz.UTC)

        # Users 7 & 8 are refunds
        self.cart = Order.get_cart_for_user(self.user7)
        CertificateItem.add_to_order(self.cart, self.course_id, self.cost, 'verified')
        self.cart.purchase()
        CourseEnrollment.unenroll(self.user7, self.course_id)

        self.cart = Order.get_cart_for_user(self.user8)
        CertificateItem.add_to_order(self.cart, self.course_id, self.cost, 'verified')
        self.cart.purchase(self.user8, self.course_id)
        CourseEnrollment.unenroll(self.user8, self.course_id)

        self.test_time = datetime.datetime.now(pytz.UTC)
        self.CORRECT_REFUND_REPORT_CSV = dedent("""
            Order Number,Customer Name,Date of Original Transaction,Date of Refund,Amount of Refund,Service Fees (if any)
            3,King Bowser,{time_str},{time_str},40,0
            4,Susan Smith,{time_str},{time_str},40,0
            """.format(time_str=str(self.test_time)))

        self.CORRECT_CERT_STATUS_CSV = dedent("""
            University,Course,Total Enrolled,Audit Enrollment,Honor Code Enrollment,Verified Enrollment,Gross Revenue,Gross Revenue over the Minimum,Number of Refunds,Dollars Refunded
            MITx,999 Robot Super Course,6,3,1,2,80.00,0.00,0,0
            """.format(time_str=str(self.test_time)))

        self.CORRECT_UNI_REVENUE_SHARE_CSV = dedent("""
            University,Course,Number of Transactions,Total Payments Collected,Service Fees (if any),Number of Successful Refunds,Total Amount of Refunds
            MITx,999 Robot Super Course,0,80.00,0.00,2,80.00
            """.format(time_str=str(self.test_time)))

    def test_refund_report_get_report_data(self):
        report = initialize_report("refund_report")
        refunded_certs = report.get_report_data(self.now - self.FIVE_MINS, self.now + self.FIVE_MINS)
        self.assertEqual(len(refunded_certs), 2)
        self.assertTrue(CertificateItem.objects.get(user=self.user7, course_id=self.course_id))
        self.assertTrue(CertificateItem.objects.get(user=self.user8, course_id=self.course_id))

    def test_refund_report_purchased_csv(self):
        """
        Tests that a generated purchase report CSV is as we expect
        """
        report = initialize_report("refund_report")
        for item in report.get_report_data(self.now - self.FIVE_MINS, self.now + self.FIVE_MINS):
            item.fulfilled_time = self.test_time
            item.refund_requested_time = self.test_time  # hm do we want to make these different
            item.save()

        csv_file = StringIO.StringIO()
        report.make_report(csv_file, self.now - self.FIVE_MINS, self.now + self.FIVE_MINS)
        csv = csv_file.getvalue()
        csv_file.close()
        # Using excel mode csv, which automatically ends lines with \r\n, so need to convert to \n
        self.assertEqual(csv.replace('\r\n', '\n').strip(), self.CORRECT_REFUND_REPORT_CSV.strip())

    def test_basic_cert_status_csv(self):
        report = initialize_report("certificate_status")
        csv_file = StringIO.StringIO()
        report.make_report(csv_file, self.now - self.FIVE_MINS, self.now + self.FIVE_MINS, 'A', 'Z')
        csv = csv_file.getvalue()
        self.assertEqual(csv.replace('\r\n', '\n').strip(), self.CORRECT_CERT_STATUS_CSV.strip())

    def test_basic_uni_revenue_share_csv(self):
        report = initialize_report("university_revenue_share")
        csv_file = StringIO.StringIO()
        report.make_report(csv_file, self.now - self.FIVE_MINS, self.now + self.FIVE_MINS, 'A', 'Z')
        csv = csv_file.getvalue()
        self.assertEqual(csv.replace('\r\n', '\n').strip(), self.CORRECT_UNI_REVENUE_SHARE_CSV.strip())
