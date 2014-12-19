# -*- coding: utf-8 -*-
from PIL import Image
# import qrcode
import datetime

from .conf import _

__all__ = ['Client', 'Provider', 'Creator', 'Item', 'Invoice']

class UnicodeProperty(object):
    _attrs = ()

    def __setattr__(self, key, value):
        if key in self._attrs:
            value = unicode(value)
        self.__dict__[key] = value

class Address(UnicodeProperty):
    _attrs = ('summary', 'address', 'city', 'zip', 'phone', 'email',
              'bank_name', 'bank_account', 'note', 'vat_id', 'ir',
              'logo_filename')

    def __init__(self, summary, address='', city='', zip='', phone='', email='',
               bank_name='', bank_account='', note='', vat_id='', ir='',
               logo_filename=''):
        self.summary = summary
        self.address = address
        self.city = city
        self.zip = zip
        self.phone = phone
        self.email = email
        self.bank_name = bank_name
        self.bank_account = bank_account
        self.note = note
        self.vat_id = vat_id
        self.ir = ir
        self.logo_filename = logo_filename


    def get_address_lines(self):
        address_line = [
            self.summary,
            self.address,
            u'%s %s' % (self.zip, self.city)
            ]
        if self.vat_id:
            address_line.append(_(u'Vat in: %s') % self.vat_id)

        if self.ir:
            address_line.append(_(u'IR: %s') % self.ir)

        return address_line

    def get_contact_lines(self):
        return [
            self.phone,
            self.email,
            ]

class Client(Address):
    pass

class Provider(Address):
    pass


class Creator(UnicodeProperty):
    _attrs = ('name', 'stamp_filename')

    def __init__(self, name, stamp_filename=''):
        self.name = name
        self.stamp_filename = stamp_filename

class Item(object):

    def __init__(self, count, price, description='', unit='', tax=0.0):
        self._count = float(count)
        self._price = float(price)
        self._description = unicode(description)
        self._unit = unicode(unit)
        self._tax = float(tax)

    @property
    def total(self):
        return self.price * self.count

    @property
    def total_tax(self):
        return self.price * self.count * (1.0 + self.tax / 100.0)

    def count_tax(self):
        return self.total_tax - self.total

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, value):
        self._description = unicode(value)

    @property
    def count(self):
        return self._count

    @count.setter
    def count(self, value):
        try:
            self._count = float(value)
        except TypeError:
            self._count = 0

    @property
    def price(self):
        return self._price

    @price.setter
    def price(self, value):
        try:
            self._price = float(value)
        except TypeError:
            self._price = 0.0

    @property
    def unit(self):
        return self._unit

    @unit.setter
    def unit(self, value):
        self._unit = unicode(value)

    @property
    def tax(self):
        return self._tax

    @tax.setter
    def tax(self, value):
        try:
            self._tax = float(value)
        except TypeError:
            self._tax = 0.0


class Invoice(UnicodeProperty):
    _attrs = ('title', 'variable_symbol', 'specific_symbol', 'paytype',
              'currency', 'currency_locale', 'number')

    rounding_result = False

    def __init__(self, client, provider, creator):
        assert isinstance(client, Client)
        assert isinstance(provider, Provider)
        assert isinstance(creator, Creator)

        self.client = client
        self.provider = provider
        self.creator = creator
        self._items = []
        self.date = None
        self.payback = None
        self.taxable_date = None

        for attr in self._attrs:
            self.__setattr__(attr, '')

    @property
    def price(self):
        return self._round_result(sum([item.total for item in self.items]))

    @property
    def price_tax(self):
        return self._round_result(sum([item.total_tax for item in self.items]))

    def add_item(self, item):
        assert isinstance(item, Item)
        self._items.append(item)

    @property
    def items(self):
        return self._items

    @property
    def use_tax(self):
        use_tax = False
        for item in self.items:
            if item.tax:
                use_tax = True
                continue
        return use_tax

    @property
    def difference_in_rounding(self):
        price = sum([item.total_tax for item in self.items])
        return round(price, 0) - price

    def _get_grouped_items_by_tax(self):
        table = {}
        for item in self.items:
            if not table.has_key(item.tax):
                table[item.tax] = {'total': item.total, 'total_tax': item.total_tax, 'tax': item.count_tax()}
            else:
                table[item.tax]['total'] += item.total
                table[item.tax]['total_tax'] +=  item.total_tax
                table[item.tax]['tax'] +=  item.count_tax()

        return table

    def _round_result(self, price):
        if self.rounding_result:
            price = round(price, 0)
        return price

    def generate_breakdown_vat(self):
        return self._get_grouped_items_by_tax()

    def generate_breakdown_vat_table(self):
        rows = []
        for vat,items in self.generate_breakdown_vat().iteritems():
             rows.append((vat, items['total'], items['total_tax'], items['tax']))

        return rows

class Correction(Invoice):
    _attrs = ('number', 'reason', 'title', 'variable_symbol', 'specific_symbol', 'paytype',
              'currency', 'currency_locale', 'date', 'payback', 'taxable_date')

    def __init__(self, client, provider, creator):
        super(Correction, self).__init__(client, provider, creator)
