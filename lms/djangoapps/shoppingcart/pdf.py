"""
Template for PDF Receipt/Invoice Generation
"""
from PIL import Image
import logging
from reportlab.lib import colors
from django.conf import settings
from django.utils.translation import ugettext as _
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
from reportlab.platypus.tables import Table, TableStyle
from xmodule.modulestore.django import ModuleI18nService
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

log = logging.getLogger("PDF Generation")


class NumberedCanvas(Canvas):
    """
    Canvas child class with auto page-numbering.
    """
    def __init__(self, *args, **kwargs):
        """
            __init__
        """
        Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def insert_page_break(self):
        """
        Starts a new page.
        """
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def current_page_count(self):
        """
        Returns the page count in the current pdf document.
        """
        return len(self._saved_page_states) + 1

    def save(self):
        """
            Adds page numbering to each page (page x of y)
        """
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            if num_pages > 1:
                self.draw_page_number(num_pages)
            Canvas.showPage(self)
        Canvas.save(self)

    def draw_page_number(self, page_count):
        """
        Draws the String "Page x of y" at the bottom right of the document.
        """
        self.setFontSize(7)
        self.drawRightString(
            200 * mm,
            12 * mm,
            _("Page {page_number} of {page_count}").format(page_number=self._pageNumber, page_count=page_count)
        )


