""" Objects and functions related to generating CSV reports """

from decimal import Decimal
import unicodecsv

from django.utils.translation import ugettext as _

from courseware.courses import get_course_by_id
from course_modes.models import CourseMode
from shoppingcart.models import CertificateItem, OrderItem
from student.models import CourseEnrollment
from util.query import use_read_replica_if_available
from xmodule.modulestore.django import modulestore


class Report(object):
    """
    Base class for making CSV reports related to revenue, enrollments, etc

    To make a different type of report, write a new subclass that implements
    the methods rows and header.
    """
    def __init__(self, start_date, end_date, start_word=None, end_word=None):
        self.start_date = start_date
        self.end_date = end_date
        self.start_word = start_word
        self.end_word = end_word

    def rows(self):
        """
        Performs database queries necessary for the report and eturns an generator of
        lists, in which each list is a separate row of the report.

        Arguments are start_date (datetime), end_date (datetime), start_word (str),
        and end_word (str).  Date comparisons are start_date <= [date of item] < end_date.
        """
        raise NotImplementedError

    def header(self):
        """
        Returns the appropriate header based on the report type, in the form of a
        list of strings.
        """
        raise NotImplementedError

    def write_csv(self, filelike):
        """
        Given a file object to write to and {start/end date, start/end letter} bounds,
        generates a CSV report of the appropriate type.
        """
        items = self.rows()
        writer = unicodecsv.writer(filelike, encoding="utf-8")
        writer.writerow(self.header())
        for item in items:
            writer.writerow(item)


class RefundReport(Report):
    """
    Subclass of Report, used to generate Refund Reports for finance purposes.

    For each refund between a given start_date and end_date, we find the relevant
    order number, customer name, date of transaction, date of refund, and any service
    fees.
    """
    def rows(self):
        query1 = use_read_replica_if_available(
            CertificateItem.objects.select_related('user__profile').filter(
                status="refunded",
                refund_requested_time__gte=self.start_date,
                refund_requested_time__lt=self.end_date,
            ).order_by('refund_requested_time'))
        query2 = use_read_replica_if_available(
            CertificateItem.objects.select_related('user__profile').filter(
                status="refunded",
                refund_requested_time=None,
            ))

        query = query1 | query2

        for item in query:
            yield [
                item.order_id,
                item.user.profile.name,
                item.fulfilled_time,
                item.refund_requested_time,
                item.line_cost,
                item.service_fee,
            ]

    def header(self):
        return [
            _("Order Number"),
            _("Customer Name"),
            _("Date of Original Transaction"),
            _("Date of Refund"),
            _("Amount of Refund"),
            _("Service Fees (if any)"),
        ]


class ItemizedPurchaseReport(Report):
    """
    Subclass of Report, used to generate itemized purchase reports.

    For all purchases (verified certificates, paid course registrations, etc) between
    a given start_date and end_date, we find that purchase's time, order ID, status,
    quantity, unit cost, total cost, currency, description, and related comments.
    """
    def rows(self):
        query = use_read_replica_if_available(
            OrderItem.objects.filter(
                status="purchased",
                fulfilled_time__gte=self.start_date,
                fulfilled_time__lt=self.end_date,
            ).order_by("fulfilled_time"))

        for item in query:
            yield [
                item.fulfilled_time,
                item.order_id,  # pylint: disable=no-member
                item.status,
                item.qty,
                item.unit_cost,
                item.line_cost,
                item.currency,
                item.line_desc,
                item.report_comments,
            ]

    def header(self):
        return [
            _("Purchase Time"),
            _("Order ID"),
            _("Status"),
            _("Quantity"),
            _("Unit Cost"),
            _("Total Cost"),
            _("Currency"),
            _("Description"),
            _("Comments")
        ]


