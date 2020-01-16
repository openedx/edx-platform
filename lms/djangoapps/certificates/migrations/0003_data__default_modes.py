# -*- coding: utf-8 -*-


from django.conf import settings
from django.core.files import File
from django.db import migrations, models

# Converted from the original South migration 0002_default_rate_limit_config.py


def forwards(apps, schema_editor):
    """Add default modes"""
    BadgeImageConfiguration = apps.get_model("certificates", "BadgeImageConfiguration")
    db_alias = schema_editor.connection.alias
    # This will need to be changed if badges/certificates get moved out of the default db for some reason.
    if db_alias != 'default':
        return
    objects = BadgeImageConfiguration.objects.using(db_alias)
    if not objects.exists():
        for mode in ['honor', 'verified', 'professional']:
            conf = objects.create(mode=mode)
            file_name = '{0}{1}'.format(mode, '.png')
            conf.icon.save(
                'badges/{}'.format(file_name),
                File(open(settings.PROJECT_ROOT / 'static' / 'images' / 'default-badges' / file_name, 'rb'))
            )

            conf.save()

def backwards(apps, schema_editor):
    """Do nothing, assumptions too dangerous."""
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('certificates', '0002_data__certificatehtmlviewconfiguration_data'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards)
    ]
