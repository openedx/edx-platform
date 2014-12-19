#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, datetime
from reportlab.pdfgen.canvas import Canvas

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm, mm, inch, pica
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from tempfile import NamedTemporaryFile

from api import Invoice as ApiInvoice
from pdf import BaseInvoice

class Address:
    firstname = ""
    lastname = ""
    address = ""
    city = ""
    zip = ""
    phone = ""
    email = ""
    bank_name = ""
    bank_account = ""
    note = ""

    def getAddressLines(self):
        return [
            "%s %s" % (self.firstname, self.lastname),
            self.address,
            "%s %s" % (self.zip, self.city),
        ]

    def getContactLines(self):
        return [
            self.phone,
            self.email,
        ]

class Item:
    name = ""
    count = 0
    price = 0.0

    def total(self):
        return self.count*self.price

class Invoice:
    client = Address()
    provider = Address()
    items = []
    title = "Faktura"
    vs = "00000000"
    creator = ""
    sign_image = None
    payment_days = 14
    paytype = "Převodem"

    pdffile = None

    def __init__(self):
        self.TOP = 260
        self.LEFT = 20

        pdfmetrics.registerFont(TTFont('DejaVu', '/usr/share/fonts/truetype/ttf-dejavu/DejaVuSans.ttf'))

        self.pdffile = NamedTemporaryFile(delete=False)

        self.pdf = Canvas(self.pdffile.name, pagesize = letter)
        self.pdf.setFont("DejaVu", 15)
        self.pdf.setStrokeColorRGB(0, 0, 0)

    def __del__(self):
        if os.path.isfile(self.pdffile.name):
            os.unlink(self.pdffile.name)

    #############################################################
    ## Setters
    #############################################################

    def setClient(self, address):
        self.client = address

    def setProvider(self, address):
        self.provider = address

    def setTitle(self, value):
        self.title = value

    def setVS(self, value):
        self.vs = value

    def setCreator(self, value):
        self.creator = value

    def setPaytype(self, value):
        self.paytype = value

    def setPaymentDays(self, value):
        self.payment_days = int(value)

    def addItem(self, item):
        self.items.append(item)

    #############################################################
    ## Getters
    #############################################################

    def getContent(self):
        # Texty
        self.drawMain()
        self.drawProvider(self.TOP-10,self.LEFT+3)
        self.drawClient(self.TOP-30,self.LEFT+91)
        self.drawPayment(self.TOP-47,self.LEFT+3)
        self.drawItems(self.TOP-80,self.LEFT)
        self.drawDates(self.TOP-10,self.LEFT+91)

        #self.pdf.setFillColorRGB(0, 0, 0)

        self.pdf.showPage()
        self.pdf.save()

        f = open(self.pdffile.name)
        data = f.read()
        f.close()

        os.unlink(self.pdffile.name)

        return data

    #############################################################
    ## Draw methods
    #############################################################

    def drawMain(self):
        # Horní lajna
        self.pdf.drawString(self.LEFT*mm, self.TOP*mm, self.title)
        self.pdf.drawString((self.LEFT+100)*mm, self.TOP*mm, "Variabilní symbol: %s" % self.vs)

        # Rámečky
        self.pdf.rect((self.LEFT)*mm, (self.TOP-68)*mm, (self.LEFT+156)*mm, 65*mm, stroke=True, fill=False)

        path = self.pdf.beginPath()
        path.moveTo((self.LEFT+88)*mm, (self.TOP-3)*mm)
        path.lineTo((self.LEFT+88)*mm, (self.TOP-68)*mm)
        self.pdf.drawPath(path, True, True)

        path = self.pdf.beginPath()
        path.moveTo((self.LEFT)*mm, (self.TOP-39)*mm)
        path.lineTo((self.LEFT+88)*mm, (self.TOP-39)*mm)
        self.pdf.drawPath(path, True, True)

        path = self.pdf.beginPath()
        path.moveTo((self.LEFT+88)*mm, (self.TOP-23)*mm)
        path.lineTo((self.LEFT+176)*mm, (self.TOP-23)*mm)
        self.pdf.drawPath(path, True, True)

    def drawClient(self,TOP,LEFT):
        self.pdf.setFont("DejaVu", 12)
        self.pdf.drawString((LEFT)*mm, (TOP)*mm, "Odběratel")
        self.pdf.setFont("DejaVu", 8)
        text = self.pdf.beginText((LEFT+2)*mm, (TOP-6)*mm)
        text.textLines("\n".join(self.client.getAddressLines()))
        self.pdf.drawText(text)
        text = self.pdf.beginText((LEFT+2)*mm, (TOP-28)*mm)
        text.textLines("\n".join(self.client.getContactLines()))
        self.pdf.drawText(text)

    def drawProvider(self,TOP,LEFT):
        self.pdf.setFont("DejaVu", 12)
        self.pdf.drawString((LEFT)*mm, (TOP)*mm, "Dodavatel")
        self.pdf.setFont("DejaVu", 8)
        text = self.pdf.beginText((LEFT+2)*mm, (TOP-6)*mm)
        text.textLines("\n".join(self.provider.getAddressLines()))
        self.pdf.drawText(text)
        text = self.pdf.beginText((LEFT+40)*mm, (TOP-6)*mm)
        text.textLines("\n".join(self.provider.getContactLines()))
        self.pdf.drawText(text)
        if self.provider.note:
            self.pdf.drawString((LEFT+2)*mm, (TOP-26)*mm, self.provider.note)

    def drawPayment(self,TOP,LEFT):
        self.pdf.setFont("DejaVu", 11)
        self.pdf.drawString((LEFT)*mm, (TOP)*mm, "Údaje pro platbu")
        #self.pdf.setFillColorRGB(255, 0, 0)
        text = self.pdf.beginText((LEFT+2)*mm, (TOP-6)*mm)
        text.textLines("""%s
Číslo účtu: %s
Variabilní symbol: %s"""%(self.provider.bank_name ,self.provider.bank_account, self.vs))
        self.pdf.drawText(text)

    def drawItems(self,TOP,LEFT):
        # Items
        path = self.pdf.beginPath()
        path.moveTo((LEFT)*mm, (TOP-4)*mm)
        path.lineTo((LEFT+176)*mm, (TOP-4)*mm)
        self.pdf.drawPath(path, True, True)

        self.pdf.setFont("DejaVu", 9)
        self.pdf.drawString((LEFT+1)*mm, (TOP-2)*mm, "Fakturuji vám:")

        i=9
        self.pdf.drawString((LEFT+100)*mm, (TOP-i)*mm, "Množství")
        self.pdf.drawString((LEFT+122)*mm, (TOP-i)*mm, "Cena za jedn.")
        self.pdf.drawString((LEFT+150)*mm, (TOP-i)*mm, "Cena celkem")
        i+=5

        # List
        total=0.0
        for x in self.items:
            self.pdf.drawString((LEFT+1)*mm, (TOP-i)*mm, x.name)
            i+=5
            self.pdf.drawString((LEFT+100)*mm, (TOP-i)*mm, "%d ks" % x.count)
            self.pdf.drawString((LEFT+122)*mm, (TOP-i)*mm, "%.2f,- kč" % x.price)
            self.pdf.drawString((LEFT+150)*mm, (TOP-i)*mm, "%.2f,- kč" % (x.total()))
            i+=5
            total += x.total()

        path = self.pdf.beginPath()
        path.moveTo((LEFT)*mm, (TOP-i)*mm)
        path.lineTo((LEFT+176)*mm, (TOP-i)*mm)
        self.pdf.drawPath(path, True, True)

        self.pdf.setFont("DejaVu", 12)
        self.pdf.drawString((LEFT+130)*mm, (TOP-i-10)*mm, "Celkem: %d ,- kč" % total)

        self.pdf.rect((LEFT)*mm, (TOP-i-17)*mm, (LEFT+156)*mm, (i+19)*mm, stroke=True, fill=False) #140,142

        if self.sign_image:
            self.pdf.drawImage(self.sign_image, (LEFT+98)*mm, (TOP-i-72)*mm)

        path = self.pdf.beginPath()
        path.moveTo((LEFT+110)*mm, (TOP-i-70)*mm)
        path.lineTo((LEFT+164)*mm, (TOP-i-70)*mm)
        self.pdf.drawPath(path, True, True)

        self.pdf.drawString((LEFT+112)*mm, (TOP-i-75)*mm, "Vystavil: %s" % self.creator)


    def drawDates(self,TOP,LEFT):
        today = datetime.datetime.today()
        payback = today+datetime.timedelta(self.payment_days)

        self.pdf.setFont("DejaVu", 10)
        self.pdf.drawString((LEFT)*mm, (TOP+1)*mm, "Datum vystavení: %s" % today.strftime("%d.%m.%Y"))
        self.pdf.drawString((LEFT)*mm, (TOP-4)*mm, "Datum splatnosti: %s" % payback.strftime("%d.%m.%Y"))
        self.pdf.drawString((LEFT)*mm, (TOP-9)*mm, "Forma úhrady: " + self.paytype)

