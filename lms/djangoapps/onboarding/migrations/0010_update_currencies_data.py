# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
import requests
from lxml import etree


def update_currency(currency_model, currency_obj):
    currency = currency_model(**currency_obj)
    currency.save()


def parse_xml_n_get_currencies():
    currency_list = []
    currency_xml_request = requests.get('https://www.currency-iso.org/dam/downloads/lists/list_one.xml')
    if currency_xml_request.status_code == 200:
        xml_content_root = etree.fromstring(currency_xml_request.content)
        currencies = xml_content_root.xpath("./CcyTbl/CcyNtry")
        for currency_xml in currencies:
            country = currency_xml.xpath('./CtryNm/text()')
            name = currency_xml.xpath('./CcyNm/text()')
            alphabetic_code = currency_xml.xpath('./Ccy/text()')
            number = currency_xml.xpath('./CcyNbr/text()')
            minor_units = currency_xml.xpath('./CcyMnrUnts/text()')
            currency = {
                "country": country[0].encode('utf8') if country else "",
                "name": name[0].encode('utf8') if name else "",
                "alphabetic_code": alphabetic_code[0].encode('utf8') if alphabetic_code else "",
                "number": number[0].encode('utf8') if number else "",
                "minor_units": minor_units[0].encode('utf8') if minor_units else ""
            }

            currency_list.append(currency)

    return currency_list


class Migration(migrations.Migration):

    def update_currency_records(apps, schema_editor):
        currency_model = apps.get_model("onboarding", "Currency")
        currency_model.objects.all().delete()
        currency_list = parse_xml_n_get_currencies()
        for currency in currency_list:
            update_currency(currency_model, currency)

    dependencies = [
        ('onboarding', '0009_auto_20180217_0527'),
    ]

    operations = [
        migrations.RunPython(update_currency_records)
    ]