class PDFInvoice(object):
    """
    PDF Generation Class
    """
    def __init__(self, items_data, item_id, date, is_invoice, total_cost, payment_received, balance):
        """
        Accepts the following positional arguments

        items_data - A list having the following items for each row.
            item_description - String
            quantity - Integer
            list_price - float
            discount - float
            item_total - float
        id - String
        date - datetime
        is_invoice - boolean - True (for invoice) or False (for Receipt)
        total_cost - float
        payment_received - float
        balance - float
        """

        # From settings
        self.currency = settings.PAID_COURSE_REGISTRATION_CURRENCY[1]
        self.logo_path = configuration_helpers.get_value("PDF_RECEIPT_LOGO_PATH", settings.PDF_RECEIPT_LOGO_PATH)
        self.cobrand_logo_path = configuration_helpers.get_value(
            "PDF_RECEIPT_COBRAND_LOGO_PATH", settings.PDF_RECEIPT_COBRAND_LOGO_PATH
        )
        self.tax_label = configuration_helpers.get_value("PDF_RECEIPT_TAX_ID_LABEL", settings.PDF_RECEIPT_TAX_ID_LABEL)
        self.tax_id = configuration_helpers.get_value("PDF_RECEIPT_TAX_ID", settings.PDF_RECEIPT_TAX_ID)
        self.footer_text = configuration_helpers.get_value("PDF_RECEIPT_FOOTER_TEXT", settings.PDF_RECEIPT_FOOTER_TEXT)
        self.disclaimer_text = configuration_helpers.get_value(
            "PDF_RECEIPT_DISCLAIMER_TEXT", settings.PDF_RECEIPT_DISCLAIMER_TEXT,
        )
        self.billing_address_text = configuration_helpers.get_value(
            "PDF_RECEIPT_BILLING_ADDRESS", settings.PDF_RECEIPT_BILLING_ADDRESS
        )
        self.terms_conditions_text = configuration_helpers.get_value(
            "PDF_RECEIPT_TERMS_AND_CONDITIONS", settings.PDF_RECEIPT_TERMS_AND_CONDITIONS
        )
        self.brand_logo_height = configuration_helpers.get_value(
            "PDF_RECEIPT_LOGO_HEIGHT_MM", settings.PDF_RECEIPT_LOGO_HEIGHT_MM
        ) * mm
        self.cobrand_logo_height = configuration_helpers.get_value(
            "PDF_RECEIPT_COBRAND_LOGO_HEIGHT_MM", settings.PDF_RECEIPT_COBRAND_LOGO_HEIGHT_MM
        ) * mm

        # From Context
        self.items_data = items_data
        self.item_id = item_id
        self.date = ModuleI18nService().strftime(date, 'SHORT_DATE')
        self.is_invoice = is_invoice
        self.total_cost = '{currency}{amount:.2f}'.format(currency=self.currency, amount=total_cost)
        self.payment_received = '{currency}{amount:.2f}'.format(currency=self.currency, amount=payment_received)
        self.balance = '{currency}{amount:.2f}'.format(currency=self.currency, amount=balance)

        # initialize the pdf variables
        self.margin = 15 * mm
        self.page_width = letter[0]
        self.page_height = letter[1]
        self.min_clearance = 3 * mm
        self.second_page_available_height = ''
        self.second_page_start_y_pos = ''
        self.first_page_available_height = ''
        self.pdf = None

    def is_on_first_page(self):
        """
        Returns True if it's the first page of the pdf, False otherwise.
        """
        return self.pdf.current_page_count() == 1

    def generate_pdf(self, file_buffer):
        """
        Takes in a buffer and puts the generated pdf into that buffer.
        """
        self.pdf = NumberedCanvas(file_buffer, pagesize=letter)

        self.draw_border()
        y_pos = self.draw_logos()
        self.second_page_available_height = y_pos - self.margin - self.min_clearance
        self.second_page_start_y_pos = y_pos

        y_pos = self.draw_title(y_pos)
        self.first_page_available_height = y_pos - self.margin - self.min_clearance

        y_pos = self.draw_course_info(y_pos)
        y_pos = self.draw_totals(y_pos)
        self.draw_footer(y_pos)

        self.pdf.insert_page_break()
        self.pdf.save()

    def draw_border(self):
        """
        Draws a big border around the page leaving a margin of 15 mm on each side.
        """
        self.pdf.setStrokeColorRGB(0.5, 0.5, 0.5)
        self.pdf.setLineWidth(0.353 * mm)

        self.pdf.rect(self.margin, self.margin,
                      self.page_width - (self.margin * 2), self.page_height - (self.margin * 2),
                      stroke=True, fill=False)

    @staticmethod
    def load_image(img_path):
        """
        Loads an image given a path. An absolute path is assumed.
        If the path points to an image file, it loads and returns the Image object, None otherwise.
        """
        try:
            img = Image.open(img_path)
        except IOError, ex:
            log.exception('Pdf unable to open the image file: %s', str(ex))
            img = None

        return img

    def draw_logos(self):
        """
        Draws logos.
        """
        horizontal_padding_from_border = self.margin + 9 * mm
        vertical_padding_from_border = 11 * mm
        img_y_pos = self.page_height - (
            self.margin + vertical_padding_from_border + max(self.cobrand_logo_height, self.brand_logo_height)
        )

        # Left-Aligned cobrand logo
        if self.cobrand_logo_path:
            cobrand_img = self.load_image(self.cobrand_logo_path)
            if cobrand_img:
                img_width = float(cobrand_img.size[0]) / (float(cobrand_img.size[1]) / self.cobrand_logo_height)
                self.pdf.drawImage(cobrand_img.filename, horizontal_padding_from_border, img_y_pos, img_width,
                                   self.cobrand_logo_height, mask='auto')

        # Right aligned brand logo
        if self.logo_path:
            logo_img = self.load_image(self.logo_path)
            if logo_img:
                img_width = float(logo_img.size[0]) / (float(logo_img.size[1]) / self.brand_logo_height)
                self.pdf.drawImage(
                    logo_img.filename,
                    self.page_width - (horizontal_padding_from_border + img_width),
                    img_y_pos,
                    img_width,
                    self.brand_logo_height,
                    mask='auto'
                )

        return img_y_pos - self.min_clearance

    def draw_title(self, y_pos):
        """
        Draws the title, order/receipt ID and the date.
        """
        if self.is_invoice:
            title = (_('Invoice'))
            id_label = (_('Invoice'))
        else:
            title = (_('Receipt'))
            id_label = (_('Order'))

        # Draw Title "RECEIPT" OR "INVOICE"
        vertical_padding = 5 * mm
        horizontal_padding_from_border = self.margin + 9 * mm
        font_size = 21
        self.pdf.setFontSize(font_size)
        self.pdf.drawString(horizontal_padding_from_border, y_pos - vertical_padding - font_size / 2, title)
        y_pos = y_pos - vertical_padding - font_size / 2 - self.min_clearance

        horizontal_padding_from_border = self.margin + 11 * mm
        font_size = 12
        self.pdf.setFontSize(font_size)
        y_pos = y_pos - font_size / 2 - vertical_padding
        # Draw Order/Invoice No.
        self.pdf.drawString(horizontal_padding_from_border, y_pos,
                            _(u'{id_label} # {item_id}').format(id_label=id_label, item_id=self.item_id))
        y_pos = y_pos - font_size / 2 - vertical_padding
        # Draw Date
        self.pdf.drawString(
            horizontal_padding_from_border, y_pos, _(u'Date: {date}').format(date=self.date)
        )

        return y_pos - self.min_clearance

    def draw_course_info(self, y_pos):
        """
        Draws the main table containing the data items.
        """
        course_items_data = [
            ['', (_('Description')), (_('Quantity')), (_('List Price\nper item')), (_('Discount\nper item')),
             (_('Amount')), '']
        ]
        for row_item in self.items_data:
            course_items_data.append([
                '',
                Paragraph(row_item['item_description'], getSampleStyleSheet()['Normal']),
                row_item['quantity'],
                '{currency}{list_price:.2f}'.format(list_price=row_item['list_price'], currency=self.currency),
                '{currency}{discount:.2f}'.format(discount=row_item['discount'], currency=self.currency),
                '{currency}{item_total:.2f}'.format(item_total=row_item['item_total'], currency=self.currency),
                ''
            ])

        padding_width = 7 * mm
        desc_col_width = 60 * mm
        qty_col_width = 26 * mm
        list_price_col_width = 21 * mm
        discount_col_width = 21 * mm
        amount_col_width = 40 * mm
        course_items_table = Table(
            course_items_data,
            [
                padding_width,
                desc_col_width,
                qty_col_width,
                list_price_col_width,
                discount_col_width,
                amount_col_width,
                padding_width
            ],
            splitByRow=1,
            repeatRows=1
        )

        course_items_table.setStyle(TableStyle([
            #List Price, Discount, Amount data items
            ('ALIGN', (3, 1), (5, -1), 'RIGHT'),

            # Amount header
            ('ALIGN', (5, 0), (5, 0), 'RIGHT'),

            # Amount column (header + data items)
            ('RIGHTPADDING', (5, 0), (5, -1), 7 * mm),

            # Quantity, List Price, Discount header
            ('ALIGN', (2, 0), (4, 0), 'CENTER'),

            # Description header
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),

            # Quantity data items
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),

            # Lines below the header and at the end of the table.
            ('LINEBELOW', (0, 0), (-1, 0), 1.00, '#cccccc'),
            ('LINEBELOW', (0, -1), (-1, -1), 1.00, '#cccccc'),

            # Innergrid around the data rows.
            ('INNERGRID', (1, 1), (-2, -1), 0.50, '#cccccc'),

            # Entire table
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 2 * mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2 * mm),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ]))
        rendered_width, rendered_height = course_items_table.wrap(0, 0)
        table_left_padding = (self.page_width - rendered_width) / 2

        split_tables = course_items_table.split(0, self.first_page_available_height)
        if len(split_tables) > 1:
            # The entire Table won't fit in the available space and requires splitting.
            # Draw the part that can fit, start a new page
            # and repeat the process with the rest of the table.
            split_table = split_tables[0]
            __, rendered_height = split_table.wrap(0, 0)
            split_table.drawOn(self.pdf, table_left_padding, y_pos - rendered_height)

            self.prepare_new_page()
            split_tables = split_tables[1].split(0, self.second_page_available_height)
            while len(split_tables) > 1:
                split_table = split_tables[0]
                __, rendered_height = split_table.wrap(0, 0)
                split_table.drawOn(self.pdf, table_left_padding, self.second_page_start_y_pos - rendered_height)

                self.prepare_new_page()
                split_tables = split_tables[1].split(0, self.second_page_available_height)
            split_table = split_tables[0]
            __, rendered_height = split_table.wrap(0, 0)
            split_table.drawOn(self.pdf, table_left_padding, self.second_page_start_y_pos - rendered_height)
        else:
            # Table will fit without the need for splitting.
            course_items_table.drawOn(self.pdf, table_left_padding, y_pos - rendered_height)

        if not self.is_on_first_page():
            y_pos = self.second_page_start_y_pos

        return y_pos - rendered_height - self.min_clearance

    def prepare_new_page(self):
        """
        Inserts a new page and includes the border and the logos.
        """
        self.pdf.insert_page_break()
        self.draw_border()
        y_pos = self.draw_logos()
        return y_pos

    def draw_totals(self, y_pos):
        """
        Draws the boxes containing the totals and the tax id.
        """
        totals_data = [
            [(_('Total')), self.total_cost],
            [(_('Payment Received')), self.payment_received],
            [(_('Balance')), self.balance]
        ]

        if self.is_invoice:
            # only print TaxID if we are generating an Invoice
            totals_data.append(
                ['', '{tax_label}:  {tax_id}'.format(tax_label=self.tax_label, tax_id=self.tax_id)]
            )

        heights = 8 * mm
        totals_table = Table(totals_data, 40 * mm, heights)

        styles = [
            # Styling for the totals table.
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),

            # Styling for the Amounts cells
            # NOTE: since we are not printing the TaxID for Credit Card
            # based receipts, we need to change the cell range for
            # these formatting rules
            ('RIGHTPADDING', (-1, 0), (-1, 2), 7 * mm),
            ('GRID', (-1, 0), (-1, 2), 3.0, colors.white),
            ('BACKGROUND', (-1, 0), (-1, 2), '#EEEEEE'),
        ]

        totals_table.setStyle(TableStyle(styles))

        __, rendered_height = totals_table.wrap(0, 0)

        left_padding = 97 * mm
        if y_pos - (self.margin + self.min_clearance) <= rendered_height:
            # if space left on page is smaller than the rendered height, render the table on the next page.
            self.prepare_new_page()
            totals_table.drawOn(self.pdf, self.margin + left_padding, self.second_page_start_y_pos - rendered_height)
            return self.second_page_start_y_pos - rendered_height - self.min_clearance
        else:
            totals_table.drawOn(self.pdf, self.margin + left_padding, y_pos - rendered_height)
            return y_pos - rendered_height - self.min_clearance

    def draw_footer(self, y_pos):
        """
        Draws the footer.
        """

        para_style = getSampleStyleSheet()['Normal']
        para_style.fontSize = 8

        footer_para = Paragraph(self.footer_text.replace("\n", "<br/>"), para_style)
        disclaimer_para = Paragraph(self.disclaimer_text.replace("\n", "<br/>"), para_style)
        billing_address_para = Paragraph(self.billing_address_text.replace("\n", "<br/>"), para_style)

        footer_data = [
            ['', footer_para],
            [(_('Billing Address')), ''],
            ['', billing_address_para],
            [(_('Disclaimer')), ''],
            ['', disclaimer_para]
        ]

        footer_style = [
            # Styling for the entire footer table.
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (-1, -1), '#AAAAAA'),

            # Billing Address Header styling
            ('LEFTPADDING', (0, 1), (0, 1), 5 * mm),

            # Disclaimer Header styling
            ('LEFTPADDING', (0, 3), (0, 3), 5 * mm),
            ('TOPPADDING', (0, 3), (0, 3), 2 * mm),

            # Footer Body styling
            # ('BACKGROUND', (1, 0), (1, 0), '#EEEEEE'),

            # Billing Address Body styling
            ('BACKGROUND', (1, 2), (1, 2), '#EEEEEE'),

            # Disclaimer Body styling
            ('BACKGROUND', (1, 4), (1, 4), '#EEEEEE'),
        ]

        if self.is_invoice:
            terms_conditions_para = Paragraph(self.terms_conditions_text.replace("\n", "<br/>"), para_style)
            footer_data.append([(_('TERMS AND CONDITIONS')), ''])
            footer_data.append(['', terms_conditions_para])

            # TERMS AND CONDITIONS header styling
            footer_style.append(('LEFTPADDING', (0, 5), (0, 5), 5 * mm))
            footer_style.append(('TOPPADDING', (0, 5), (0, 5), 2 * mm))

            # TERMS AND CONDITIONS body styling
            footer_style.append(('BACKGROUND', (1, 6), (1, 6), '#EEEEEE'))

        footer_table = Table(footer_data, [5 * mm, 176 * mm])

        footer_table.setStyle(TableStyle(footer_style))
        __, rendered_height = footer_table.wrap(0, 0)

        if y_pos - (self.margin + self.min_clearance) <= rendered_height:
            self.prepare_new_page()

        footer_table.drawOn(self.pdf, self.margin, self.margin + 5 * mm)
