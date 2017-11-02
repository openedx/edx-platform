# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

import requests
from lxml import etree


def create_currency(apps, currency_obj):
    currency_model = apps.get_model("onboarding_survey", "Currency")
    currency = currency_model(**currency_obj)
    currency.save()


def parse_xml_n_get_currencies():
    currency_list = []
    currency_xml_request = requests.get('https://www.currency-iso.org/dam/downloads/lists/list_one.xml')
    if currency_xml_request.status_code == 200:
        xml_content_root = etree.fromstring(currency_xml_request.content)
        countries = xml_content_root.xpath("./CcyTbl/CcyNtry")
        for country in countries:
            currency_name = country.xpath('./CcyNm/text()')
            currency_code = country.xpath('./Ccy/text()')
            if currency_code and currency_name:
                currency_name_encoded = currency_name[0].encode('utf8')
                currency_code_encoded = currency_code[0].encode('utf8')
                currency = {"name": currency_name_encoded, "alphabetic_code": currency_code_encoded}
                currency_list.append(currency)

    return currency_list


class Migration(migrations.Migration):
    def populate_currency_model(apps, schema_editor):
        currency_list = parse_xml_n_get_currencies()
        for currency in currency_list:
            create_currency(apps, currency)

    dependencies = [
        ('onboarding_survey', '0032_auto_20171101_0803'),
    ]

    operations = [
        migrations.RunPython(populate_currency_model),
    ]
