# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import json
import os

# Converted from the original South migration 0020_certificatehtmlviewconfiguration_data.py

from django.db import migrations, models
from django.conf import settings


def forwards(apps, schema_editor):
    """
    Bootstraps the HTML view template with some default configuration parameters
    """
    _links = getattr(settings, "MKTG_URL_LINK_MAP", {})
    config = {
        "default": {
            "accomplishment_class_append": "accomplishment-certificate",
            "platform_name": getattr(settings, "PLATFORM_NAME", "Your Platform Name Here"),
             "company_about_url": '/%s' % _links.get("ABOUT", ''),
             "company_privacy_url": '/%s' % _links.get("PRIVACY", ''),
             "company_tos_url": '/%s' % _links.get("TOS", ''),
             "company_verified_certificate_url": "https://edx.org/verified-certificate",
             "logo_src": "images/logo.png",
             "logo_url": ""
        },
        "honor": {
            "certificate_type": "Honor Code",
            "certificate_title": "Certificate of Achievement",
        },
        "verified": {
            "certificate_type": "Verified",
            "certificate_title": "Verified Certificate of Achievement",
        }
    }
    certificate_html_view_configuration_model = apps.get_model("certificates", "CertificateHtmlViewConfiguration")
    db_alias = schema_editor.connection.alias

    objects = certificate_html_view_configuration_model.objects.using(db_alias)
    if not objects.exists():
        objects.create(
            configuration=json.dumps(config),
            enabled=False,
        )

def backwards(apps, schema_editor):
    """
    Rolling back to zero-state, so remove all currently-defined configurations
    """
    certificate_html_view_configuration_model = apps.get_model("certificates", "CertificateHtmlViewConfiguration")
    db_alias = schema_editor.connection.alias

    certificate_html_view_configuration_model.objects.using(db_alias).all().delete()

class Migration(migrations.Migration):

    dependencies = [
        ('certificates', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards)
    ]
