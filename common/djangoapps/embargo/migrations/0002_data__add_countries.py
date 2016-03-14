# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# Converted from the original South migration 0003_add_countries.py

from django.db import migrations, models
from django_countries import countries


def create_embargo_countries(apps, schema_editor):
    """Populate the available countries with all 2-character ISO country codes. """
    country_model = apps.get_model("embargo", "Country")
    db_alias = schema_editor.connection.alias
    for country_code, __ in list(countries):
        country_model.objects.using(db_alias).get_or_create(country=country_code)

def remove_embargo_countries(apps, schema_editor):
    """Clear all available countries. """
    country_model = apps.get_model("embargo", "Country")
    db_alias = schema_editor.connection.alias
    country_model.objects.using(db_alias).all().delete()

class Migration(migrations.Migration):

    dependencies = [
        ('embargo', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_embargo_countries, remove_embargo_countries),
    ]

