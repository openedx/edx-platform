"""
Tests for Pdf file
"""
from datetime import datetime
from django.test.utils import override_settings
from django.conf import settings
import unittest
from io import BytesIO
from shoppingcart.pdf import PDFInvoice
from shoppingcart.utils import parse_pages

PDF_RECEIPT_DISCLAIMER_TEXT = "THE SITE AND ANY INFORMATION, CONTENT OR SERVICES MADE AVAILABLE ON OR THROUGH " \
    "THE SITE ARE PROVIDED \"AS IS\" AND \"AS AVAILABLE\" WITHOUT WARRANTY OF ANY KIND (EXPRESS, IMPLIED OR" \
    " OTHERWISE), INCLUDING, WITHOUT LIMITATION, ANY IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A " \
    "PARTICULAR PURPOSE AND NON-INFRINGEMENT, EXCEPT INSOFAR AS ANY SUCH IMPLIED WARRANTIES MAY NOT BE DISCLAIMED" \
    " UNDER APPLICABLE LAW."
PDF_RECEIPT_BILLING_ADDRESS = "edX\n141 Portland St.\n9th Floor\nCambridge,\nMA 02139"
PDF_RECEIPT_FOOTER_TEXT = "EdX offers online courses that include opportunities for professor-to-student and" \
    " student-to-student interactivity, individual assessment of a student's work and, for students who demonstrate" \
    " their mastery of subjects, a certificate of achievement or other acknowledgment."
PDF_RECEIPT_TAX_ID = "46-0807740"
PDF_RECEIPT_TAX_ID_LABEL = "edX Tax ID"
PDF_RECEIPT_TERMS_AND_CONDITIONS = "Enrollments:\nEnrollments must be completed within 7 full days from the course " \
    "start date.\nPayment Terms:\nPayment is due immediately. Preferred method of payment is wire transfer. Full " \
    "instructions and remittance details will be included on your official invoice. Please note that our terms are " \
    "net zero. For questions regarding payment instructions or extensions, please contact " \
    "onlinex-registration@mit.edu and include the words \"payment question\" in your subject line.\nCancellations:" \
    "\nCancellation requests must be submitted to onlinex-registration@mit.edu 14 days prior to the course start " \
    "date to be eligible for a refund. If you submit a cancellation request within 14 days prior to the course start " \
    "date, you will not be eligible for a refund. Please see our Terms of Service page for full details." \
    "\nSubstitutions:\nThe MIT Professional Education Online X Programs office must receive substitution requests " \
    "before the course start date in order for the request to be considered. Please email " \
    "onlinex-registration@mit.edu to request a substitution.Please see our Terms of Service page for our detailed " \
    "policies, including terms and conditions of use."


