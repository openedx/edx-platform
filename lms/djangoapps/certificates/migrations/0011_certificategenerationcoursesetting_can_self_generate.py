# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import apps
from django.db import migrations, models
from django.db.models import F

def copy_field():
    MyModel = apps.get_model('certificates', 'certificategenerationcoursesetting')
    MyModel.objects.all().update(can_self_generate=F('enabled'))

class Migration(migrations.Migration):

    dependencies = [
        ('certificates', '0010_certificate_language_course_setting'),
    ]

    operations = [
        migrations.AddField(
            model_name='certificategenerationcoursesetting',
            name='can_self_generate',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(copy_field)
    ]