class CertificateStatusReport(Report):
    """
    Subclass of Report, used to generate Certificate Status Reports for Ed Services.

    For each course in each university whose name is within the range start_word and end_word,
    inclusive, (i.e., the letter range H-J includes both Ithaca College and Harvard University), we
    calculate the total enrollment, audit enrollment, honor enrollment, verified enrollment, total
    gross revenue, gross revenue over the minimum, and total dollars refunded.
    """
    def rows(self):
        for course_id in course_ids_between(self.start_word, self.end_word):
            # If the first letter of the university is between start_word and end_word, then we include
            # it in the report.  These comparisons are unicode-safe.
            cur_course = get_course_by_id(course_id)
            university = cur_course.org
            course = cur_course.number + " " + cur_course.display_name_with_default  # TODO add term (i.e. Fall 2013)?
            counts = CourseEnrollment.objects.enrollment_counts(course_id)
            total_enrolled = counts['total']
            audit_enrolled = counts['audit']
            honor_enrolled = counts['honor']

            if counts['verified'] == 0:
                verified_enrolled = 0
                gross_rev = Decimal(0.00)
                gross_rev_over_min = Decimal(0.00)
            else:
                verified_enrolled = counts['verified']
                gross_rev = CertificateItem.verified_certificates_monetary_field_sum(course_id, 'purchased', 'unit_cost')
                gross_rev_over_min = gross_rev - (CourseMode.min_course_price_for_verified_for_currency(course_id, 'usd') * verified_enrolled)

            num_verified_over_the_minimum = CertificateItem.verified_certificates_contributing_more_than_minimum(course_id)

            # should I be worried about is_active here?
            number_of_refunds = CertificateItem.verified_certificates_count(course_id, 'refunded')
            if number_of_refunds == 0:
                dollars_refunded = Decimal(0.00)
            else:
                dollars_refunded = CertificateItem.verified_certificates_monetary_field_sum(course_id, 'refunded', 'unit_cost')

            course_announce_date = ""
            course_reg_start_date = ""
            course_reg_close_date = ""
            registration_period = ""

            yield [
                university,
                course,
                course_announce_date,
                course_reg_start_date,
                course_reg_close_date,
                registration_period,
                total_enrolled,
                audit_enrolled,
                honor_enrolled,
                verified_enrolled,
                gross_rev,
                gross_rev_over_min,
                num_verified_over_the_minimum,
                number_of_refunds,
                dollars_refunded
            ]

    def header(self):
        return [
            _("University"),
            _("Course"),
            _("Course Announce Date"),
            _("Course Start Date"),
            _("Course Registration Close Date"),
            _("Course Registration Period"),
            _("Total Enrolled"),
            _("Audit Enrollment"),
            _("Honor Code Enrollment"),
            _("Verified Enrollment"),
            _("Gross Revenue"),
            _("Gross Revenue over the Minimum"),
            _("Number of Verified Students Contributing More than the Minimum"),
            _("Number of Refunds"),
            _("Dollars Refunded"),
        ]


class UniversityRevenueShareReport(Report):
    """
    Subclass of Report, used to generate University Revenue Share Reports for finance purposes.

    For each course in each university whose name is within the range start_word and end_word,
    inclusive, (i.e., the letter range H-J includes both Ithaca College and Harvard University), we calculate
    the total revenue generated by that particular course.  This includes the number of transactions,
    total payments collected, service fees, number of refunds, and total amount of refunds.
    """
    def rows(self):
        for course_id in course_ids_between(self.start_word, self.end_word):
            cur_course = get_course_by_id(course_id)
            university = cur_course.org
            course = cur_course.number + " " + cur_course.display_name_with_default
            total_payments_collected = CertificateItem.verified_certificates_monetary_field_sum(course_id, 'purchased', 'unit_cost')
            service_fees = CertificateItem.verified_certificates_monetary_field_sum(course_id, 'purchased', 'service_fee')
            num_refunds = CertificateItem.verified_certificates_count(course_id, "refunded")
            amount_refunds = CertificateItem.verified_certificates_monetary_field_sum(course_id, 'refunded', 'unit_cost')
            num_transactions = (num_refunds * 2) + CertificateItem.verified_certificates_count(course_id, "purchased")

            yield [
                university,
                course,
                num_transactions,
                total_payments_collected,
                service_fees,
                num_refunds,
                amount_refunds
            ]

    def header(self):
        return [
            _("University"),
            _("Course"),
            _("Number of Transactions"),
            _("Total Payments Collected"),
            _("Service Fees (if any)"),
            _("Number of Successful Refunds"),
            _("Total Amount of Refunds"),
        ]


def course_ids_between(start_word, end_word):
    """
    Returns a list of all valid course_ids that fall alphabetically between start_word and end_word.
    These comparisons are unicode-safe.
    """

    valid_courses = []
    for course in modulestore().get_courses():
        course_id = course.id.to_deprecated_string()
        if start_word.lower() <= course_id.lower() <= end_word.lower():
            valid_courses.append(course.id)
    return valid_courses
