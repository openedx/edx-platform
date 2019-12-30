# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commerce', '0004_auto_20160531_0950'),
    ]

    operations = [
        migrations.AddField(
            model_name='commerceconfiguration',
            name='enable_automatic_refund_approval',
            field=models.BooleanField(default=True, help_text='Automatically approve valid refund requests, without manual processing'),
        ),
    ]
