from shoppingcart.models import CertificateItem, OrderItem
from django.db import models
from django.db.models import Sum
import unicodecsv
from django.conf import settings
from courseware.courses import get_course_by_id
from student.models import CourseEnrollment
from course_modes.models import CourseMode
from decimal import Decimal


class Report(Object):
    """
    Base class for making CSV reports related to revenue, enrollments, etc

    To make a different type of report, write a new subclass that implements
    the methods report_row_generator and csv_report_header_row.
    """

    def report_row_generator(self, start_date, end_date, start_letter=None, end_letter=None):
        """
        Performs database queries necessary for the report.  Returns an generator of
        lists, in which each list is a separate row of the report.
        """
        raise NotImplementedError

    def csv_report_header_row(self):
        """
        Returns the appropriate header based on the report type, in the form of a
        list of strings.
        """
        raise NotImplementedError

    def make_report(self, filelike, start_date, end_date, start_letter=None, end_letter=None):
        """
        Given the string report_type, a file object to write to, and start/end date bounds,
        generates a CSV report of the appropriate type.
        """
        items = self.report_row_generator(start_date, end_date, start_letter, end_letter)
        writer = unicodecsv.writer(filelike, encoding="utf-8")
        writer.writerow(self.csv_report_header_row())
        for item in items:
            writer.writerow(item)


class RefundReport(Report):
    """
    Subclass of Report, used to generate Refund Reports for finance purposes.

    For each refund between a given start_date and end_date, we find the relevant
    order number, customer name, date of transaction, date of refund, and any service
    fees.
    """
    def report_row_generator(self, start_date, end_date, start_letter=None, end_letter=None):
        query = CertificateItem.objects.select_related('user__profile').filter(
            status="refunded",
            refund_requested_time__gte=start_date,
            refund_requested_time__lt=end_date,
        ).order_by('refund_requested_time')
        for item in query:
            yield [
                item.order_id,
                item.user.profile.name,
                item.fulfilled_time,
                item.refund_requested_time,
                item.line_cost,
                item.service_fee,
            ]

    def csv_report_header_row(self):
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
    def report_row_generator(self, start_date, end_date, start_letter=None, end_letter=None):
        query = OrderItem.objects.filter(
            status="purchased",
            fulfilled_time__gte=start_date,
            fulfilled_time__lt=end_date,
        ).order_by("fulfilled_time")

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

    def csv_report_header_row(self):
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

    For each course in each university whose name is within the range start_letter and end_letter,
    inclusive, (i.e., the letter range H-J includes both Ithaca College and Harvard University), we
    calculate the total enrollment, audit enrollment, honor enrollment, verified enrollment, total
    gross revenue, gross revenue over the minimum, and total dollars refunded.
    """
    def report_row_generator(self, start_date, end_date, start_letter=None, end_letter=None):
        results = []
        for course_id in settings.COURSE_LISTINGS['default']:
            # If the first letter of the university is between start_letter and end_letter, then we include
            # it in the report.  These comparisons are unicode-safe.
            if (start_letter.lower() <= course_id.lower()) and (end_letter.lower() >= course_id.lower()) and (get_course_by_id(course_id) is not None):
                cur_course = get_course_by_id(course_id)
                university = cur_course.org
                course = cur_course.number + " " + cur_course.display_name_with_default  # TODO add term (i.e. Fall 2013)?
                enrollments = CourseEnrollment.enrollments_in(course_id)
                total_enrolled = enrollments.count()
                audit_enrolled = CourseEnrollment.enrollments_in(course_id, "audit").count()
                honor_enrolled = CourseEnrollment.enrollments_in(course_id, "honor").count()

                # Since every verified enrollment has 1 and only 1 cert item, let's just query those
                verified_enrollments = CertificateItem.verified_certificates_in(course_id, 'purchased')
                if verified_enrollments is None:
                    verified_enrolled = 0
                    gross_rev = Decimal(0.00)
                    gross_rev_over_min = Decimal(0.00)
                else:
                    verified_enrolled = verified_enrollments.count()
                    gross_rev_temp = verified_enrollments.aggregate(Sum('unit_cost'))
                    gross_rev = gross_rev_temp['unit_cost__sum']
                    gross_rev_over_min = gross_rev - (CourseMode.objects.get(course_id=course_id, mode_slug="verified").min_price * verified_enrolled)

                # should I be worried about is_active here?
                refunded_enrollments = CertificateItem.verified_certificates_in(course_id, 'refunded')
                if refunded_enrollments is None:
                    number_of_refunds = 0
                    dollars_refunded = Decimal(0.00)
                else:
                    number_of_refunds = refunded_enrollments.count()
                    dollars_refunded_temp = refunded_enrollments.aggregate(Sum('unit_cost'))
                    dollars_refunded = dollars_refunded_temp['unit_cost__sum']

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

                results.append(result)
        for item in results:
            yield item

    def csv_report_header_row(self):
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

    For each course in each university whose name is within the range start_letter and end_letter,
    inclusive, (i.e., the letter range H-J includes both Ithaca College and Harvard University), we calculate
    the total revenue generated by that particular course.  This includes the number of transactions,
    total payments collected, service fees, number of refunds, and total amount of refunds.
    """
    def report_row_generator(self, start_date, end_date, start_letter=None, end_letter=None):
        results = []
        for course_id in settings.COURSE_LISTINGS['default']:
            # If the first letter of the university is between start_letter and end_letter, then we include
            # it in the report.  These comparisons are unicode-safe.
            if (start_letter.lower() <= course_id.lower()) and (end_letter.lower() >= course_id.lower()):
                try:
                    cur_course = get_course_by_id(course_id)
                except:
                    break
                university = cur_course.org
                course = cur_course.number + " " + cur_course.display_name_with_default
                num_transactions = 0  # TODO clarify with billing what transactions are included in this (purchases? refunds? etc)

                all_paid_certs = CertificateItem.verified_certificates_in(course_id, "purchased")
                try:
                    total_payments_collected_temp = all_paid_certs.aggregate(Sum('unit_cost'))
                    total_payments_collected = total_payments_collected_temp['unit_cost__sum']
                except:
                    total_payments_collected = Decimal(0.00)
                try:
                    total_service_fees_temp = all_paid_certs.aggregate(Sum('service_fee'))
                    service_fees = total_service_fees_temp['service_fee__sum']
                except:
                    service_fees = Decimal(0.00)

                refunded_enrollments = CertificateItem.verified_certificates_in(course_id, "refunded")
                num_refunds = refunded_enrollments.count()

                amount_refunds_temp = refunded_enrollments.aggregate(Sum('unit_cost'))
                if amount_refunds_temp['unit_cost__sum'] is None:
                    amount_refunds = Decimal(0.00)
                else:
                    amount_refunds = amount_refunds_temp['unit_cost__sum']

                result = [
                    university,
                    course,
                    num_transactions,
                    total_payments_collected,
                    service_fees,
                    num_refunds,
                    amount_refunds
                ]
                results.append(result)

        for item in results:
            yield item

    def csv_report_header_row(self):
        return [
            "University",
            "Course",
            "Number of Transactions",
            "Total Payments Collected",
            "Service Fees (if any)",
            "Number of Successful Refunds",
            "Total Amount of Refunds",
        ]