class Generator(object):

    def __init__(self, invoice):
        assert isinstance(invoice, ApiInvoice)
        self.invoice = invoice

    def gen(self, filename, pdf_invoice):
        assert issubclass(pdf_invoice, BaseInvoice)

        pdf = pdf_invoice(self.invoice)
        pdf.gen(filename)

if __name__ == "__main__":
    client = Address()
    client.firstname = "Adam"
    client.lastname = "Štrauch"
    client.address = "Houští 474"
    client.city = "Lanškroun"
    client.zip = "563 01"
    client.phone = "+420777636388"
    client.email = "cx@initd.cz"
    client.bank_name = "GE Money Bank"
    client.bank_account = "181553009/0600"
    client.note = "Blablabla"

    provider = Address()
    provider.firstname = "Adam"
    provider.lastname = "Štrauch"
    provider.address = "Houští 474"
    provider.city = "Lanškroun"
    provider.zip = "563 01"
    provider.phone = "+420777636388"
    provider.email = "cx@initd.cz"
    provider.bank_name = "GE Money Bank"
    provider.bank_account = "181553009/0600"
    provider.note = "Blablabla"

    item1 = Item()
    item1.name = "Položka 1"
    item1.count = 5
    item1.price = 100
    item2 = Item()
    item2.name = "Položka 2"
    item2.count = 10
    item2.price = 750

    invoice = Invoice()
    invoice.setClient(client)
    invoice.setProvider(provider)
    invoice.setTitle("Faktura")
    invoice.setVS("00001")
    invoice.setCreator("Adam Štrauch")
    invoice.addItem(item1)
    invoice.addItem(item2)

    f = open("test.pdf", "w")
    f.write(invoice.getContent())
    f.close()
