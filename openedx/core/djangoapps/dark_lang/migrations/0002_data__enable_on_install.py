# Converted from the original South migration 0002_enable_on_install.py
#
from django.db import migrations, models


def create_dark_lang_config(apps, schema_editor):
    """
    Enable DarkLang by default when it is installed, to prevent accidental
    release of testing languages.
    """
    DarkLangConfig = apps.get_model("dark_lang", "DarkLangConfig")

    objects = DarkLangConfig.objects
    if not objects.exists():
        objects.create(enabled=True)

def remove_dark_lang_config(apps, schema_editor):
    """Write your backwards methods here."""
    raise RuntimeError("Cannot reverse this migration.")

class Migration(migrations.Migration):

    dependencies = [
        ('dark_lang', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_dark_lang_config, remove_dark_lang_config),
    ]
