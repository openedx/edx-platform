# -*- coding: utf-8 -*-


import datetime

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('entitlements', '0006_courseentitlementsupportdetail_action'),
    ]

    operations = [
        migrations.AlterField(
            model_name='courseentitlementpolicy',
            name='expiration_period',
            field=models.DurationField(default=datetime.timedelta(730), help_text=u'Duration in days from when an entitlement is created until when it is expired.'),
        ),
    ]
