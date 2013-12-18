from shoppingcart.models import CertificateItem, OrderItem
from django.db import models
from django.db.models import Sum
import unicodecsv
from django.conf import settings
from courseware.courses import get_course_by_id
from student.models import CourseEnrollment
from course_modes.models import CourseMode
from decimal import Decimal


class Report(models.Model):
    """
    Base class for making CSV reports related to revenue, enrollments, etc

    To make a different type of report, write a new subclass that implements
    the methods get_report_data, csv_report_header_row, and csv_report_row.
    """

    def get_report_data(self, start_date, end_date, start_letter=None, end_letter=None):
        """
        Performs database queries necessary for the report.  May return either a query result
        or a list of lists, depending on the particular type of report--see Report subclasses
        for sample implementations.
        """
        raise NotImplementedError

    def csv_report_header_row(self):
        """
        Returns the appropriate header based on the report type.
        """
        raise NotImplementedError

    def csv_report_row(self, item):
        """
        Given the results of get_report_data, this function generates a single row of a csv.
        """
        raise NotImplementedError

    def make_report(self, filelike, start_date, end_date, start_letter=None, end_letter=None):
        """
        Given the string report_type, a file object to write to, and start/end date bounds,
        generates a CSV report of the appropriate type.
        """
        items = self.get_report_data(start_date, end_date, start_letter, end_letter)
        writer = unicodecsv.writer(filelike, encoding="utf-8")
        writer.writerow(self.csv_report_header_row())
        for item in items:
            writer.writerow(self.csv_report_row(item))


class RefundReport(Report):
    """
    Subclass of Report, used to generate Refund Reports for finance purposes.
    """
    def get_report_data(self, start_date, end_date, start_letter=None, end_letter=None):
        return CertificateItem.objects.filter(
            status="refunded",
            refund_requested_time__gte=start_date,
            refund_requested_time__lt=end_date,
        )

    def csv_report_header_row(self):
        return [
            "Order Number",
            "Customer Name",
            "Date of Original Transaction",
            "Date of Refund",
            "Amount of Refund",
            "Service Fees (if any)",
        ]

    def csv_report_row(self, item):
        return [
            item.order_id,
            item.user.get_full_name(),
            item.fulfilled_time,
            item.refund_requested_time,  # TODO Change this torefund_fulfilled once we start recording that value
            item.line_cost,
            item.service_fee,
        ]


class ItemizedPurchaseReport(Report):
    """
    Subclass of Report, used to generate itemized purchase reports.
    """
    def get_report_data(self, start_date, end_date, start_letter=None, end_letter=None):
        return OrderItem.objects.filter(
            status="purchased",
            fulfilled_time__gte=start_date,
            fulfilled_time__lt=end_date,
        ).order_by("fulfilled_time")

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

    def csv_report_row(self, item):
        return [
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


class CertificateStatusReport(Report):
    """
    Subclass of Report, used to generate Certificate Status Reports for ed services.
    """
    def get_report_data(self, start_date, end_date, start_letter=None, end_letter=None):
        results = []
        for course_id in settings.COURSE_LISTINGS['default']:
            if (start_letter.lower() <= course_id.lower()) and (end_letter.lower() >= course_id.lower()) and (get_course_by_id(course_id) is not None):
                cur_course = get_course_by_id(course_id)
                university = cur_course.org
                course = cur_course.number + " " + cur_course.display_name  # TODO add term (i.e. Fall 2013)?
                enrollments = CourseEnrollment.enrollments_in(course_id)
                total_enrolled = enrollments.count()
                audit_enrolled = enrollments.filter(mode="audit").count()
                honor_enrolled = enrollments.filter(mode="honor").count()
                # Since every verified enrollment has 1 and only 1 cert item, let's just query those
                verified_enrollments = CertificateItem.objects.filter(course_id=course_id, mode="verified", status="purchased")
                verified_enrolled = verified_enrollments.count()
                gross_rev_temp = CertificateItem.objects.filter(course_id=course_id, mode="verified", status="purchased").aggregate(Sum('unit_cost'))
                gross_rev = gross_rev_temp['unit_cost__sum']
                gross_rev_over_min = gross_rev - (CourseMode.objects.get(course_id=course_id, mode_slug="verified").min_price * verified_enrolled)
                refunded_enrollments = CertificateItem.objects.filter(course_id='course_id', mode="verified", status="refunded")
                number_of_refunds = refunded_enrollments.count()
                dollars_refunded_temp = refunded_enrollments.aggregate(Sum('unit_cost'))
                if dollars_refunded_temp['unit_cost__sum'] is None:
                    dollars_refunded = Decimal(0.00)
                else:
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
        return results

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

    def csv_report_row(self, item):
        return item


class UniversityRevenueShareReport(Report):
    """
    Subclass of Report, used to generate University Revenue Share Reports for finance purposes.
    """
    def get_report_data(self, start_date, end_date, start_letter=None, end_letter=None):
        results = []
        for course_id in settings.COURSE_LISTINGS['default']:
            if (start_letter.lower() <= course_id.lower()) and (end_letter.lower() >= course_id.lower()):
                try:
                    cur_course = get_course_by_id(course_id)
                except:
                    break
                university = cur_course.org
                course = cur_course.number + " " + cur_course.display_name
                num_transactions = 0  # TODO clarify with billing what transactions are included in this (purchases? refunds? etc)

                all_paid_certs = CertificateItem.objects.filter(course_id=course_id, status="purchased")

                total_payments_collected_temp = all_paid_certs.aggregate(Sum('unit_cost'))
                if total_payments_collected_temp['unit_cost__sum'] is None:
                    total_payments_collected = Decimal(0.00)
                else:
                    total_payments_collected = total_payments_collected_temp['unit_cost__sum']

                total_service_fees_temp = all_paid_certs.aggregate(Sum('service_fee'))
                if total_service_fees_temp['service_fee__sum'] is None:
                    service_fees = Decimal(0.00)
                else:
                    service_fees = total_service_fees_temp['service_fee__sum']

                refunded_enrollments = CertificateItem.objects.filter(course_id=course_id, status="refunded")
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

        return results

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

    def csv_report_row(self, item):
        return item
