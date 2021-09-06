# -*- coding: utf-8 -*-



import json

from django.db import migrations, models

# Converted from the original South migration 0020_certificatehtmlviewconfiguration_data.py



def forwards(apps, schema_editor):
    """
    Bootstraps the HTML view template with some default configuration parameters
    """
    config = {
        "default": {
            "accomplishment_class_append": "accomplishment-certificate",
            "platform_name": "Your Platform Name Here",
            "company_about_url": "http://www.example.com/about-us",
            "company_privacy_url": "http://www.example.com/privacy-policy",
            "company_tos_url": "http://www.example.com/terms-service",
            "company_verified_certificate_url": "http://www.example.com/verified-certificate",
            "logo_src": "/static/certificates/images/logo.png",
            "logo_url": "http://www.example.com"
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

    objects = certificate_html_view_configuration_model.objects
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

    certificate_html_view_configuration_model.objects.all().delete()

class Migration(migrations.Migration):

    dependencies = [
        ('certificates', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards)
    ]
