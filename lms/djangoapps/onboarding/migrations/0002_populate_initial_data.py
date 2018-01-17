# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
import requests
from lxml import etree


def create_currency(apps, currency_obj):
    currency_model = apps.get_model("onboarding", "Currency")
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


def create_records(apps, ModelClass, records_map):
    all_codes = ModelClass.objects.all().values_list('code', flat=True)

    objs = []
    idx = 1
    for code, label in records_map.items():
        if not code in all_codes:
            objs.append(ModelClass(order=idx, code=code, label=label))
            idx += 1

    if objs:
        ModelClass.objects.bulk_create(objs)


class Migration(migrations.Migration):

    def insert_education_levels(apps, schema_editor):
         
        _levels = {
            "DPD": "Doctoral or professional degree",
            "MD": "Master's degree",
            "BD": "Bachelor's degree",
            "SUND": "Some university, no degree",
            "HSDOE": "High school diploma or equivalent secondary degree",
            "NFE": "No formal educational degree",
            "IWRNS": "I'd rather not say"
        }
        EducationLevel = apps.get_model('onboarding', 'EducationLevel')
        create_records(apps, EducationLevel, _levels)

    def insert_english_proficiency(apps, schema_editor):
        _levels = {
            "NP": "No proficiency",
            "BEG": "Beginning",
            "INT": "Intermediate",
            "ADV": "Advanced",
            "NS": "Native speaker",
            "IWRNS": "I'd rather not say"
        }
        EnglishProficiency = apps.get_model('onboarding', 'EnglishProficiency')
        create_records(apps, EnglishProficiency, _levels)

    def insert_role_inside_org(apps, schema_editor):
        _levels = {
            "VOL": "Volunteer",
            "INTERN": "Internship",
            "EL": "Entry level",
            "MAN": "Manager",
            "DIR": "Director",
            "EXC": "Executive Director/CEO",
            "IWRNS": "I'd rather not say"
        }
        RoleInsideOrg = apps.get_model('onboarding', 'RoleInsideOrg')
        create_records(apps, RoleInsideOrg, _levels)

    def insert_operation_levels(apps, schema_editor):
        _levels = {
            "INERNAIONA": "International",
            "RMC": "Regional including offices in multiple countries",
            "NATIONAL": "National",
            "RMLOC": "Regional including multiple offices within one country",
            "LOCAL": "Local",
            "IWRNS": "I'd rather not say",
        }
        OperationLevel = apps.get_model('onboarding', 'OperationLevel')
        create_records(apps, OperationLevel, _levels)

    def insert_org_sectors(apps, schema_editor):
        _levels = {
            "AI": "Academic Institution",
            "FPC": "For-Profit Company",
            "GOVTA": "Government Agency",
            "GFND": "Grantmaking Foundation",
            "NPORG": "Non-Profit Organization",
            "SLFEMP": "Self-Employed",
            "SENTR": "Social Enterprise",
            "IWRNS": "I'd rather not say",
        }
        OrgSector = apps.get_model('onboarding', 'OrgSector')
        create_records(apps, OrgSector, _levels)

    def insert_focus_areas(apps, schema_editor):
        _levels = {
            "ANM": "Animals",
            "ACH": "Arts, Culture, Humanities",
            "CD": "Community Development",
            "EDU": "Education",
            "ENV": "Environment",
            "HEALTH": "Health",
            "HCR": "Human and Civil Rights",
            "HSRV": "Human Services",
            "INERNAIONA": "International",
            "RELIGION": "Religion",
            "RPP": "Research and Public Policy",
            "OTHER": "Other",
            "IWRNS": "I'd rather not say",
        }
        FocusArea = apps.get_model('onboarding', 'FocusArea')
        create_records(apps, FocusArea, _levels)

    def insert_total_employees(apps, schema_editor):
        _levels = {
            "1-ONLY": "1 (only yourself)",
            "2-5": "2-5",
            "6-10": "6-10",
            "11-20": "11-20",
            "21-50": "21-50",
            "101-200": "101-200",
            "201-501": "201-501",
            "501-1,000": "501-1,000",
            "51-100": "51-100",
            "1,000+": "1,000+",
            "NA": "Not applicable",
        }
        TotalEmployee = apps.get_model('onboarding', 'TotalEmployee')
        create_records(apps, TotalEmployee, _levels)

    def insert_partner_networks(apps, schema_editor):
        _levels = {
            "ACUMEN": "+Acumen",
            "FHI": "FHI 360/ FHI Foundation",
            "GG": "Global Giving",
            "MC": "Mercy Corps",
            "WAFGAW": "With and For Girls Award Winner",
            "WAFGN": "With and For Girls Network"
        }
        PartnerNetwork = apps.get_model('onboarding', 'PartnerNetwork')
        create_records(apps, PartnerNetwork, _levels)

    def populate_currency_model(apps, schema_editor):
        currency_list = parse_xml_n_get_currencies()
        for currency in currency_list:
            create_currency(apps, currency)

    dependencies = [
        ('onboarding', '0003_historicaluser'),
    ]

    operations = [
        migrations.RunPython(insert_education_levels),
        migrations.RunPython(insert_english_proficiency),
        migrations.RunPython(insert_role_inside_org),

        migrations.RunPython(insert_operation_levels),
        migrations.RunPython(insert_org_sectors),
        migrations.RunPython(insert_focus_areas),

        migrations.RunPython(insert_total_employees),
        migrations.RunPython(insert_partner_networks),
        migrations.RunPython(populate_currency_model)
    ]
