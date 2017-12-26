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
    for code, label in records_map.items():
        if not code in all_codes:
            objs.append(ModelClass(code=code, label=label))

    if objs:
        ModelClass.objects.bulk_create(objs)


class Migration(migrations.Migration):

    def insert_education_levels(apps, schema_editor):
         
        _levels = {
            "DPD": "Doctoral or professional degree",
            "MD": "Master's degree",
            "BD": "Bachelor's degree",
            "AD": "Associate's degree",
            "PNA": "Postsecondary nondegree award",
            "SCND": "Some college, no degree",
            "HSDOE": "High school diploma or equivalent",
            "NFE": "No formal educational credential"
        }
        EducationLevel = apps.get_model('onboarding', 'EducationLevel')
        create_records(apps, EducationLevel, _levels)

    def insert_english_proficiency(apps, schema_editor):
        _levels = {
            "NP": "No proficiency",
            "EP": "Elementary proficiency",
            "LWP": "Limited working proficiency",
            "PWP": "Professional working proficiency",
            "NOBP": "Native or bilingual proficiency"
        }
        EnglishProficiency = apps.get_model('onboarding', 'EnglishProficiency')
        create_records(apps, EnglishProficiency, _levels)

    def insert_role_inside_org(apps, schema_editor):
        _levels = {
            "VOL": "Volunteer",
            "EL": "Entry level",
            "ASSO": "Associate",
            "INTERN": "Internship",
            "MSL": "Mid-Senior level",
            "DIR": "Director",
            "EXC": "Executive",
        }
        RoleInsideOrg = apps.get_model('onboarding', 'RoleInsideOrg')
        create_records(apps, RoleInsideOrg, _levels)

    def insert_operation_levels(apps, schema_editor):
        _levels = {
            "INERNAIONA": "International",
            "RMC": "Regional including multiple countries",
            "NATIONAL": "National",
            "RMLOC": "Regional including multiple localities within one country",
            "LOCAL": "Local",
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
            "STU": "Student",
            "UNEMP": "Unemployed",
            "OTHER": "Other",
        }
        OrgSector = apps.get_model('onboarding', 'OrgSector')
        create_records(apps, OrgSector, _levels)

    def insert_focus_areas(apps, schema_editor):
        _levels = {
            "ACH": "Arts, Culture, Humanities",
            "CD": "Community Development",
            "EDU": "Education",
            "ENV": "Environment",
            "HEALTH": "Health",
            "HCR": "Human and Civil Rights",
            "HSRV": "Human Services",
            "RELIGION": "Religion",
            "RPP": "Research and Public Policy",
        }
        FocusArea = apps.get_model('onboarding', 'FocusArea')
        create_records(apps, FocusArea, _levels)

    def insert_total_employees(apps, schema_editor):
        _levels = {
            "1-10": "1-10",
            "11-15": "11-15",
            "51-100": "51-100",
            "101-500": "101-500",
            "1,000+": "1,000+",
            "NA": "Not applicable",
        }
        TotalEmployee = apps.get_model('onboarding', 'TotalEmployee')
        create_records(apps, TotalEmployee, _levels)

    def insert_partner_networks(apps, schema_editor):
        _levels = {
            "ACUMEN": "+Acumen",
            "EAHP": "East Africa Health Platform",
            "FHI": "FHI 360",
            "MC": "Mercy Corps",
            "WAFGAW": "With and For Girls Award Winner",
            "CAFSA": "Charities Aid Foundation South Africa",
            "EACSOF": "East African Civil Society Organizations Forum",
            "GG": "Global Giving",
            "SIAN": "Starts Impact Awards Network",
            "WAFGN": "With and For Girls Network"
        }
        PartnerNetwork = apps.get_model('onboarding', 'PartnerNetwork')
        create_records(apps, PartnerNetwork, _levels)

    def populate_currency_model(apps, schema_editor):
        currency_list = parse_xml_n_get_currencies()
        for currency in currency_list:
            create_currency(apps, currency)

    dependencies = [
        ('onboarding', '0001_initial'),
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
