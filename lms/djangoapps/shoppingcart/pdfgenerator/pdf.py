# -*- coding: utf-8 -*-
from PIL import Image

from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus.tables import Table, TableStyle

from .conf import _, FONT_PATH, FONT_BOLD_PATH
from api import Invoice
import locale
import warnings

class BaseInvoice(object):

    def __init__(self, invoice):
        assert isinstance(invoice, Invoice)

        self.invoice = invoice

    def gen(self, filename):
        pass


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


def prepare_invoice_draw(self):
    self.TOP = 260
    self.LEFT = 20

    pdfmetrics.registerFont(TTFont('DejaVu', FONT_PATH))
    pdfmetrics.registerFont(TTFont('DejaVu-Bold', FONT_BOLD_PATH))

    self.pdf = NumberedCanvas(self.filename, pagesize = letter)
    self.addMetaInformation(self.pdf)

    self.pdf.setFont('DejaVu', 15)
    self.pdf.setStrokeColorRGB(0, 0, 0)

    if self.invoice.currency:
        warnings.warn("currency attribute is deprecated, use locale instead", DeprecationWarning)
    locale.setlocale(locale.LC_ALL, str(self.invoice.currency_locale))


#Fix for http://bugs.python.org/issue15276.
def fix_grouping(bytestring):
    try:
        return unicode(bytestring)
    except UnicodeDecodeError:
        return bytestring.decode("utf-8")


def currency(amount):
    return fix_grouping(locale.currency(amount, grouping=True)).replace(u",00 Kč", u",- Kč   ")


