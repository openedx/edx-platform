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
        self.user1.profile.name = "John Doe"
        self.user1.profile.save()

        self.user2 = UserFactory.create()
        self.user2.profile.name = "Jane Deer"
        self.user2.profile.save()

        self.user3 = UserFactory.create()
        self.user3.profile.name = "Joe Miller"
        self.user3.profile.save()

        self.user4 = UserFactory.create()
        self.user4.profile.name = "Simon Blackquill"
        self.user4.profile.save()

        self.user5 = UserFactory.create()
        self.user5.profile.name = "Super Mario"
        self.user5.profile.save()

        self.user6 = UserFactory.create()
        self.user6.profile.name = "Princess Peach"
        self.user6.profile.save()

        self.user7 = UserFactory.create()
        self.user7.profile.name = "King Bowser"
        self.user7.profile.save()

        self.user8 = UserFactory.create()
        self.user8.profile.name = "Susan Smith"
        self.user8.profile.save()

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

        # We can't modify the values returned by report_row_generator directly, since it's a generator, but
        # we need the times on CORRECT_CSV and the generated report to match.  So, we extract the times from
        # the report_row_generator and place them in CORRECT_CSV.
        self.time_str = {}
        report = initialize_report("refund_report")
        refunds = report.report_row_generator(self.now - self.FIVE_MINS, self.now + self.FIVE_MINS)
        time_index = 0
        for item in refunds:
            self.time_str[time_index] = item[2]
            time_index += 1
            self.time_str[time_index] = item[3]
            time_index += 1
        self.CORRECT_REFUND_REPORT_CSV = dedent("""
            Order Number,Customer Name,Date of Original Transaction,Date of Refund,Amount of Refund,Service Fees (if any)
            3,King Bowser,{time_str0},{time_str1},40,0
            4,Susan Smith,{time_str2},{time_str3},40,0
            """.format(time_str0=str(self.time_str[0]), time_str1=str(self.time_str[1]), time_str2=str(self.time_str[2]), time_str3=str(self.time_str[3])))

        self.test_time = datetime.datetime.now(pytz.UTC)

        self.CORRECT_CERT_STATUS_CSV = dedent("""
            University,Course,Total Enrolled,Audit Enrollment,Honor Code Enrollment,Verified Enrollment,Gross Revenue,Gross Revenue over the Minimum,Number of Refunds,Dollars Refunded
            MITx,999 Robot Super Course,6,3,1,2,80.00,0.00,2,80.00
            """.format(time_str=str(self.test_time)))

        self.CORRECT_UNI_REVENUE_SHARE_CSV = dedent("""
            University,Course,Number of Transactions,Total Payments Collected,Service Fees (if any),Number of Successful Refunds,Total Amount of Refunds
            MITx,999 Robot Super Course,0,80.00,0.00,2,80.00
            """.format(time_str=str(self.test_time)))

    def test_refund_report_report_row_generator(self):
        report = initialize_report("refund_report")
        refunded_certs = report.report_row_generator(self.now - self.FIVE_MINS, self.now + self.FIVE_MINS)

        # check that we have the right number
        num_certs = 0
        for cert in refunded_certs:
            num_certs += 1
        self.assertEqual(num_certs, 2)

        self.assertTrue(CertificateItem.objects.get(user=self.user7, course_id=self.course_id))
        self.assertTrue(CertificateItem.objects.get(user=self.user8, course_id=self.course_id))

    def test_refund_report_purchased_csv(self):
        """
        Tests that a generated purchase report CSV is as we expect
        """
        report = initialize_report("refund_report")
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
