from decimal import Decimal
import unicodecsv

from django.db import models
from django.conf import settings

from courseware.courses import get_course_by_id
from course_modes.models import CourseMode
from shoppingcart.models import CertificateItem, OrderItem
from student.models import CourseEnrollment
from util.query import use_read_replica_if_available


class Report(object):
    """
    Base class for making CSV reports related to revenue, enrollments, etc

    To make a different type of report, write a new subclass that implements
    the methods rows and header.
    """

    def rows(self, start_date, end_date, start_word=None, end_word=None):
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

    def write_csv(self, filelike, start_date, end_date, start_word=None, end_word=None):
        """
        Given a file object to write to and {start/end date, start/end letter} bounds,
        generates a CSV report of the appropriate type.
        """
        items = self.rows(start_date, end_date, start_word, end_word)
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
    def rows(self, start_date, end_date, start_word=None, end_word=None):
        query = use_read_replica_if_available(
            CertificateItem.objects.select_related('user__profile').filter(
                status="refunded",
                refund_requested_time__gte=start_date,
                refund_requested_time__lt=end_date,
            ).order_by('refund_requested_time'))

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
            "Order Number",
            "Customer Name",
            "Date of Original Transaction",
            "Date of Refund",
            "Amount of Refund",
            "Service Fees (if any)",
        ]


class ItemizedPurchaseReport(Report):
    """
    Subclass of Report, used to generate itemized purchase reports.

    For all purchases (verified certificates, paid course registrations, etc) between
    a given start_date and end_date, we find that purchase's time, order ID, status,
    quantity, unit cost, total cost, currency, description, and related comments.
    """
    def rows(self, start_date, end_date, start_word=None, end_word=None):
        query = use_read_replica_if_available(
            OrderItem.objects.filter(
                status="purchased",
                fulfilled_time__gte=start_date,
                fulfilled_time__lt=end_date,
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
            "Purchase Time",
            "Order ID",
            "Status",
            "Quantity",
            "Unit Cost",
            "Total Cost",
            "Currency",
            "Description",
            "Comments"
        ]


class CertificateStatusReport(Report):
    """
    Subclass of Report, used to generate Certificate Status Reports for Ed Services.

    For each course in each university whose name is within the range start_word and end_word,
    inclusive, (i.e., the letter range H-J includes both Ithaca College and Harvard University), we
    calculate the total enrollment, audit enrollment, honor enrollment, verified enrollment, total
    gross revenue, gross revenue over the minimum, and total dollars refunded.
    """
    def rows(self, start_date, end_date, start_word=None, end_word=None):
        results = []
        for course_id in course_ids_between(start_word, end_word):
            # If the first letter of the university is between start_word and end_word, then we include
            # it in the report.  These comparisons are unicode-safe.
            cur_course = get_course_by_id(course_id)
            university = cur_course.org
            course = cur_course.number + " " + cur_course.display_name_with_default  # TODO add term (i.e. Fall 2013)?
            counts = CourseEnrollment.enrollment_counts(course_id)
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
                gross_rev_over_min = gross_rev - (CourseMode.min_course_price_for_currency(course_id, 'usd') * verified_enrolled)

            # should I be worried about is_active here?
            number_of_refunds = CertificateItem.verified_certificates_count(course_id, 'refunded')
            if number_of_refunds == 0:
                dollars_refunded = Decimal(0.00)
            else:
                dollars_refunded = CertificateItem.verified_certificates_monetary_field_sum(course_id, 'refunded', 'unit_cost')

            result = [
                university,
                course,
                total_enrolled,
                audit_enrolled,
                honor_enrolled,
                verified_enrolled,
                gross_rev,
                gross_rev_over_min,
                number_of_refunds,
                dollars_refunded
            ]
            yield result

    def header(self):
        return [
            "University",
            "Course",
            "Total Enrolled",
            "Audit Enrollment",
            "Honor Code Enrollment",
            "Verified Enrollment",
            "Gross Revenue",
            "Gross Revenue over the Minimum",
            "Number of Refunds",
            "Dollars Refunded",
        ]


class UniversityRevenueShareReport(Report):
    """
    Subclass of Report, used to generate University Revenue Share Reports for finance purposes.

    For each course in each university whose name is within the range start_word and end_word,
    inclusive, (i.e., the letter range H-J includes both Ithaca College and Harvard University), we calculate
    the total revenue generated by that particular course.  This includes the number of transactions,
    total payments collected, service fees, number of refunds, and total amount of refunds.
    """
    def rows(self, start_date, end_date, start_word=None, end_word=None):
        results = []
        for course_id in course_ids_between(start_word, end_word):
            cur_course = get_course_by_id(course_id)
            university = cur_course.org
            course = cur_course.number + " " + cur_course.display_name_with_default
            num_transactions = 0  # TODO clarify with billing what transactions are included in this (purchases? refunds? etc)
            total_payments_collected = CertificateItem.verified_certificates_monetary_field_sum(course_id, 'purchased', 'unit_cost')
            service_fees = CertificateItem.verified_certificates_monetary_field_sum(course_id, 'purchased', 'service_fee')
            num_refunds = CertificateItem.verified_certificates_count(course_id, "refunded")
            amount_refunds = CertificateItem.verified_certificates_monetary_field_sum(course_id, 'refunded', 'unit_cost')

            result = [
                university,
                course,
                num_transactions,
                total_payments_collected,
                service_fees,
                num_refunds,
                amount_refunds
            ]
            yield result

    def header(self):
        return [
            "University",
            "Course",
            "Number of Transactions",
            "Total Payments Collected",
            "Service Fees (if any)",
            "Number of Successful Refunds",
            "Total Amount of Refunds",
        ]

def course_ids_between(start_word, end_word):
    """ 
    Returns a list of all valid course_ids that fall alphabetically between start_word and end_word.
    These comparisons are unicode-safe. 
    """
    valid_courses = []
    for course_id in settings.COURSE_LISTINGS['default']:
        if (start_word.lower() <= course_id.lower()) and (end_word.lower() >= course_id.lower()) and (get_course_by_id(course_id) is not None):
            valid_courses.append(course_id)
    return valid_courses
