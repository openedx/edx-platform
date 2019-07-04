# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('oef', '0004_auto_20171211_0510'),
    ]

    operations = [
        migrations.AddField(
            model_name='topicquestion',
            name='order_number',
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
    ]
