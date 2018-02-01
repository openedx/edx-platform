# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('oef', '0005_topicquestion_order_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organizationoefscore',
            name='finish_date',
            field=models.DateField(null=True, blank=True),
        ),
    ]
