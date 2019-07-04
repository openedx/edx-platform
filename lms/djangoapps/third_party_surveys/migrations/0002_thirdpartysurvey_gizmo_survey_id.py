# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('third_party_surveys', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='thirdpartysurvey',
            name='gizmo_survey_id',
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
    ]
