# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('shoppingcart', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coupon',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2015, 9, 23, 16, 15, 27, 103205, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='courseregistrationcode',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2015, 9, 23, 16, 15, 27, 101492, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='registrationcoderedemption',
            name='redeemed_at',
            field=models.DateTimeField(default=datetime.datetime(2015, 9, 23, 16, 15, 27, 102427, tzinfo=utc), null=True),
        ),
    ]