class SimpleInvoice(BaseInvoice):

    def gen(self, filename, generate_qr_code=False):
        self.filename = filename

        qr_builder = None

        self.qr_builder = qr_builder

        prepare_invoice_draw(self)


        # Texty
        self.drawMain()
        self.drawTitle()
        self.drawProvider(self.TOP - 10,self.LEFT + 3)
        self.drawClient(self.TOP - 35,self.LEFT + 91)
        self.drawPayment(self.TOP - 47,self.LEFT + 3)
        self.drawDates(self.TOP - 10,self.LEFT + 91)
        self.drawItems(self.TOP - 80,self.LEFT)

        self.pdf.setFillColorRGB(0, 0, 0)

        self.pdf.showPage()
        self.pdf.save()
        if self.qr_builder:
            self.qr_builder.destroy()

    #############################################################
    ## Draw methods
    #############################################################

    def addMetaInformation(self, pdf):
        pdf.setCreator(self.invoice.provider.summary)
        pdf.setTitle(self.invoice.title)
        pdf.setAuthor(self.invoice.creator.name)

    def drawTitle(self):
        # Up line
        self.pdf.drawString(self.LEFT*mm, self.TOP*mm, self.invoice.title)
        self.pdf.drawString((self.LEFT + 90) * mm,
            self.TOP*mm,
            _(u'Invoice num.: %s') %
            self.invoice.number)

    def drawMain(self):
        # Borders
        self.pdf.rect(self.LEFT * mm, (self.TOP - 68) * mm,
                      (self.LEFT + 156) * mm, 65 * mm, stroke=True, fill=False)

        path = self.pdf.beginPath()
        path.moveTo((self.LEFT + 88) * mm, (self.TOP - 3) * mm)
        path.lineTo((self.LEFT + 88) * mm, (self.TOP - 68) * mm)
        self.pdf.drawPath(path, True, True)

        path = self.pdf.beginPath()
        path.moveTo(self.LEFT * mm, (self.TOP - 39) * mm)
        path.lineTo((self.LEFT + 88) * mm, (self.TOP - 39) * mm)
        self.pdf.drawPath(path, True, True)

        path = self.pdf.beginPath()
        path.moveTo((self.LEFT + 88) * mm, (self.TOP - 27) * mm)
        path.lineTo((self.LEFT + 176) * mm, (self.TOP - 27) * mm)
        self.pdf.drawPath(path, True, True)

    def drawClient(self,TOP,LEFT):
        self.pdf.setFont('DejaVu', 12)
        self.pdf.drawString(LEFT * mm, TOP * mm, _(u'Customer'))
        self.pdf.setFont('DejaVu', 8)

        text = self.pdf.beginText((LEFT + 2) * mm, (TOP - 6) * mm)
        text.textLines(self.invoice.client.get_address_lines())
        self.pdf.drawText(text)

        text = self.pdf.beginText((LEFT + 2) * mm, (TOP - 23) * mm)
        text.textLines(self.invoice.client.get_contact_lines())
        self.pdf.drawText(text)

        if self.invoice.client.note:
            self.pdf.setFont('DejaVu', 6)
            text = self.pdf.beginText((LEFT + 2) * mm, (TOP - 29) * mm)
            text.textLines(self.invoice.client.note.splitlines())
            self.pdf.drawText(text)


    def drawProvider(self,TOP,LEFT):
        self.pdf.setFont('DejaVu', 12)
        self.pdf.drawString(LEFT * mm, TOP * mm, _(u'Provider'))
        self.pdf.setFont('DejaVu', 8)

        text = self.pdf.beginText((LEFT + 2) * mm, (TOP - 6) * mm)
        text.textLines(self.invoice.provider.get_address_lines())
        self.pdf.drawText(text)

        text = self.pdf.beginText((LEFT + 40) * mm, (TOP - 6) * mm)
        text.textLines(self.invoice.provider.get_contact_lines())

        self.pdf.drawText(text)
        if self.invoice.provider.note:
            self.pdf.setFont('DejaVu', 6)
            text = self.pdf.beginText((LEFT + 2) * mm, (TOP - 23) * mm)
            text.textLines(self.invoice.provider.note.splitlines())
            self.pdf.drawText(text)

        if self.invoice.provider.logo_filename:
            im = Image.open(self.invoice.provider.logo_filename)
            height = 30.0
            width = float(im.size[0]) / (float(im.size[1])/height)
            self.pdf.drawImage(self.invoice.provider.logo_filename, (LEFT + 84) * mm - width, (TOP - 4) * mm, width, height)

    def drawPayment(self,TOP,LEFT):
        self.pdf.setFont('DejaVu-Bold', 9)
        self.pdf.drawString(LEFT * mm, TOP * mm, _(u'Payment information'))

        text = self.pdf.beginText((LEFT + 2) * mm, (TOP - 6) * mm)
        lines = [
            self.invoice.provider.bank_name,
            '%s: %s' % (_(u'Account n.'), self.invoice.provider.bank_account),
        ]
        if self.invoice.variable_symbol:
            lines.append(
                '%s: %s' % (_(u'Variable symbol'), self.invoice.variable_symbol))
        if self.invoice.specific_symbol:
            lines.append(
                '%s: %s' % (_(u'Specific symbol'), self.invoice.specific_symbol))
        text.textLines(lines)
        self.pdf.drawText(text)


    def drawItemsHeader(self, TOP, LEFT):
        path = self.pdf.beginPath()
        path.moveTo(LEFT * mm, (TOP - 4) * mm)
        path.lineTo((LEFT + 176) * mm, (TOP - 4) * mm)
        self.pdf.drawPath(path, True, True)

        self.pdf.setFont('DejaVu-Bold', 7)
        self.pdf.drawString((LEFT + 1) * mm, (TOP - 2) * mm, _(u'List of items'))

        self.pdf.drawString((LEFT + 1) * mm, (TOP - 9) * mm, _(u'Description'))
        items_are_with_tax = self.invoice.use_tax
        if items_are_with_tax:
            i=9
            self.pdf.drawString((LEFT + 73) * mm, (TOP - i) * mm, _(u'Units'))
            self.pdf.drawString((LEFT + 88) * mm, (TOP - i) * mm,
                                _(u'Price per one'))
            self.pdf.drawString((LEFT + 115) * mm, (TOP - i) * mm,
                                _(u'Total price'))
            self.pdf.drawString((LEFT + 137) * mm, (TOP - i) * mm,
                                _(u'Tax'))
            self.pdf.drawString((LEFT + 146) * mm, (TOP - i) * mm,
                                _(u'Total price with tax'))
            i+=5
        else:
            i=9
            self.pdf.drawString((LEFT + 104) * mm, (TOP - i) * mm,
                                _(u'Units'))
            self.pdf.drawString((LEFT + 123) * mm, (TOP - i) * mm,
                                _(u'Price per one'))
            self.pdf.drawString((LEFT + 150) * mm, (TOP - i) * mm,
                                _(u'Total price'))
            i+=5
        return i


    def drawItems(self,TOP,LEFT):
        # Items
        i = self.drawItemsHeader(TOP, LEFT)
        self.pdf.setFont('DejaVu', 7)

        items_are_with_tax = self.invoice.use_tax

        # List
        will_wrap = False
        for item in self.invoice.items:
            if TOP - i < 30 * mm:
                will_wrap = True

            style = ParagraphStyle('normal', fontName='DejaVu', fontSize=7)
            p = Paragraph(item.description, style)
            pwidth, pheight = p.wrapOn(self.pdf, 70*mm if items_are_with_tax else 90*mm, 30*mm)
            i_add = max(float(pheight)/mm, 4.23)

            if will_wrap and TOP - i - i_add < 8 * mm:
                will_wrap = False
                self.pdf.rect(LEFT * mm, (TOP - i) * mm, (LEFT + 156) * mm, (i + 2) * mm, stroke=True, fill=False) #140,142
                self.pdf.showPage()

                i = self.drawItemsHeader(self.TOP, LEFT)
                TOP = self.TOP
                self.pdf.setFont('DejaVu', 7)

            #leading line
            path = self.pdf.beginPath()
            path.moveTo(LEFT * mm, (TOP - i + 3.5) * mm)
            path.lineTo((LEFT + 176) * mm, (TOP - i + 3.5) * mm)
            self.pdf.setLineWidth(0.1)
            self.pdf.drawPath(path, True, True)
            self.pdf.setLineWidth(1)

            i += i_add
            p.drawOn(self.pdf, (LEFT + 1) * mm, (TOP - i + 3) * mm)
            i -= 4.23
            if items_are_with_tax:
                if float(int(item.count)) == item.count:
                    self.pdf.drawRightString((LEFT + 85) * mm, (TOP - i) * mm, u'%s %s' % (fix_grouping(locale.format("%i", item.count, grouping=True)), item.unit))
                else:
                    self.pdf.drawRightString((LEFT + 85) * mm, (TOP - i) * mm, u'%s %s' % (fix_grouping(locale.format("%.2f", item.count, grouping=True)), item.unit))
                self.pdf.drawRightString((LEFT + 110) * mm, (TOP - i) * mm, currency(item.price))
                self.pdf.drawRightString((LEFT + 134) * mm, (TOP - i) * mm, currency(item.total))
                self.pdf.drawRightString((LEFT + 144) * mm, (TOP - i) * mm, '%.0f %%' % item.tax)
                self.pdf.drawRightString((LEFT + 173) * mm, (TOP - i) * mm, currency(item.total_tax))
                i+=5
            else:
                if float(int(item.count)) == item.count:
                    self.pdf.drawRightString((LEFT + 118) * mm, (TOP - i) * mm, u'%s %s' % (fix_grouping(locale.format("%i", item.count, grouping=True)), item.unit))
                else:
                    self.pdf.drawRightString((LEFT + 118) * mm, (TOP - i) * mm, u'%s %s' % (fix_grouping(locale.format("%.2f", item.count, grouping=True)), item.unit))
                self.pdf.drawRightString((LEFT + 148) * mm, (TOP - i) * mm, currency(item.price))
                self.pdf.drawRightString((LEFT + 173) * mm, (TOP - i) * mm, currency(item.total))
                i+=5

        if will_wrap:
            self.pdf.rect(LEFT * mm, (TOP - i) * mm, (LEFT + 156) * mm, (i + 2) * mm, stroke=True, fill=False) #140,142
            self.pdf.showPage()

            i=0
            TOP = self.TOP
            self.pdf.setFont('DejaVu', 7)

        if self.invoice.rounding_result:
            path = self.pdf.beginPath()
            path.moveTo(LEFT * mm, (TOP - i) * mm)
            path.lineTo((LEFT + 176) * mm, (TOP - i) * mm)
            i += 5
            self.pdf.drawPath(path, True, True)
            self.pdf.drawString((LEFT + 1) * mm, (TOP - i) * mm, _(u'Rounding'))
            self.pdf.drawString((LEFT + 68) * mm, (TOP - i) * mm, currency(self.invoice.difference_in_rounding))
            i += 3

        path = self.pdf.beginPath()
        path.moveTo(LEFT * mm, (TOP - i) * mm)
        path.lineTo((LEFT + 176) * mm, (TOP - i) * mm)
        self.pdf.drawPath(path, True, True)

        if not items_are_with_tax:
            self.pdf.setFont('DejaVu-Bold', 11)
            self.pdf.drawString((LEFT + 100) * mm, (TOP - i - 7) * mm, '%s: %s' % (_(u'Total'), currency(self.invoice.price)))
        else:
            self.pdf.setFont('DejaVu-Bold', 6)
            self.pdf.drawString((LEFT + 1) * mm, (TOP - i - 2) * mm, _(u'Breakdown VAT'))
            vat_list, tax_list, total_list, total_tax_list = [_(u'VAT rate')], [_(u'Tax')], [_(u'Without VAT')], [_(u'With VAT')]
            for vat, items in self.invoice.generate_breakdown_vat().iteritems():
                vat_list.append("%s%%" % locale.format('%.2f', vat))
                tax_list.append(currency(items['tax']))
                total_list.append(currency(items['total']))
                total_tax_list.append(currency(items['total_tax']))


            self.pdf.setFont('DejaVu', 6)
            text = self.pdf.beginText((LEFT + 1) * mm, (TOP - i - 5) * mm)
            text.textLines(vat_list)
            self.pdf.drawText(text)

            text = self.pdf.beginText((LEFT + 11) * mm, (TOP - i - 5) * mm)
            text.textLines(tax_list)
            self.pdf.drawText(text)

            text = self.pdf.beginText((LEFT + 27) * mm, (TOP - i - 5) * mm)
            text.textLines(total_list)
            self.pdf.drawText(text)

            text = self.pdf.beginText((LEFT + 45) * mm, (TOP - i - 5) * mm)
            text.textLines(total_tax_list)
            self.pdf.drawText(text)



            self.pdf.setFont('DejaVu-Bold', 11)
            self.pdf.drawString((LEFT + 100) * mm, (TOP - i - 14) * mm, u'%s: %s' % (_(u'Total with tax'), currency(self.invoice.price_tax)))

        if items_are_with_tax:
            self.pdf.rect(LEFT * mm, (TOP - i - 17) * mm, (LEFT + 156) * mm, (i + 19) * mm, stroke=True, fill=False) #140,142
        else:
            self.pdf.rect(LEFT * mm, (TOP - i - 11) * mm, (LEFT + 156) * mm, (i + 13) * mm, stroke=True, fill=False) #140,142

        self.drawCreator(TOP - i - 20, self.LEFT + 98)


    def drawCreator(self, TOP, LEFT):
        height = 20*mm
        if self.invoice.creator.stamp_filename:
            im = Image.open(self.invoice.creator.stamp_filename)
            height = float(im.size[1]) / (float(im.size[0])/200.0)
            self.pdf.drawImage(self.invoice.creator.stamp_filename, (LEFT) * mm, (TOP - 2) * mm - height, 200, height)

        path = self.pdf.beginPath()
        path.moveTo((LEFT + 8) * mm, (TOP) * mm - height)
        path.lineTo((LEFT + 62) * mm, (TOP) * mm - height)
        self.pdf.drawPath(path, True, True)

        self.pdf.drawString((LEFT + 10) * mm, (TOP - 5) * mm - height, '%s: %s' % (_(u'Creator'), self.invoice.creator.name))


    def drawQR(self, TOP, LEFT, size=130.0):
        if self.qr_builder:
            qr_filename = self.qr_builder.filename
            im = Image.open(qr_filename)
            height = float(im.size[1]) / (float(im.size[0]) / size)
            self.pdf.drawImage(qr_filename, LEFT * mm, TOP * mm - height,
                               size, height)


    def drawDates(self,TOP,LEFT):
        self.pdf.setFont('DejaVu', 10)
        top = TOP + 1
        items = []
        if self.invoice.date:
            items.append((LEFT * mm, '%s: %s' % (_(u'Date of exposure taxable invoice'), self.invoice.date)))
        if self.invoice.payback:
            items.append((LEFT * mm, '%s: %s' % (_(u'Payback'), self.invoice.payback)))
        if self.invoice.taxable_date:
            items.append((LEFT * mm, '%s: %s' % (_(u'Taxable date'),
                        self.invoice.taxable_date)))

        if self.invoice.paytype:
            items.append((LEFT * mm, '%s: %s' % (_(u'Paytype'),
                                                           self.invoice.paytype)))

        for item in items:
            self.pdf.drawString(item[0], top * mm, item[1])
            top += -5


