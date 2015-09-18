# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('shoppingcart', '0002_auto_20150923_1215'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coupon',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2015, 10, 2, 14, 4, 16, 520488, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='courseregistrationcode',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2015, 10, 2, 14, 4, 16, 518625, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='registrationcoderedemption',
            name='redeemed_at',
            field=models.DateTimeField(default=datetime.datetime(2015, 10, 2, 14, 4, 16, 519560, tzinfo=utc), null=True),
        ),
    ]
