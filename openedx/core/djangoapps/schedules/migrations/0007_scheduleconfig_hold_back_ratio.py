# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schedules', '0006_scheduleexperience'),
    ]

    operations = [
        migrations.AddField(
            model_name='scheduleconfig',
            name='hold_back_ratio',
            field=models.FloatField(default=0),
        ),
    ]