class TestPdfFile(unittest.TestCase):
    """
    Unit test cases for pdf file generation
    """
    def setUp(self):
        super(TestPdfFile, self).setUp()

        self.items_data = [self.get_item_data(1)]
        self.item_id = '1'
        self.date = datetime.now()
        self.is_invoice = False
        self.total_cost = 1000
        self.payment_received = 1000
        self.balance = 0
        self.pdf_buffer = BytesIO()

    def get_item_data(self, index, discount=0):
        """
        return the dictionary with the dummy data
        """
        return {
            'item_description': 'Course %s Description' % index,
            'quantity': index,
            'list_price': 10,
            'discount': discount,
            'item_total': 10
        }

    @override_settings(
        PDF_RECEIPT_DISCLAIMER_TEXT=PDF_RECEIPT_DISCLAIMER_TEXT,
        PDF_RECEIPT_BILLING_ADDRESS=PDF_RECEIPT_BILLING_ADDRESS,
        PDF_RECEIPT_FOOTER_TEXT=PDF_RECEIPT_FOOTER_TEXT,
        PDF_RECEIPT_TAX_ID=PDF_RECEIPT_TAX_ID,
        PDF_RECEIPT_TAX_ID_LABEL=PDF_RECEIPT_TAX_ID_LABEL,
        PDF_RECEIPT_TERMS_AND_CONDITIONS=PDF_RECEIPT_TERMS_AND_CONDITIONS,
    )
    def test_pdf_receipt_configured_generation(self):
        PDFInvoice(
            items_data=self.items_data,
            item_id=self.item_id,
            date=self.date,
            is_invoice=self.is_invoice,
            total_cost=self.total_cost,
            payment_received=self.payment_received,
            balance=self.balance
        ).generate_pdf(self.pdf_buffer)
        pdf_content = parse_pages(self.pdf_buffer, 'test_pass')
        self.assertTrue(any('Receipt' in s for s in pdf_content))
        self.assertTrue(any(str(self.total_cost) in s for s in pdf_content))
        self.assertTrue(any(str(self.payment_received) in s for s in pdf_content))
        self.assertTrue(any(str(self.balance) in s for s in pdf_content))
        self.assertFalse(any('edX Tax ID' in s for s in pdf_content))

        # PDF_RECEIPT_TERMS_AND_CONDITIONS not displayed in the receipt pdf
        self.assertFalse(any(
            'Enrollments:\nEnrollments must be completed within 7 full days from the course'
            ' start date.\nPayment Terms:\nPayment is due immediately.' in s for s in pdf_content
        ))
        self.assertTrue(any('edX\n141 Portland St.\n9th Floor\nCambridge,\nMA 02139' in s for s in pdf_content))

    def test_pdf_receipt_not_configured_generation(self):
        PDFInvoice(
            items_data=self.items_data,
            item_id=self.item_id,
            date=self.date,
            is_invoice=self.is_invoice,
            total_cost=self.total_cost,
            payment_received=self.payment_received,
            balance=self.balance
        ).generate_pdf(self.pdf_buffer)
        pdf_content = parse_pages(self.pdf_buffer, 'test_pass')
        self.assertTrue(any('Receipt' in s for s in pdf_content))
        self.assertTrue(any(settings.PDF_RECEIPT_DISCLAIMER_TEXT in s for s in pdf_content))
        self.assertTrue(any(settings.PDF_RECEIPT_BILLING_ADDRESS in s for s in pdf_content))
        self.assertTrue(any(settings.PDF_RECEIPT_FOOTER_TEXT in s for s in pdf_content))
        # PDF_RECEIPT_TERMS_AND_CONDITIONS not displayed in the receipt pdf
        self.assertFalse(any(settings.PDF_RECEIPT_TERMS_AND_CONDITIONS in s for s in pdf_content))

    @override_settings(
        PDF_RECEIPT_DISCLAIMER_TEXT=PDF_RECEIPT_DISCLAIMER_TEXT,
        PDF_RECEIPT_BILLING_ADDRESS=PDF_RECEIPT_BILLING_ADDRESS,
        PDF_RECEIPT_FOOTER_TEXT=PDF_RECEIPT_FOOTER_TEXT,
        PDF_RECEIPT_TAX_ID=PDF_RECEIPT_TAX_ID,
        PDF_RECEIPT_TAX_ID_LABEL=PDF_RECEIPT_TAX_ID_LABEL,
        PDF_RECEIPT_TERMS_AND_CONDITIONS=PDF_RECEIPT_TERMS_AND_CONDITIONS,
    )
    def test_pdf_receipt_file_item_data_pagination(self):
        for i in range(2, 50):
            self.items_data.append(self.get_item_data(i))

        PDFInvoice(
            items_data=self.items_data,
            item_id=self.item_id,
            date=self.date,
            is_invoice=self.is_invoice,
            total_cost=self.total_cost,
            payment_received=self.payment_received,
            balance=self.balance
        ).generate_pdf(self.pdf_buffer)

        pdf_content = parse_pages(self.pdf_buffer, 'test_pass')
        self.assertTrue(any('Receipt' in s for s in pdf_content))
        self.assertTrue(any('Page 3 of 3' in s for s in pdf_content))

    def test_pdf_receipt_file_totals_pagination(self):
        for i in range(2, 48):
            self.items_data.append(self.get_item_data(i))

        PDFInvoice(
            items_data=self.items_data,
            item_id=self.item_id,
            date=self.date,
            is_invoice=self.is_invoice,
            total_cost=self.total_cost,
            payment_received=self.payment_received,
            balance=self.balance
        ).generate_pdf(self.pdf_buffer)

        pdf_content = parse_pages(self.pdf_buffer, 'test_pass')
        self.assertTrue(any('Receipt' in s for s in pdf_content))
        self.assertTrue(any('Page 3 of 3' in s for s in pdf_content))

    @override_settings(PDF_RECEIPT_LOGO_PATH='wrong path')
    def test_invalid_image_path(self):
        PDFInvoice(
            items_data=self.items_data,
            item_id=self.item_id,
            date=self.date,
            is_invoice=self.is_invoice,
            total_cost=self.total_cost,
            payment_received=self.payment_received,
            balance=self.balance
        ).generate_pdf(self.pdf_buffer)

        pdf_content = parse_pages(self.pdf_buffer, 'test_pass')
        self.assertTrue(any('Receipt' in s for s in pdf_content))

    def test_pdf_receipt_file_footer_pagination(self):
        for i in range(2, 44):
            self.items_data.append(self.get_item_data(i))

        PDFInvoice(
            items_data=self.items_data,
            item_id=self.item_id,
            date=self.date,
            is_invoice=self.is_invoice,
            total_cost=self.total_cost,
            payment_received=self.payment_received,
            balance=self.balance
        ).generate_pdf(self.pdf_buffer)

        pdf_content = parse_pages(self.pdf_buffer, 'test_pass')
        self.assertTrue(any('Receipt' in s for s in pdf_content))

    @override_settings(
        PDF_RECEIPT_DISCLAIMER_TEXT=PDF_RECEIPT_DISCLAIMER_TEXT,
        PDF_RECEIPT_BILLING_ADDRESS=PDF_RECEIPT_BILLING_ADDRESS,
        PDF_RECEIPT_FOOTER_TEXT=PDF_RECEIPT_FOOTER_TEXT,
        PDF_RECEIPT_TAX_ID=PDF_RECEIPT_TAX_ID,
        PDF_RECEIPT_TAX_ID_LABEL=PDF_RECEIPT_TAX_ID_LABEL,
        PDF_RECEIPT_TERMS_AND_CONDITIONS=PDF_RECEIPT_TERMS_AND_CONDITIONS,
    )
    def test_pdf_invoice_with_settings_from_patch(self):
        self.is_invoice = True
        PDFInvoice(
            items_data=self.items_data,
            item_id=self.item_id,
            date=self.date,
            is_invoice=self.is_invoice,
            total_cost=self.total_cost,
            payment_received=self.payment_received,
            balance=self.balance
        ).generate_pdf(self.pdf_buffer)
        pdf_content = parse_pages(self.pdf_buffer, 'test_pass')
        self.assertTrue(any('46-0807740' in s for s in pdf_content))
        self.assertTrue(any('Invoice' in s for s in pdf_content))
        self.assertTrue(any(str(self.total_cost) in s for s in pdf_content))
        self.assertTrue(any(str(self.payment_received) in s for s in pdf_content))
        self.assertTrue(any(str(self.balance) in s for s in pdf_content))
        self.assertTrue(any('edX Tax ID' in s for s in pdf_content))
        self.assertTrue(any(
            'Enrollments:\nEnrollments must be completed within 7 full'
            ' days from the course start date.\nPayment Terms:\nPayment'
            ' is due immediately.' in s for s in pdf_content))

    def test_pdf_invoice_with_default_settings(self):
        self.is_invoice = True
        PDFInvoice(
            items_data=self.items_data,
            item_id=self.item_id,
            date=self.date,
            is_invoice=self.is_invoice,
            total_cost=self.total_cost,
            payment_received=self.payment_received,
            balance=self.balance
        ).generate_pdf(self.pdf_buffer)

        pdf_content = parse_pages(self.pdf_buffer, 'test_pass')
        self.assertTrue(any(settings.PDF_RECEIPT_TAX_ID in s for s in pdf_content))
        self.assertTrue(any('Invoice' in s for s in pdf_content))
        self.assertTrue(any(settings.PDF_RECEIPT_TERMS_AND_CONDITIONS in s for s in pdf_content))
