# Converted from the original South migration 0003_add_countries.py

from django.db import migrations, models
from django_countries import countries


def create_embargo_countries(apps, schema_editor):
    """Populate the available countries with all 2-character ISO country codes. """
    country_model = apps.get_model("embargo", "Country")
    for country_code, __ in list(countries):
        country_model.objects.get_or_create(country=country_code)

def remove_embargo_countries(apps, schema_editor):
    """Clear all available countries. """
    country_model = apps.get_model("embargo", "Country")
    country_model.objects.all().delete()

class Migration(migrations.Migration):

    dependencies = [
        ('embargo', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_embargo_countries, remove_embargo_countries),
    ]