class CorrectingInvoice(SimpleInvoice):
    def gen(self, filename):
        self.filename = filename
        prepare_invoice_draw(self)

        # Texty
        self.drawMain()
        self.drawTitle()
        self.drawProvider(self.TOP - 10,self.LEFT + 3)
        self.drawClient(self.TOP - 35,self.LEFT + 91)
        self.drawPayment(self.TOP - 47,self.LEFT + 3)
        self.drawCorretion(self.TOP - 73,self.LEFT)
        self.drawDates(self.TOP - 10,self.LEFT + 91)
        self.drawItems(self.TOP - 82,self.LEFT)

        #self.pdf.setFillColorRGB(0, 0, 0)

        self.pdf.showPage()
        self.pdf.save()

    def drawTitle(self):
        # Up line
        self.pdf.drawString(self.LEFT*mm, self.TOP*mm, self.invoice.title)
        self.pdf.drawString((self.LEFT + 90) * mm,
            self.TOP*mm,
            _(u'Correcting document: %s') %
            self.invoice.number)


    def drawCorretion(self,TOP,LEFT):
        self.pdf.setFont('DejaVu', 8)
        self.pdf.drawString(LEFT * mm, TOP * mm, _(u'Correction document for invoice: %s') % self.invoice.number)
        self.pdf.drawString(LEFT * mm, (TOP - 4) * mm, _(u'Reason to correction: %s') % self.invoice.reason)


class ProformaInvoice(SimpleInvoice):

    def drawCreator(self, TOP, LEFT):
        return

    def drawDates(self, TOP, LEFT):
        self.pdf.setFont('DejaVu', 10)
        top = TOP + 1
        items = []
        if self.invoice.date:
            items.append((LEFT * mm, '%s: %s' % (_(u'Date of exposure'), self.invoice.date)))
        if self.invoice.payback:
            items.append((LEFT * mm, '%s: %s' % (_(u'Payback'), self.invoice.payback)))

        if self.invoice.paytype:
            items.append((LEFT * mm, '%s: %s' % (_(u'Paytype'),
                                                 self.invoice.paytype)))

        for item in items:
            self.pdf.drawString(item[0], top * mm, item[1])
            top += -5