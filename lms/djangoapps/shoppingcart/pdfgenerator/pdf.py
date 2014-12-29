# -*- coding: utf-8 -*-
from PIL import Image
from reportlab.lib import colors

from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm, inch
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus.tables import Table, TableStyle

import locale
import warnings

_ = lambda x: x

class UnicodeProperty(object):
    _attrs = ()

    def __setattr__(self, key, value):
        if key in self._attrs:
            value = unicode(value)
        self.__dict__[key] = value

class NumberedCanvas(Canvas):
    def __init__(self, *args, **kwargs):
        Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        """add page info to each page (page x of y)"""
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            if num_pages > 1:
                self.draw_page_number(num_pages)
            Canvas.showPage(self)
        Canvas.save(self)

    def draw_page_number(self, page_count):
        self.setFont("DejaVu", 7)
        self.drawRightString(200*mm, 20*mm,
            _("Page %(page_number)d of %(page_count)d") % {"page_number": self._pageNumber, "page_count": page_count})


class SimpleInvoice(UnicodeProperty):
    def __init__(self, items_data, id, date, title, is_invoice, total_cost, wl_logo, edx_logo, payment_received='0.00', balance='NIL'):
        self.items_data = items_data
        self.id = id
        self.date = date
        self.title = title
        self.is_invoice = is_invoice
        self.total_cost = total_cost
        self.payment_received = payment_received
        self.balance = balance
        self.wl_logo = wl_logo
        self.edx_logo = edx_logo

    def prepare_invoice_draw(self):
        self.MARGIN = 15
        FONT_PATH = '/usr/share/fonts/truetype/ttf-dejavu/DejaVuSans.ttf'
        FONT_BOLD_PATH = '/usr/share/fonts/truetype/ttf-dejavu/DejaVuSans-Bold.ttf'

        pdfmetrics.registerFont(TTFont('DejaVu', FONT_PATH))
        pdfmetrics.registerFont(TTFont('DejaVu-Bold', FONT_BOLD_PATH))

        self.pdf = NumberedCanvas(self.filename, pagesize=letter)

        self.pdf.setFont('DejaVu', 15)
        self.pdf.setStrokeColorRGB(0.5, 0.5, 0.5)
        self.pdf.setLineWidth(0.353 * mm)

    def gen(self, filename):
        self.filename = filename

        self.prepare_invoice_draw()

        self.drawBorders()
        self.drawLogos()

        self.drawTitle()
        y_pos = self.drawCourseInfo()
        y_pos = self.show_totals(y_pos)
        self.draw_footer(y_pos)
        # self.pdf.setFillColorRGB(0, 0, 0)

        self.pdf.showPage()
        self.pdf.save()

    #############################################################
    ## Draw methods
    #############################################################

    def drawBorders(self):
        # Borders
        self.pdf.rect(self.MARGIN * mm, self.MARGIN * mm,
                      186 * mm, 249 * mm, stroke=True, fill=False)

    def drawLogos(self):
        im = Image.open(self.wl_logo)
        height = 12
        top = 240
        width = float(im.size[0]) / (float(im.size[1])/height)
        self.pdf.drawImage(self.wl_logo, (self.MARGIN + 9) * mm, top * mm, width * mm, height*mm, mask='auto')

        im = Image.open(self.edx_logo)
        width = float(im.size[0]) / (float(im.size[1])/height)
        self.pdf.drawImage(self.edx_logo, (self.MARGIN + 177 -width) * mm, top * mm, width * mm, height*mm, mask='auto')

    def drawTitle(self):
        self.pdf.setFont('DejaVu', 21)
        self.pdf.drawCentredString(108*mm, (230)*mm, self.title)

        self.pdf.setFont('DejaVu', 10)
        self.pdf.drawString((self.MARGIN + 8) * mm, 220 * mm, _(u'Order # ' + self.id))
        self.pdf.drawRightString((self.MARGIN + 177) * mm, 220 * mm, _(u'Date ' + self.date))

    def drawCourseInfo(self):
        data = [['', 'Description', 'Quantity', 'List Price\nper item', 'Discount\nper item', 'Amount', '']]
        for row in self.items_data:
            data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
            data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
            data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
            data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
            data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
            data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
            data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
            data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
            data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
            data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
            data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
            data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
            data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
            data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
            data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
            data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
            data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
            data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
            data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
            data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
            data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
            data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
            data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
            data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
            data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
            data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
            data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
            data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
            data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
            data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
            data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
            data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
            data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
            data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
            data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
            data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
            data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
            data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
            data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
            data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
            data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
            data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
            data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
            data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
            data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
            data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
            # data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
            # data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
            data.append(['', row['course_name'], row['quantity'], row['list_price'], row['discount'], row['total'], ''])
        # data= [['', 'Description', 'Quantity', 'List Price\nper item', 'Discount\nper item', 'Amount', ''],
        # ['', 'Demo Course 1', '2', '$100.00', '$0.00', '$200.00', ''],
        # ['', 'Demo Course 2', '2', '$1000.00', '$10.00', '$1980.00', ''],
        # ['', 'Demo Course 3', '5', '$500.00', '$0.00', '$2500.00', ''],
        # ['', 'Demo Course 4', '2', '$10000.00', '$150.00', '$19700.00', '']
        # ]
        heights = [12*mm]
        heights.extend((len(data) - 1 )*[8*mm])
        t=Table(data,[7*mm, 60*mm, 26*mm, 21*mm,21*mm, 40*mm, 7*mm], heights, splitByRow=1, repeatRows=1)

        t.setStyle(TableStyle([
            ('ALIGN',(3,1),(5,-1),'RIGHT'),
            ('RIGHTPADDING', (5,1), (5,-1), 7*mm),
            ('ALIGN',(2,0),(-1,0),'CENTER'),
            ('ALIGN',(1,0),(0,0),'LEFT'),
            ('ALIGN',(1,1),(1,-1),'LEFT'),
            ('ALIGN',(2,1),(2,-1),'CENTER'),
            ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
            ('TEXTCOLOR',(0,-1),(-1,-1),colors.black),
            ('LINEBELOW', (0,0), (-1,0), 1.00, colors.black),
            ('LINEBELOW', (0,-1), (-1,-1), 1.00, colors.black),
            ('INNERGRID', (1,1), (-2,-1), 0.50, colors.black),
        ]))
        t.wrap(0,0)


        first_page_available_height = 185*mm
        remainaing_pages_available_height = 205*mm
        first_page_top = 215*mm
        next_pages_top = 235*mm

        split_tables = t.split(0, first_page_available_height)
        last_table_height = 0
        is_on_first_page = True
        if len(split_tables)>1:
            split_table = split_tables[0]
            split_table.wrap(0,0)
            split_table.drawOn(self.pdf, (self.MARGIN + 2) * mm, first_page_top - split_table._height)

            self.prepare_new_page()
            is_on_first_page = False
            split_tables = split_tables[1].split(0, remainaing_pages_available_height)
            while len(split_tables) > 1:
                split_table = split_tables[0]
                split_table.wrap(0,0)
                split_table.drawOn(self.pdf, (self.MARGIN + 2) * mm, next_pages_top - split_table._height)

                self.prepare_new_page()
                split_tables = split_tables[1].split(0, remainaing_pages_available_height)
            split_table = split_tables[0]
            split_table.wrap(0,0)
            split_table.drawOn(self.pdf, (self.MARGIN + 2) * mm, next_pages_top - split_table._height)
            last_table_height = split_table._height
        else:
            split_table = split_tables[0]
            split_table.wrap(0,0)
            split_table.drawOn(self.pdf, (self.MARGIN + 2) * mm, first_page_top -split_table._height)
            last_table_height = split_table._height

        if is_on_first_page:
            return first_page_top - last_table_height
        else:
            return next_pages_top - last_table_height

    def prepare_new_page(self):
        self.pdf.showPage()
        self.drawBorders()
        self.drawLogos()

    def show_totals(self, y_pos):
        data= [['Total', self.total_cost]]
        if (self.is_invoice):
            data.append(['Payment Received', self.payment_received])
            data.append(['Balance', self.balance])

        data.append(['', 'EdX Tax ID:  46-0807740'])
        
        heights = 8*mm
        t=Table(data,40*mm, heights)

        t.setStyle(TableStyle([
            ('ALIGN',(0,0),(-1,-1),'RIGHT'),
            ('RIGHTPADDING', (-1,0), (-1,-2), 7*mm),
            ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
            ('TEXTCOLOR',(0,-1),(-1,-1),colors.black),
            ('GRID', (-1,0), (-1,-2), 0.50, colors.black),
            ('BACKGROUND', (-1,0), (-1,-2), colors.lightgrey),
        ]))
        t.wrap(0,0)
        t.drawOn(self.pdf, (self.MARGIN + 97) * mm, y_pos - t._height - 5*mm)
        return y_pos - t._height - 5*mm


    def draw_footer(self, y_pos):
        service_provider_text = """EdX offers online courses that include opportunities for professor-to-student and student-to-student interactivity, individual assessment of a student's work and, for students who demonstrate their mastery of subjects, a certificate of achievement or other acknowledgment."""

        disclaimer_text = """THE SITE AND ANY INFORMATION, CONTENT OR SERVICES MADE AVAILABLE ON OR THROUGH THE SITE ARE PROVIDED "AS IS" AND "AS AVAILABLE" WITHOUT WARRANTY OF ANY KIND (EXPRESS, IMPLIED OR OTHERWISE), INCLUDING, WITHOUT LIMITATION, ANY IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NON-INFRINGEMENT, EXCEPT INSOFAR AS ANY SUCH IMPLIED WARRANTIES MAY NOT BE DISCLAIMED UNDER APPLICABLE LAW."""

        billing_address_text = """141 Portland St.
        9th Floor
        Cambridge,
        MA 02139"""

        style = getSampleStyleSheet()['Normal']
        style.fontSize = 8

        service_provider_para = Paragraph(service_provider_text.replace("\n", "<br/>"), style)
        disclaimer_para = Paragraph(disclaimer_text.replace("\n", "<br/>"), style)
        billing_address_para = Paragraph(billing_address_text.replace("\n", "<br/>"), style)

        data= [
            [service_provider_para],
            ['Disclaimer'],
            [disclaimer_para],
            ['Billing Address'],
            [billing_address_para]
        ]

        footer_style = [
            ('ALIGN',(0,0),(-1,-1),'LEFT'),
            ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
            ('TEXTCOLOR',(0,0),(-1,-1),colors.black),
            ('BACKGROUND', (0,0), (0,0), colors.lightgrey),
            ('LEFTPADDING', (0,0), (0,0), 5*mm),
            ('GRID', (0,0), (0,0), 0.50, colors.black),
            ('BACKGROUND', (0,2), (0,2), colors.lightgrey),
            ('LEFTPADDING', (0,2), (0,2), 5*mm),
            ('GRID', (0,2), (0,2), 0.50, colors.black),
            ('BACKGROUND', (0,4), (0,4), colors.lightgrey),
            ('LEFTPADDING', (0,4), (0,4), 5*mm),
            ('GRID', (0,4), (0,4), 0.50, colors.black),

        ]

        if (self.is_invoice):
            terms_conditions_text = """Enrollments:
            Enrollments must be completed within 7 full days from the course start date.
            Payment Terms:
            Payment is due immediately. Preferred method of payment is wire transfer. Full instructions and remittance details will be included on your official invoice. Please note that our terms are net zero. For questions regarding payment instructions or extensions, please contact onlinex-registration@mit.edu and include the words "payment question" in your subject line.
            Cancellations:
            Cancellation requests must be submitted to onlinex-registration@mit.edu 14 days prior to the course start date to be eligible for a refund. If you submit a cancellation request within 14 days prior to the course start date, you will not be eligible for a refund. Please see our Terms of Service page for full details.
            Substitutions:
            The MIT Professional Education Online X Programs office must receive substitution requests before the course start date in order for the request to be considered. Please email onlinex-registration@mit.edu to request a substitution.
            Please see our Terms of Service page for our detailed policies, including terms and conditions of use."""
            terms_conditions_para = Paragraph(terms_conditions_text.replace("\n", "<br/>"), style)
            data.append(['TERMS AND CONDITIONS'])
            data.append([terms_conditions_para])
            footer_style.append(('LEFTPADDING', (0,6), (0,6), 5*mm))

        t=Table(data, 176*mm)

        t.setStyle(TableStyle(footer_style))
        t.wrap(0,0)

        if (y_pos-(5+self.MARGIN+5)*mm)<=t._height:
            self.prepare_new_page()

        t.drawOn(self.pdf, (self.MARGIN + 5) * mm, (self.MARGIN + 5) * mm)



