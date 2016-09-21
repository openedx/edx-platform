# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shoppingcart', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='courseregcodeitem',
            name='mode',
            field=models.SlugField(default=b'honor'),
        ),
        migrations.AlterField(
            model_name='paidcourseregistration',
            name='mode',
            field=models.SlugField(default=b'honor'),
        ),
    ]
