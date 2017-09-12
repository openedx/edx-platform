# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import apps
from django.db import migrations, models
from django.db.models import F

def copy_field(apps, schema_editor):
    CertificateGenerationCourseSetting = apps.get_model('certificates', 'CertificateGenerationCourseSetting')
    CertificateGenerationCourseSetting.objects.all().update(self_generation_enabled=F('enabled'))

class Migration(migrations.Migration):

    dependencies = [
        ('certificates', '0009_auto_20170911_2120'),
    ]

    operations = [
        migrations.RunPython(copy_field),
        migrations.RemoveField(
            model_name='certificategenerationcoursesetting',
            name='enabled',
        ),
    ]
